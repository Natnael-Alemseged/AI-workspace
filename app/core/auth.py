"""Custom authentication configuration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Authentication constants
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in environment variables")
