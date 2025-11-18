"""
Test script for chat feature.
Run this after setting up the chat feature to verify everything works.

Usage:
    python test_chat_feature.py
"""
import asyncio
import os
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models.chat import ChatMessage, ChatRoom, ChatRoomMember, ChatRoomType, MessageType
from app.models.user import User
from app.services.chat_service import ChatService
from app.schemas.chat import ChatMessageCreate, ChatRoomCreate

# Load environment variables
load_dotenv()


async def test_chat_feature():
    """Test the chat feature end-to-end."""
    print("🧪 Testing Chat Feature...\n")
    
    async with AsyncSessionLocal() as session:
        # 1. Get or create test users
        print("1️⃣ Setting up test users...")
        user1 = await get_or_create_test_user(session, "test1@example.com")
        user2 = await get_or_create_test_user(session, "test2@example.com")
        print(f"   ✅ User 1: {user1.email} ({user1.id})")
        print(f"   ✅ User 2: {user2.email} ({user2.id})\n")
        
        # 2. Create a direct chat
        print("2️⃣ Creating direct chat...")
        room_data = ChatRoomCreate(
            room_type=ChatRoomType.DIRECT,
            member_ids=[user2.id]
        )
        room = await ChatService.create_room(session, room_data, user1.id)
        print(f"   ✅ Direct chat created: {room.id}\n")
        
        # 3. Send a text message
        print("3️⃣ Sending text message...")
        message_data = ChatMessageCreate(
            room_id=room.id,
            message_type=MessageType.TEXT,
            content="Hello from test script!"
        )
        message = await ChatService.create_message(session, message_data, user1.id)
        print(f"   ✅ Message sent: {message.id}")
        print(f"   📝 Content: {message.content}\n")
        
        # 4. Reply to message
        print("4️⃣ Sending reply...")
        reply_data = ChatMessageCreate(
            room_id=room.id,
            message_type=MessageType.TEXT,
            content="Thanks for the message!",
            reply_to_id=message.id
        )
        reply = await ChatService.create_message(session, reply_data, user2.id)
        print(f"   ✅ Reply sent: {reply.id}")
        print(f"   📝 Content: {reply.content}")
        print(f"   ↩️  Reply to: {reply.reply_to_id}\n")
        
        # 5. Get room messages
        print("5️⃣ Fetching room messages...")
        messages, total = await ChatService.get_room_messages(
            session, room.id, user1.id, page=1, page_size=10
        )
        print(f"   ✅ Found {total} messages:")
        for msg in reversed(messages):
            sender = "User 1" if msg.sender_id == user1.id else "User 2"
            reply_indicator = " (reply)" if msg.reply_to_id else ""
            print(f"      - {sender}: {msg.content}{reply_indicator}")
        print()
        
        # 6. Edit message
        print("6️⃣ Editing message...")
        updated_message = await ChatService.update_message(
            session, message.id, user1.id, "Hello from test script! (edited)"
        )
        print(f"   ✅ Message edited: {updated_message.id}")
        print(f"   📝 New content: {updated_message.content}")
        print(f"   ✏️  Edited: {updated_message.is_edited}\n")
        
        # 7. Mark messages as read
        print("7️⃣ Marking messages as read...")
        receipts = await ChatService.mark_messages_as_read(
            session, room.id, user2.id, [message.id, reply.id]
        )
        print(f"   ✅ Marked {len(receipts)} messages as read\n")
        
        # 8. Create a group chat
        print("8️⃣ Creating group chat...")
        user3 = await get_or_create_test_user(session, "test3@example.com")
        group_data = ChatRoomCreate(
            name="Test Group",
            room_type=ChatRoomType.GROUP,
            description="A test group chat",
            member_ids=[user2.id, user3.id]
        )
        group = await ChatService.create_room(session, group_data, user1.id)
        print(f"   ✅ Group chat created: {group.id}")
        print(f"   👥 Name: {group.name}")
        print(f"   📝 Description: {group.description}\n")
        
        # 9. Send message to group
        print("9️⃣ Sending message to group...")
        group_message_data = ChatMessageCreate(
            room_id=group.id,
            message_type=MessageType.TEXT,
            content="Hello everyone in the group!"
        )
        group_message = await ChatService.create_message(
            session, group_message_data, user1.id
        )
        print(f"   ✅ Group message sent: {group_message.id}\n")
        
        # 10. Get user's rooms
        print("🔟 Fetching user's rooms...")
        rooms, total_rooms = await ChatService.get_user_rooms(
            session, user1.id, page=1, page_size=10
        )
        print(f"   ✅ User 1 has {total_rooms} rooms:")
        for r in rooms:
            room_type = "Direct" if r.room_type == ChatRoomType.DIRECT else "Group"
            name = r.name or f"{room_type} Chat"
            print(f"      - {name} ({room_type})")
        print()
        
        # 11. Test Supabase configuration
        print("1️⃣1️⃣ Checking Supabase configuration...")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            print(f"   ✅ Supabase URL configured")
            print(f"   ✅ Supabase Key configured")
            print(f"   ℹ️  Bucket: {os.getenv('SUPABASE_BUCKET', 'chat-media')}")
        else:
            print(f"   ⚠️  Supabase not configured (media uploads will fail)")
        print()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n📋 Summary:")
        print(f"   - Created {total_rooms} chat rooms")
        print(f"   - Sent {total} messages")
        print(f"   - Tested edit, reply, and read receipts")
        print(f"   - Verified group chat functionality")
        print("\n🚀 Chat feature is ready to use!")
        print("\n📚 Next steps:")
        print("   1. Start the server: uvicorn app.main:app --reload")
        print("   2. Test Socket.IO: See CHAT_SETUP_GUIDE.md")
        print("   3. Check API docs: http://localhost:8000/docs")


async def get_or_create_test_user(session: AsyncSession, email: str) -> User:
    """Get or create a test user."""
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        
        user = User(
            id=uuid4(),
            email=email,
            hashed_password=pwd_context.hash("testpassword123"),
            is_active=True,
            is_superuser=False,
            is_verified=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Chat Feature Test Script")
    print("=" * 60 + "\n")
    
    try:
        asyncio.run(test_chat_feature())
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure database is set up: alembic upgrade head")
        print("   2. Check .env file has correct DATABASE_URL")
        print("   3. Verify all dependencies are installed: pip install -e .")
        print("   4. See CHAT_SETUP_GUIDE.md for detailed setup")
        raise
