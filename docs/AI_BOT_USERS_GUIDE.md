# AI Bot Users - Implementation Guide

## Overview
AI bots are now implemented as **real user accounts** with fixed UUIDs. This allows them to be treated like regular users in topics and chat rooms, with proper sender IDs and relationships.

## Bot Users

### Created Bot Accounts

| Bot Name | Email | UUID | Avatar | Purpose |
|----------|-------|------|--------|---------|
| Email AI | emailai@armada.bot | `00000000-0000-0000-0000-000000000001` | 📧 | Email management |
| Search AI | searchai@armada.bot | `00000000-0000-0000-0000-000000000002` | 🔍 | Web search |
| General AI | generalai@armada.bot | `00000000-0000-0000-0000-000000000003` | 🤖 | General assistance |

### Bot Characteristics
- ✅ Real user accounts in the database
- ✅ Fixed UUIDs (never change)
- ✅ No passwords (cannot login)
- ✅ Can be members of topics/rooms
- ✅ Messages have proper `sender_id`
- ✅ Work with existing Pydantic schemas

## Setup

### 1. Seed Bot Users
```bash
python seed_ai_bots.py
```

This creates the three bot users if they don't already exist.

### 2. Bot Constants
Located in `app/core/ai_bots.py`:

```python
from app.core.ai_bots import (
    EMAIL_AI_BOT_ID,
    SEARCH_AI_BOT_ID,
    GENERAL_AI_BOT_ID,
    get_bot_id_for_agent_type,
    get_bot_name,
    get_bot_avatar
)
```

## Usage

### In Services

#### Topic Messages
```python
from app.core.ai_bots import get_bot_id_for_agent_type

# Create AI message with bot as sender
bot_id = get_bot_id_for_agent_type("emailAi")
message = TopicMessage(
    topic_id=topic_id,
    sender_id=bot_id,  # Bot user ID
    content=ai_response,
    reply_to_id=original_message_id
)
```

#### Chat Messages
```python
from app.core.ai_bots import get_bot_id_for_agent_type

# Create AI message
ai_message = await ChatService.create_ai_message(
    session,
    ChatMessageCreate(
        room_id=room_id,
        content=ai_response,
        reply_to_id=original_message_id
    ),
    agent_type="emailAi"  # Maps to EMAIL_AI_BOT_ID
)
```

### Agent Type Mapping

```python
AGENT_TYPE_TO_BOT_ID = {
    "emailAi": EMAIL_AI_BOT_ID,
    "searchAi": SEARCH_AI_BOT_ID,
    "general": GENERAL_AI_BOT_ID,
}
```

## Frontend Integration

### Message Structure
AI messages now have proper sender IDs:

```typescript
{
  id: "uuid",
  sender_id: "00000000-0000-0000-0000-000000000001",  // Bot UUID
  content: "AI response...",
  reply_to_id: "original-message-uuid",
  created_at: "2025-11-15T18:00:00Z",
  // ... other fields
}
```

### Identifying Bot Messages
```typescript
const BOT_IDS = [
  "00000000-0000-0000-0000-000000000001", // Email AI
  "00000000-0000-0000-0000-000000000002", // Search AI
  "00000000-0000-0000-0000-000000000003", // General AI
];

function isBotMessage(message: Message): boolean {
  return BOT_IDS.includes(message.sender_id);
}

function getBotInfo(senderId: string) {
  const botMap = {
    "00000000-0000-0000-0000-000000000001": {
      name: "Email AI",
      avatar: "📧",
      email: "emailai@armada.bot"
    },
    "00000000-0000-0000-0000-000000000002": {
      name: "Search AI",
      avatar: "🔍",
      email: "searchai@armada.bot"
    },
    "00000000-0000-0000-0000-000000000003": {
      name: "General AI",
      avatar: "🤖",
      email: "generalai@armada.bot"
    }
  };
  return botMap[senderId];
}
```

