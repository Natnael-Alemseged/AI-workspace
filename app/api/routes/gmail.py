"""Gmail integration API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_active_user as current_active_user
from app.db import get_async_session
from app.models.user import User
from app.services.integrations.composio_service import composio_service

router = APIRouter(prefix="/gmail", tags=["gmail"])


# Request/Response Models
class GmailConnectionRequest(BaseModel):
    """Request to connect Gmail account."""
    redirect_url: Optional[str] = None  # Ignored in managed auth; include if switching to custom


class GmailConnectionResponse(BaseModel):
    """Response with Gmail connection details."""
    connection_url: str
    entity_id: str
    status: str


class EmailRecipient(BaseModel):
    """Email recipient model."""
    email: EmailStr
    name: Optional[str] = None


class SendEmailRequest(BaseModel):
    """Request to send an email via Composio."""
    recipient_email: EmailStr
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []
    extra_recipients: Optional[List[EmailStr]] = []


class EmailDraftRequest(BaseModel):
    """Request to create an email draft."""
    to: List[EmailRecipient]
    subject: str
    body: str
    cc: Optional[List[EmailRecipient]] = None
    bcc: Optional[List[EmailRecipient]] = None


class ReadEmailsRequest(BaseModel):
    """Request to read emails."""
    max_results: int = 10
    query: Optional[str] = None  # Gmail search query (e.g., "is:unread")


@router.post("/connect", response_model=GmailConnectionResponse)
async def connect_gmail(
        request: GmailConnectionRequest,
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        entity_id = str(user.id)
        logger.info(f"Initiating Gmail connection for user {entity_id}")

        result = composio_service.connect_gmail_account(user_id=entity_id)

        return GmailConnectionResponse(
            connection_url=result["connection_url"],
            entity_id=result["entity_id"],
            status=result["status"]
        )

    except Exception as e:
        logger.error(f"Error connecting Gmail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Gmail connection: {str(e)}"
        )


# Optional: Keep if you want to repurpose for custom auth or status polling; otherwise, remove
@router.get("/callback")
async def gmail_callback(
        code: str,
        state: Optional[str] = None,
        user: User = Depends(current_active_user)
):
    """
    Handle OAuth callback from Gmail (not used in managed auth).
    """
    try:
        logger.info(f"Gmail OAuth callback received for user {user.id}")

        return {
            "status": "success",
            "message": "Gmail connected successfully",
            "user_id": str(user.id)
        }

    except Exception as e:
        logger.error(f"Error in Gmail callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Gmail connection: {str(e)}"
        )


@router.get("/status")
async def get_gmail_status(
        user: User = Depends(current_active_user)
):
    try:
        entity_id = str(user.id)
        result = composio_service.get_gmail_status(user_id=entity_id)
        return result

    except Exception as e:
        logger.error(f"Error checking Gmail status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Gmail status: {str(e)}"
        )


@router.post("/read")
def composio_fetch_emails(
        request: ReadEmailsRequest,
        user: User = Depends(current_active_user)
):
    """
    Fetch emails for a given user id and limit.
    """
    try:
        entity_id = str(user.id)
        result = composio_service.read_emails(
            user_id=entity_id,
            limit=request.max_results,
            query=request.query
        )
        return result

    except Exception as e:
        logger.error(f"Error reading emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read emails: {str(e)}",
        )


@router.post("/send")
async def send_email(
        request: SendEmailRequest,
        user: User = Depends(current_active_user)
):
    try:
        entity_id = str(user.id)
        logger.info(f"Sending email for user {entity_id}")

        result = composio_service.send_email(
            user_id=entity_id,
            recipient_email=request.recipient_email,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            extra_recipients=request.extra_recipients
        )

        return result

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/draft")
async def create_draft(
        request: EmailDraftRequest,
        user: User = Depends(current_active_user)
):
    """
    Create an email draft in Gmail.
    """
    try:
        entity_id = str(user.id)
        logger.info(f"Creating email draft for user {entity_id}")

        to_emails = [r.email for r in request.to]
        cc_emails = [r.email for r in request.cc] if request.cc else []
        bcc_emails = [r.email for r in request.bcc] if request.bcc else []

        # Note: This method needs to be added to composio_service if draft creation is needed
        # For now, keeping the original implementation
        from composio import Composio
        from app.core.config import COMPOSIO_API_KEY
        
        composio_client = Composio(apikey=COMPOSIO_API_KEY)
        result = composio_client.tools.execute(
            user_id=entity_id,
            slug="GMAIL_CREATE_EMAIL_DRAFT",
            arguments={
                "to": to_emails,
                "subject": request.subject,
                "body": request.body,
                "cc": cc_emails,
                "bcc": bcc_emails
            }
        )

        return {
            "status": "success",
            "message": "Draft created successfully",
            "draft_id": result.get("id"),
            "result": result
        }

    except Exception as e:
        logger.error(f"Error creating draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft: {str(e)}"
        )


@router.get("/tools")
async def get_gmail_tools(user: User = Depends(current_active_user)):
    """
    Get available Gmail tools for the current user.
    """
    try:
        entity_id = str(user.id)
        tools = composio_service.get_gmail_tools(user_id=entity_id)

        return {
            "status": "success",
            "tools": tools,
            "count": len(tools)
        }

    except Exception as e:
        logger.error(f"Error getting Gmail tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Gmail tools: {str(e)}"
        )
