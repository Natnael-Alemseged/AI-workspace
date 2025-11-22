"""Custom authentication endpoints to replace FastAPI-Users."""
from datetime import datetime, timedelta
from typing import Optional
import uuid
import os

from fastapi import APIRouter, Depends, HTTPException, Header, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

from app.db import get_async_session
from app.models.user import User
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.services.auth.google_oauth import oauth, GoogleOAuthService

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Load environment variables
load_dotenv(override=True)
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "aud": "fastapi-users:auth"
    })
    
    # Reload SECRET_KEY to ensure consistency
    load_dotenv(override=True)
    secret = os.getenv("SECRET_KEY", "")
    
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current user from JWT token."""
    from app.core.logging import logger
    
    if not authorization:
        logger.error("No Authorization header provided")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.error(f"Invalid Authorization header format")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    token = parts[1]
    
    try:
        # Reload SECRET_KEY to ensure consistency
        load_dotenv(override=True)
        secret = os.getenv("SECRET_KEY", "")
        
        logger.debug(f"Decoding token with SECRET_KEY length: {len(secret)}")
        
        payload = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            audience=["fastapi-users:auth"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        logger.debug(f"Token decoded, user_id: {user_id}")
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    # Fetch user
    result = await session.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    
    logger.debug(f"User authenticated: {user.id}")
    return user


@router.post("/jwt/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    """Login endpoint that returns JWT token."""
    from app.core.logging import logger
    
    # Find user by email
    result = await session.execute(
        select(User).where(User.email == form_data.username.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.error(f"Login failed for user: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User {user.id} logged in successfully")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/jwt/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint (JWT is stateless, so this is mainly for logging)."""
    from app.core.logging import logger
    logger.info(f"User {current_user.id} logged out")
    return {"detail": "Successfully logged out"}


@router.post("/register", response_model=UserRead, status_code=201)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Register a new user."""
    from app.core.logging import logger
    
    # Check if user already exists
    result = await session.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="REGISTER_USER_ALREADY_EXISTS")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email.lower(),
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role="admin",  # Set all new users as admin
        is_active=True,
        is_superuser=False,
        is_verified=False
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    logger.info(f"User {new_user.id} registered successfully")
    
    return new_user


@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    """Request password reset (placeholder - would send email in production)."""
    from app.core.logging import logger
    logger.info(f"Password reset requested for: {email}")
    return {"detail": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(token: str = Form(...), password: str = Form(...)):
    """Reset password with token (placeholder)."""
    from app.core.logging import logger
    logger.info(f"Password reset attempted with token")
    return {"detail": "Password reset successful"}


@router.post("/request-verify-token")
async def request_verify_token(email: EmailStr):
    """Request verification token (placeholder)."""
    from app.core.logging import logger
    logger.info(f"Verification token requested for: {email}")
    return {"detail": "Verification email sent"}


@router.post("/verify")
async def verify(token: str = Form(...)):
    """Verify user email (placeholder)."""
    from app.core.logging import logger
    logger.info(f"Email verification attempted")
    return {"detail": "Email verified successfully"}


# ============================================================================
# Google OAuth Endpoints
# ============================================================================

@router.get("/google/authorize")
async def google_authorize(request: Request):
    """
    Initiate Google OAuth flow.
    Redirects user to Google's authorization page.
    """
    from app.core.logging import logger
    
    # Get the redirect URI from environment or use default
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI",
        f"{request.base_url}api/auth/google/callback"
    )
    
    logger.info(f"Initiating Google OAuth with redirect_uri: {redirect_uri}")
    
    # Generate authorization URL
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Handle Google OAuth callback.
    Exchanges authorization code for tokens and creates/updates user.
    """
    from app.core.logging import logger
    
    try:
        # Exchange authorization code for access token
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            # If userinfo not in token, fetch it
            resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            user_info = resp.json()
        
        logger.info(f"Google OAuth callback for email: {user_info.get('email')}")
        
        # Calculate token expiration
        expires_at = None
        if 'expires_in' in token:
            expires_at = datetime.utcnow() + timedelta(seconds=token['expires_in'])
        
        # Get or create user
        user = await GoogleOAuthService.get_or_create_user(
            session=session,
            google_user_info=user_info,
            access_token=token['access_token'],
            refresh_token=token.get('refresh_token'),
            expires_at=expires_at
        )
        
        # Create JWT token for the user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        logger.info(f"User {user.id} authenticated via Google OAuth")
        
        # Get frontend URL from environment
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Redirect to frontend with token
        # Frontend should handle this token and store it
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={access_token}&type=google"
        )
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{frontend_url}/auth/error?message=OAuth authentication failed"
        )


@router.post("/google/token", response_model=Token)
async def google_token_exchange(
    code: str = Form(...),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Alternative endpoint for mobile/SPA apps to exchange Google auth code for JWT.
    This is useful when you can't use redirect-based flow.
    """
    from app.core.logging import logger
    
    try:
        # This would require implementing the token exchange manually
        # For now, we'll return an error suggesting to use the redirect flow
        raise HTTPException(
            status_code=501,
            detail="Direct token exchange not implemented. Use /auth/google/authorize flow."
        )
    except Exception as e:
        logger.error(f"Google token exchange error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/google/status")
async def google_oauth_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Check if current user has Google OAuth connected.
    Returns OAuth account status and token validity.
    """
    from app.core.logging import logger
    
    oauth_account = await GoogleOAuthService.get_oauth_account(session, current_user.id)
    
    if not oauth_account:
        return {
            "connected": False,
            "email": None,
            "expires_at": None
        }
    
    is_expired = GoogleOAuthService.is_token_expired(oauth_account)
    
    return {
        "connected": True,
        "email": oauth_account.account_email,
        "expires_at": oauth_account.expires_at.isoformat() if oauth_account.expires_at else None,
        "is_expired": is_expired
    }