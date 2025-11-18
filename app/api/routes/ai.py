

#ai.py
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_active_user as current_active_user
from app.core.ai_bots import get_bot_avatar, get_bot_id_for_agent_type, get_bot_name
from app.db import get_async_session
from app.models.chat import MessageType
from app.models.message import MessageRole
from app.models.user import User
from app.schemas.chat import ChatMessageCreate
from app.schemas.conversation import ChatRequest, ChatResponse
from app.services.chat import agent_service, ConversationService
from app.services.chat.chat_service import ChatService
from app.services.socketio_service import emit_to_room


router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class EmailToAI(BaseModel):
    """Schema for sending email to AI bot."""
    room_id: UUID
    content: str


@router.post("", response_model=ChatResponse)
async def ai_handler(
    chat_request: ChatRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    AI chat endpoint that stores conversations and messages in the database.
    Supports multiple chat sessions via conversation_id.
    """
    user_id = user.id
    prompt = chat_request.message
    conversation_id = chat_request.conversation_id

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'message' in request"
        )

    try:
        # Get or create conversation
        conversation = await ConversationService.get_or_create_conversation(
            db, user_id, conversation_id
        )
        
        logger.info(f"Processing AI request for user {user_id} in conversation {conversation.id}")

        # Store user message
        from app.schemas.conversation import MessageCreate
        user_message = await ConversationService.create_message(
            db,
            MessageCreate(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=prompt,
            ),
            user_id,
        )

        if not user_message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store user message"
            )

        # Run the AI agent with specified type
        agent_type = chat_request.agent_type if chat_request.agent_type != "general" else None
        output = await agent_service.run_agent_stream(prompt, str(user_id), agent_type)

        # Store assistant response
        assistant_message = await ConversationService.create_message(
            db,
            MessageCreate(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=output,
            ),
            user_id,
        )

        if not assistant_message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store assistant message"
            )

        # Generate title if this is a new conversation with first message
        if not conversation.title:
            await ConversationService.generate_conversation_title(
                db, conversation.id, user_id
            )

        logger.info(f"Successfully processed AI request for conversation {conversation.id}")

        return ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            role=assistant_message.role,
            content=assistant_message.content,
            content_type=assistant_message.content_type,
            tool_calls_executed=[],
            created_at=assistant_message.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI handler error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing failed: {str(e)}"
        )


@router.post("/email", status_code=status.HTTP_202_ACCEPTED)
async def send_email_to_ai(
    email_data: EmailToAI,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Send email to AI bot - returns immediately, AI replies via socket.
    The AI response will be sent as a reply to the user's message.
    """
    try:
        # Create user's message first
        user_message = await ChatService.create_message(
            session,
            ChatMessageCreate(
                room_id=email_data.room_id,
                message_type=MessageType.TEXT,
                content=email_data.content
            ),
            sender_id=current_user.id
        )
        
        # Emit user's message immediately
        await emit_to_room(
            str(email_data.room_id),
            "new_message",
            {
                "message": {
                    "id": str(user_message.id),
                    "room_id": str(user_message.room_id),
                    "sender_id": str(user_message.sender_id),
                    "content": user_message.content,
                    "message_type": user_message.message_type.value,
                    "created_at": user_message.created_at.isoformat(),
                    "reply_to_id": None,
                    "is_edited": False,
                    "is_deleted": False
                },
                "sender": {
                    "id": str(current_user.id),
                    "email": current_user.email,
                    "full_name": current_user.full_name
                }
            }
        )
        
        # Queue AI processing with the message ID to reply to
        background_tasks.add_task(
            process_ai_email_response,
            reply_to_message_id=user_message.id,
            room_id=email_data.room_id,
            user_id=current_user.id,
            content=email_data.content,
            user_name=current_user.full_name or current_user.email
        )
        
        logger.info(f"Email queued for AI processing: message {user_message.id}")
        
        return {
            "status": "processing",
            "message_id": str(user_message.id),
            "message": "Email sent to AI, response will arrive shortly"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending email to AI: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email to AI"
        )


async def process_ai_email_response(
    reply_to_message_id: UUID,
    room_id: UUID,
    user_id: UUID,
    content: str,
    user_name: str
):
    """
    Process AI response in background and send as a reply to the original message.
    
    Args:
        reply_to_message_id: The message ID to reply to
        room_id: Chat room ID
        user_id: User ID who sent the email
        content: Email content
        user_name: User's display name
    """
    from app.db import async_session_maker
    
    try:
        # Show "AI is typing" indicator
        await emit_to_room(
            str(room_id),
            "typing",
            {
                "room_id": str(room_id),
                "user_type": "ai",
                "is_typing": True
            }
        )
        
        logger.info(f"Processing AI email for message {reply_to_message_id}")
        
        # Process with AI (can take time)
        ai_response = await agent_service.run_agent_stream(
            prompt=content,
            user_id=str(user_id),
            agent_type="emailAi"
        )
        
        # Create new session for background task
        async with async_session_maker() as session:
            # Create AI response as a REPLY to the user's message
            ai_message = await ChatService.create_ai_message(
                session,
                ChatMessageCreate(
                    room_id=room_id,
                    message_type=MessageType.TEXT,
                    content=ai_response,
                    reply_to_id=reply_to_message_id  # Link to original message
                ),
                agent_type="emailAi"
            )
            
            # Get bot info
            bot_id = get_bot_id_for_agent_type("emailAi")
            bot_name = get_bot_name(bot_id)
            bot_avatar = get_bot_avatar(bot_id)
            
            # Stop typing indicator
            await emit_to_room(
                str(room_id),
                "typing",
                {
                    "room_id": str(room_id),
                    "user_type": "ai",
                    "is_typing": False
                }
            )
            
            # Emit AI response with reply context
            await emit_to_room(
                str(room_id),
                "new_message",
                {
                    "message": {
                        "id": str(ai_message.id),
                        "room_id": str(ai_message.room_id),
                        "sender_id": str(bot_id),
                        "content": ai_message.content,
                        "message_type": ai_message.message_type.value,
                        "created_at": ai_message.created_at.isoformat(),
                        "reply_to_id": str(reply_to_message_id),
                        "reply_to": {
                            "id": str(reply_to_message_id),
                            "content": content[:100] + "..." if len(content) > 100 else content,
                            "sender_name": user_name
                        },
                        "is_edited": False,
                        "is_deleted": False
                    },
                    "sender": {
                        "type": "ai",
                        "name": bot_name,
                        "avatar": bot_avatar,
                        "email": "emailai@armada.bot"
                    }
                }
            )
            
            logger.info(f"AI replied to message {reply_to_message_id}")
            
    except Exception as e:
        logger.error(f"Error processing AI email: {e}", exc_info=True)
        
        # Emit error to user
        try:
            await emit_to_room(
                str(room_id),
                "typing",
                {
                    "room_id": str(room_id),
                    "user_type": "ai",
                    "is_typing": False
                }
            )
            
            await emit_to_room(
                str(room_id),
                "ai_error",
                {
                    "room_id": str(room_id),
                    "error": "AI failed to process your email",
                    "original_message_id": str(reply_to_message_id)
                }
            )
        except Exception as emit_error:
            logger.error(f"Error emitting AI error: {emit_error}")