### Display Bot Messages
```tsx
function MessageComponent({ message }: { message: Message }) {
  const isBot = isBotMessage(message);
  const botInfo = isBot ? getBotInfo(message.sender_id) : null;
  
  return (
    <div className={`message ${isBot ? 'bot-message' : 'user-message'}`}>
      {message.reply_to && (
        <ReplyPreview replyTo={message.reply_to} />
      )}
      
      <div className="message-header">
        <span className="avatar">
          {isBot ? botInfo.avatar : '👤'}
        </span>
        <span className="name">
          {isBot ? botInfo.name : message.sender_name}
        </span>
      </div>
      
      <div className="content">{message.content}</div>
    </div>
  );
}
```

## Auto-Membership

### Topics
All AI bots are **automatically added as members** when a topic is created:
- ✅ Email AI
- ✅ Search AI  
- ✅ General AI

This happens in `TopicManagementService.create_topic()`.

### Chat Rooms
AI bots are automatically added to **group chats only** (not direct chats):
- ✅ Email AI
- ✅ Search AI
- ✅ General AI

This happens in `ChatService.create_room()` when `room_type == GROUP`.

### Why Auto-Add?
1. **Always Available** - Users can @mention bots anytime
2. **No Setup Required** - Bots work out of the box
3. **Consistent Experience** - Every topic/room has AI assistance
4. **Proper Permissions** - Bots are real members, not special cases

## Benefits

### ✅ Proper Data Model
- Bots are real users with UUIDs
- No special handling for NULL sender_ids
- Works with existing foreign key constraints
- Compatible with Pydantic validation

### ✅ Simplified Logic
- No need for nullable sender_id checks
- Can query bot messages like any other user
- Bot membership in topics/rooms works naturally

### ✅ Better UX
- Bots appear as members in topic/room lists
- Can @mention bots (they're real users)
- Bot messages show proper sender info
- Consistent with user message structure

### ✅ Scalability
- Easy to add new bot types
- Bots can have profiles, avatars, etc.
- Can implement bot-specific permissions
- Bot analytics and tracking

## Database Schema

### No Changes Required
The existing schema works perfectly:
- `topic_messages.sender_id` → References bot user
- `chat_messages.sender_id` → References bot user
- `topic_members` → Bots can be members
- `chat_room_members` → Bots can be members

## Adding New Bots

1. **Add to seed script** (`seed_ai_bots.py`):
```python
{
    "id": "00000000-0000-0000-0000-000000000004",
    "email": "codeai@armada.bot",
    "full_name": "Code AI",
    "role": "user",
    ...
}
```

2. **Add to constants** (`app/core/ai_bots.py`):
```python
CODE_AI_BOT_ID = UUID("00000000-0000-0000-0000-000000000004")

AGENT_TYPE_TO_BOT_ID = {
    ...
    "codeAi": CODE_AI_BOT_ID,
}
```

3. **Run seed script**:
```bash
python seed_ai_bots.py
```

## Migration Notes

### Previous Implementation
- ❌ `sender_id = None` for AI messages
- ❌ Required nullable sender_id column
- ❌ Pydantic validation errors
- ❌ Special handling everywhere

### Current Implementation
- ✅ `sender_id = BOT_UUID` for AI messages
- ✅ sender_id is a real user reference
- ✅ No validation errors
- ✅ Bots treated like users

## Testing

```bash
# 1. Seed bots
python seed_ai_bots.py

# 2. Send message with AI mention
POST /api/channels/topics/{topic_id}/messages
{
  "content": "@EmailAI send email to test@example.com"
}

# 3. Verify bot response has proper sender_id
# Response should include:
{
  "sender_id": "00000000-0000-0000-0000-000000000001",
  "sender_email": "emailai@armada.bot",
  "sender_full_name": "Email AI"
}
```

## Summary

AI bots are now **first-class citizens** in the system:
- Real user accounts with fixed UUIDs
- Can be members of topics and chat rooms
- Messages have proper sender relationships
- No special handling required
- Clean, scalable architecture

🎉 This approach is much cleaner than using NULL sender_ids!
