"""Token schemas for JWT authentication."""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data extracted from JWT."""
    username: Optional[str] = None