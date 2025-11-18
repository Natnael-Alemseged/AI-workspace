"""Agent configuration for Agno-based agents"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Agent configuration
AGENT_CONFIG = {
    "model": "llama3-groq-70b-8192-tool-use-preview",  # Groq model with tool calling
    "add_datetime": True,
    "timezone": "Africa/Nairobi",  # Default timezone
    "add_location": True,
}

# Gmail tool actions
gmail_tools_actions = [
    "GMAIL_SEND_EMAIL",
    "GMAIL_FETCH_EMAILS",
    "GMAIL_CREATE_EMAIL_DRAFT",
    "GMAIL_REPLY_TO_EMAIL",
    "GMAIL_SEARCH_EMAILS",
]

# Calendar tool actions (for future use)
calendar_tools_actions = [
    "GOOGLECALENDAR_CREATE_EVENT",
    "GOOGLECALENDAR_FIND_EVENT",
    "GOOGLECALENDAR_LIST_EVENTS",
]

# Weather tool actions (for future use)
weather_tools_actions = [
    "WEATHERMAP_GET_CURRENT_WEATHER",
]

# Web search tool actions (for future use)
websearch_tools_actions = [
    "SERPAPI_SEARCH",
]

# Google Drive tool actions (for future use)
googledrive_tools_actions = [
    "GOOGLEDRIVE_CREATE_FILE",
    "GOOGLEDRIVE_FIND_FILE",
    "GOOGLEDRIVE_LIST_FILES",
]


def get_system_timezone() -> str:
    """Get the system timezone."""
    try:
        if os.name == 'posix':  # Unix-like systems (Linux, macOS)
            try:
                return os.readlink('/etc/localtime').split('zoneinfo/')[1]
            except Exception:
                return "UTC"
        elif os.name == 'nt':  # Windows
            return os.popen('tzutil /g').read().strip()
        else:
            return "UTC"
    except Exception:
        return "UTC"


def get_home_directory() -> str:
    """Get the home directory of the current user."""
    return os.path.expanduser("~")