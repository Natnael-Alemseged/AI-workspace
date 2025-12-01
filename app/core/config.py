import logging
import sys
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from app.core.logging import InterceptHandler
from loguru import logger
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")


def _clean_db_url(database_url: str) -> str:
    database_url = database_url.strip().strip("\"")
    return database_url


def _build_async_database_url(database_url: str) -> str:
    database_url = _clean_db_url(database_url)
    if database_url.startswith("postgresql+psycopg2://"):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql://", 1)
    if database_url.startswith("sqlite+aiosqlite"):
        return database_url
    if database_url.startswith("sqlite"):
        return database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if database_url.startswith("postgresql+asyncpg"):
        return database_url
    if database_url.startswith("postgresql://"):
        parsed = urlparse(database_url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        sslmode_values = query_params.pop("sslmode", None)
        query_params.pop("channel_binding", None)
        if sslmode_values:
            sslmode = sslmode_values[0]
            if sslmode in {"require", "verify-full"}:
                query_params["ssl"] = ["require"]
            elif sslmode in {"disable", "allow"}:
                query_params["ssl"] = ["prefer"]
            elif sslmode == "prefer":
                query_params["ssl"] = ["prefer"]
        new_query = urlencode({k: v[0] for k, v in query_params.items()}, doseq=False)
        parsed = parsed._replace(scheme="postgresql+asyncpg", query=new_query)
        return urlunparse(parsed)
    return database_url


API_PREFIX = "/api"
VERSION = "0.1.0"
DEBUG: bool = config("DEBUG", cast=bool, default=False)
MAX_CONNECTIONS_COUNT: int = config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
MIN_CONNECTIONS_COUNT: int = config("MIN_CONNECTIONS_COUNT", cast=int, default=10)
SECRET_KEY: Secret = config("SECRET_KEY", cast=Secret, default="")
# JWT Authentication
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=60)
DATABASE_URL_RAW: str = config("DATABASE_URL", default="sqlite:///./app.db")
DATABASE_URL: str = _clean_db_url(DATABASE_URL_RAW)
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)


ASYNC_DATABASE_URL: str = _build_async_database_url(DATABASE_URL)

PROJECT_NAME: str = config("PROJECT_NAME", default="Armada Den")

# OAuth configuration
GOOGLE_CLIENT_ID: str = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET: str = config("GOOGLE_CLIENT_SECRET", default="")
GITHUB_CLIENT_ID: str = config("GITHUB_CLIENT_ID", default="")
GITHUB_CLIENT_SECRET: str = config("GITHUB_CLIENT_SECRET", default="")

# CORS configuration for OAuth
ALLOWED_ORIGINS: list[str] = config(
    "ALLOWED_ORIGINS",
    cast=lambda v: [x.strip() for x in v.split(",") if x.strip()],
    default="http://localhost:3000,http://localhost:8080,https://armada-den-frontend.vercel.app"
)

# OpenAI Configuration
OPENAI_API_KEY: str = config("OPENAI_API_KEY", default="")
GEMINI_API_KEY: str = config("GEMINI_API_KEY", default="")
GROQ_API_KEY: str = config("GROQ_API_KEY", default="")
GROQ_MODEL: str = config("GROQ_MODEL", default="")

GROK_API_KEY: str = config("GROK_API_KEY", default="")

SUPERMEMORY_API_KEY: str = config("SUPERMEMORY_API_KEY", default="")
OPENAI_MODEL: str = config("OPENAI_MODEL", default="gpt-3.5-turbo")

# Composio Configuration
COMPOSIO_API_KEY: str = config("COMPOSIO_API_KEY", default="")
COMPOSIO_AUTH_CONFIG_ID: str = config("COMPOSIO_AUTH_CONFIG_ID", default="")

# Web Search Configuration
BING_API_KEY: str = config("BING_API_KEY", default="")
SERPAPI_API_KEY: str = config("SERPAPI_API_KEY", default="")

# Vector Database Configuration
VECTOR_DB_TYPE: str = config("VECTOR_DB_TYPE", default="supermemory")
PINECONE_API_KEY: str = config("PINECONE_API_KEY", default="")
PINECONE_ENVIRONMENT: str = config("PINECONE_ENVIRONMENT", default="")
PINECONE_INDEX_NAME: str = config("PINECONE_INDEX_NAME", default="armada-den-memory")

# Supabase Configuration
SUPABASE_URL: str = config("SUPABASE_URL", default="")
SUPABASE_KEY: str = config("SUPABASE_KEY", default="")
SUPABASE_BUCKET: str = config("SUPABASE_BUCKET", default="chat-media")

# Supabase S3 Configuration
SUPABASE_S3_ACCESS_KEY_ID: str = config("SUPABASE_S3_ACCESS_KEY_ID", default="")
SUPABASE_S3_SECRET_ACCESS_KEY: str = config("SUPABASE_S3_SECRET_ACCESS_KEY", default="")
SUPABASE_S3_ENDPOINT_URL: str = config("SUPABASE_S3_ENDPOINT_URL", default="")
SUPABASE_S3_REGION_NAME: str = config("SUPABASE_S3_REGION_NAME", default="")
SUPABASE_PROJECT_REF: str = config("SUPABASE_PROJECT_REF", default="wijpuothbstqrbdalpta")


REDIS_URL: str = config("REDIS_URL", default="")

# logging configuration
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    handlers=[InterceptHandler(level=LOGGING_LEVEL)], level=LOGGING_LEVEL
)
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])

