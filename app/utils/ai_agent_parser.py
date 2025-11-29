"""Utility for parsing AI agent mentions in messages."""
import re
from enum import Enum
from typing import Optional, Tuple


class AgentType(str, Enum):
    """Supported AI agent types."""
    EMAIL_AI = "emailAi"
    SEARCH_AI = "searchAi"
    GENERAL_AI = "general"


class AgentMention:
    """Represents a detected AI agent mention in a message."""
    
    def __init__(self, agent_type: AgentType, prompt: str, original_message: str):
        self.agent_type = agent_type
        self.prompt = prompt
        self.original_message = original_message
    
    def __repr__(self):
        return f"AgentMention(agent_type={self.agent_type}, prompt='{self.prompt[:50]}...')"


def parse_agent_mention(message: str) -> Optional[AgentMention]:
    """
    Parse a message to detect AI agent mentions.
    
    Supports patterns like:
    - "@emailAi send an email to user@example.com"
    - "@searchAi find information about Python"
    - "@Email AI send an email to user@example.com" (with spaces)
    - "@Search AI find information about Python" (with spaces)
    
    Args:
        message: The message content to parse
        
    Returns:
        AgentMention object if an agent mention is detected, None otherwise
    """
    # Pattern to match @agentName followed by text (supports spaces in agent name)
    # Matches: @emailAi, @Email AI, @searchAi, @Search AI, etc.
    pattern = r'@([\w\s]+?)\s+(.+)'
    match = re.match(pattern, message.strip(), re.IGNORECASE)
    
    if not match:
        return None
    
    agent_name = match.group(1).strip().lower().replace(' ', '')
    prompt = match.group(2).strip()
    
    # Map agent name to AgentType (normalize by removing spaces and lowercasing)
    agent_type_map = {
        'emailai': AgentType.EMAIL_AI,
        'searchai': AgentType.SEARCH_AI,
        'generalai': AgentType.GENERAL_AI,
    }
    
    agent_type = agent_type_map.get(agent_name)
    
    if not agent_type:
        return None
    
    return AgentMention(
        agent_type=agent_type,
        prompt=prompt,
        original_message=message
    )


def extract_agent_and_prompt(message: str) -> Tuple[Optional[str], str]:
    """
    Extract agent type and prompt from a message.
    
    Args:
        message: The message content
        
    Returns:
        Tuple of (agent_type, prompt) where agent_type is None if no agent mention found
    """
    agent_mention = parse_agent_mention(message)
    
    if agent_mention:
        return agent_mention.agent_type.value, agent_mention.prompt
    
    return None, message
