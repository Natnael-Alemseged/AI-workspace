"""Google OAuth service for handling authentication flow."""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv

from app.models.user import User, OAuthAccount
from app.core.logging import logger

# Load environment variables
load_dotenv(override=True)

# OAuth configuration
oauth = OAuth()

# Register Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',
    }
)


class GoogleOAuthService:
    """Service for handling Google OAuth operations."""
    
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        google_user_info: Dict[str, Any],
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> User:
        """
        Get existing user or create new user from Google OAuth data.
        
        Args:
            session: Database session
            google_user_info: User info from Google OAuth
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_at: Token expiration time
            
        Returns:
            User object
        """
        email = google_user_info.get('email', '').lower()
        google_id = google_user_info.get('sub')
        full_name = google_user_info.get('name')
        
        if not email or not google_id:
            logger.error("Missing required Google user info")
            raise HTTPException(status_code=400, detail="Invalid Google user data")
        
        # Check if user exists by email
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"Existing user found: {user.id}")
            # Update or create OAuth account
            await GoogleOAuthService._update_oauth_account(
                session, user, google_id, email, access_token, refresh_token, expires_at
            )
        else:
            # Create new user
            logger.info(f"Creating new user for email: {email}")
            user = await GoogleOAuthService._create_user_with_oauth(
                session, email, full_name, google_id, access_token, refresh_token, expires_at
            )
        
        return user
    
    @staticmethod
    async def _create_user_with_oauth(
        session: AsyncSession,
        email: str,
        full_name: Optional[str],
        google_id: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: Optional[datetime]
    ) -> User:
        """Create a new user with OAuth account."""
        # Create user without password (OAuth user)
        new_user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            hashed_password="",  # OAuth users don't have passwords
            is_active=True,
            is_superuser=False,
            is_verified=True  # Google-verified email
        )
        
        session.add(new_user)
        await session.flush()  # Get user ID
        
        # Create OAuth account
        oauth_account = OAuthAccount(
            id=uuid.uuid4(),
            user_id=new_user.id,
            oauth_name="google",
            access_token=access_token,
            refresh_token=refresh_token or "",
            expires_at=expires_at,
            account_id=google_id,
            account_email=email
        )
        
        session.add(oauth_account)
        await session.commit()
        await session.refresh(new_user)
        
        logger.info(f"Created new user with OAuth: {new_user.id}")
        return new_user
    
    @staticmethod
    async def _update_oauth_account(
        session: AsyncSession,
        user: User,
        google_id: str,
        email: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: Optional[datetime]
    ):
        """Update or create OAuth account for existing user."""
        # Check if OAuth account exists
        result = await session.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user.id,
                OAuthAccount.oauth_name == "google"
            )
        )
        oauth_account = result.scalar_one_or_none()
        
        if oauth_account:
            # Update existing OAuth account
            oauth_account.access_token = access_token
            if refresh_token:
                oauth_account.refresh_token = refresh_token
            oauth_account.expires_at = expires_at
            oauth_account.account_id = google_id
            oauth_account.account_email = email
            oauth_account.updated_at = datetime.utcnow()
            logger.info(f"Updated OAuth account for user: {user.id}")
        else:
            # Create new OAuth account
            oauth_account = OAuthAccount(
                id=uuid.uuid4(),
                user_id=user.id,
                oauth_name="google",
                access_token=access_token,
                refresh_token=refresh_token or "",
                expires_at=expires_at,
                account_id=google_id,
                account_email=email
            )
            session.add(oauth_account)
            logger.info(f"Created OAuth account for user: {user.id}")
        
        await session.commit()
    
    @staticmethod
    async def get_oauth_account(
        session: AsyncSession,
        user_id: uuid.UUID
    ) -> Optional[OAuthAccount]:
        """Get Google OAuth account for a user."""
        result = await session.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user_id,
                OAuthAccount.oauth_name == "google"
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    def is_token_expired(oauth_account: OAuthAccount) -> bool:
        """Check if OAuth token is expired."""
        if not oauth_account.expires_at:
            return False
        return datetime.utcnow() >= oauth_account.expires_at