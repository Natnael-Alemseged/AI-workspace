"""AI Bot user constants and utilities."""
from uuid import UUID

# AI Bot User IDs (fixed UUIDs)
EMAIL_AI_BOT_ID = UUID("00000000-0000-0000-0000-000000000001")
SEARCH_AI_BOT_ID = UUID("00000000-0000-0000-0000-000000000002")
GENERAL_AI_BOT_ID = UUID("00000000-0000-0000-0000-000000000003")

# Map agent types to bot IDs
AGENT_TYPE_TO_BOT_ID = {
    "emailAi": EMAIL_AI_BOT_ID,
    "searchAi": SEARCH_AI_BOT_ID,
    "general": GENERAL_AI_BOT_ID,
}

# Bot display names
BOT_NAMES = {
    EMAIL_AI_BOT_ID: "Email AI",
    SEARCH_AI_BOT_ID: "Search AI",
    GENERAL_AI_BOT_ID: "General AI",
}

# Bot avatars
BOT_AVATARS = {
    EMAIL_AI_BOT_ID: "📧",
    SEARCH_AI_BOT_ID: "🔍",
    GENERAL_AI_BOT_ID: "🤖",
}


def get_bot_id_for_agent_type(agent_type: str) -> UUID:
    """Get the bot user ID for a given agent type."""
    return AGENT_TYPE_TO_BOT_ID.get(agent_type, GENERAL_AI_BOT_ID)


def get_bot_name(bot_id: UUID) -> str:
    """Get the display name for a bot."""
    return BOT_NAMES.get(bot_id, "AI Assistant")


def get_bot_avatar(bot_id: UUID) -> str:
    """Get the avatar emoji for a bot."""
    return BOT_AVATARS.get(bot_id, "🤖")
