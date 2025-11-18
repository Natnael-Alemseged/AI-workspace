"""Tests for AI agent parser utility."""
import pytest
from app.utils.ai_agent_parser import parse_agent_mention, extract_agent_and_prompt, AgentType


def test_parse_email_agent_mention():
    """Test parsing @emailAi mention."""
    message = "@emailAi send an email to natiaabaydam@gmail.com saying hi"
    result = parse_agent_mention(message)
    
    assert result is not None
    assert result.agent_type == AgentType.EMAIL_AI
    assert result.prompt == "send an email to natiaabaydam@gmail.com saying hi"
    assert result.original_message == message


def test_parse_search_agent_mention():
    """Test parsing @searchAi mention."""
    message = "@searchAi find information about Python programming"
    result = parse_agent_mention(message)
    
    assert result is not None
    assert result.agent_type == AgentType.SEARCH_AI
    assert result.prompt == "find information about Python programming"
    assert result.original_message == message


def test_parse_email_agent_case_insensitive():
    """Test that agent mention is case-insensitive."""
    message = "@EmailAi send a test email"
    result = parse_agent_mention(message)
    
    assert result is not None
    assert result.agent_type == AgentType.EMAIL_AI
    assert result.prompt == "send a test email"


def test_parse_no_agent_mention():
    """Test message without agent mention."""
    message = "This is a regular message without any agent"
    result = parse_agent_mention(message)
    
    assert result is None


def test_parse_agent_mention_with_extra_spaces():
    """Test parsing with extra spaces."""
    message = "@emailAi    send an email with extra spaces"
    result = parse_agent_mention(message)
    
    assert result is not None
    assert result.agent_type == AgentType.EMAIL_AI
    assert result.prompt == "send an email with extra spaces"


def test_extract_agent_and_prompt_with_agent():
    """Test extract_agent_and_prompt with agent mention."""
    message = "@searchAi search for AI news"
    agent_type, prompt = extract_agent_and_prompt(message)
    
    assert agent_type == "searchAi"
    assert prompt == "search for AI news"


def test_extract_agent_and_prompt_without_agent():
    """Test extract_agent_and_prompt without agent mention."""
    message = "Just a regular message"
    agent_type, prompt = extract_agent_and_prompt(message)
    
    assert agent_type is None
    assert prompt == message


def test_parse_agent_mention_not_at_start():
    """Test that agent mention must be at the start of message."""
    message = "Hello @emailAi send an email"
    result = parse_agent_mention(message)
    
    assert result is None


def test_parse_multiline_prompt():
    """Test parsing agent mention with multiline prompt."""
    message = "@emailAi send an email to test@example.com with subject 'Test' and body 'Hello World'"
    result = parse_agent_mention(message)
    
    assert result is not None
    assert result.agent_type == AgentType.EMAIL_AI
    assert "send an email to test@example.com" in result.prompt
