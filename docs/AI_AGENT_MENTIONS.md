# AI Agent Mentions

This document explains how to use AI agent mentions in topic messages to trigger specialized AI agents with specific toolkits.

## Overview

The system supports specialized AI agents that can be invoked by mentioning them at the start of a message. Each agent has access to specific Composio toolkits and is optimized for particular tasks.

## Supported Agents

### 1. Email Agent (`@emailAi`)

**Purpose:** Specialized agent for managing Gmail and email tasks.

**Available Tools:**
- Gmail toolkit (send emails, read emails, search emails, manage drafts, etc.)

**Example Usage:**
```
@emailAi send an email to natiaabaydam@gmail.com saying hi
```

**What happens:**
1. The system detects the `@emailAi` mention
2. Extracts the prompt: "send an email to natiaabaydam@gmail.com saying hi"
3. Routes the request to the Email Agent with Gmail tools only
4. The agent processes the request and sends the email
5. The response is appended to the message in the topic

### 2. Search Agent (`@searchAi`)

**Purpose:** Specialized agent for web search and information retrieval.

**Available Tools:**
- Composio Search toolkit (web search)

**Example Usage:**
```
@searchAi find the latest news about artificial intelligence
```

**What happens:**
1. The system detects the `@searchAi` mention
2. Extracts the prompt: "find the latest news about artificial intelligence"
3. Routes the request to the Search Agent with search tools only
4. The agent searches the web and returns relevant information
5. The response is appended to the message in the topic

## How It Works

### In Topic Messages

When a user sends a message in a topic that starts with an AI agent mention:

1. **Detection:** The `parse_agent_mention()` function detects the agent type
2. **Extraction:** The prompt is extracted (everything after the agent mention)
3. **Processing:** The appropriate agent is invoked with the extracted prompt
4. **Response:** The AI response is appended to the original message

**Message Flow:**
```
User sends: "@emailAi send an email to user@example.com"
           ↓
System detects: agent_type = "emailAi", prompt = "send an email to user@example.com"
           ↓
Agent processes with Gmail tools
           ↓
Message saved: "@emailAi send an email to user@example.com

**AI Response (emailAi):**
I've successfully sent the email to user@example.com."
```

### In Direct AI Conversations

You can also specify the agent type in the AI chat endpoint:

```json
{
  "message": "send an email to user@example.com",
  "agent_type": "emailAi"
}
```

## Implementation Details

### Agent Types

Defined in `app/utils/ai_agent_parser.py`:

```python
class AgentType(str, Enum):
    EMAIL_AI = "emailAi"
    SEARCH_AI = "searchAi"
```

### Agent Service

The `agent_service.py` manages different agent types:

- **Email Agent:** Only has access to Gmail toolkit
- **Search Agent:** Only has access to Composio Search toolkit
- **General Agent:** Has access to all tools (default)

### Parsing Logic

The parser uses regex to detect agent mentions:

```python
pattern = r'@(emailAi|searchAi)\s+(.+)'
```

**Requirements:**
- Agent mention must be at the start of the message
- Must have a space after the agent name
- Everything after the space is treated as the prompt

## Error Handling

If the AI agent fails to process the request:

```
@emailAi send an email

**AI Error:** Failed to process request - [error details]
```

## Adding New Agents

To add a new agent type:

1. **Add to AgentType enum** in `app/utils/ai_agent_parser.py`:
   ```python
   class AgentType(str, Enum):
       EMAIL_AI = "emailAi"
       SEARCH_AI = "searchAi"
       CALENDAR_AI = "calendarAi"  # New agent
   ```

2. **Update the parser pattern** in `parse_agent_mention()`:
   ```python
   pattern = r'@(emailAi|searchAi|calendarAi)\s+(.+)'
   ```

3. **Add toolkit support** in `agent_service.py`:
   ```python
   elif agent_type == AgentType.CALENDAR_AI.value:
       if calendar_tools is None:
           calendar_tools = composio.tools.get(
               user_id=user_id,
               toolkits=["googlecalendar"],
               limit=50
           )
       return calendar_tools
   ```

4. **Add agent configuration** in `run_agent_stream()`:
   ```python
   elif agent_type == AgentType.CALENDAR_AI.value:
       agent_name = "Calendar Assistant"
       agent_description = "A specialized agent for managing calendar events."
       system_prompt = "You are a helpful calendar assistant..."
   ```

## Testing

Run the tests:

```bash
pytest tests/test_ai_agent_parser.py -v
```

## Best Practices

1. **Be Specific:** Provide clear, specific prompts to the agents
2. **Use the Right Agent:** Choose the agent that matches your task
3. **Error Handling:** Always check for error messages in responses
4. **Security:** Agents use user-specific Composio authentication

## Examples

### Email Examples

```
@emailAi send an email to team@company.com with subject "Meeting Tomorrow" and body "Don't forget about our 2pm meeting"

@emailAi search my inbox for emails from john@example.com

@emailAi draft an email to client@company.com about the project update
```

### Search Examples

```
@searchAi what is the current weather in New York?

@searchAi find the latest Python 3.12 features

@searchAi search for best practices in REST API design
```

## Limitations

- Agent mention must be at the start of the message
- Only one agent can be invoked per message
- Agents have access only to their specific toolkits
- User must have appropriate Composio authentication set up
