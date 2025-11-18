# Emoji Reactions System

## Overview
Your application **already has a fully functional emoji reaction system** for messages! Users can add and remove emoji reactions to any topic message.

## API Endpoints

### 1. Add Reaction
**POST** `/channels/topics/messages/{message_id}/reactions`

**Request Body:**
```json
{
  "emoji": "👍"
}
```

**Response:** `201 Created`
```json
{
  "message": "Reaction added successfully"
}
```

**Features:**
- Prevents duplicate reactions (same user + same emoji on same message)
- Real-time notification via Socket.IO (`reaction_added` event)
- Supports any emoji (unicode or shortcode, max 50 characters)

---

### 2. Remove Reaction
**DELETE** `/channels/topics/messages/{message_id}/reactions/{emoji}`

**Response:** `204 No Content`

**Features:**
- Only the user who added the reaction can remove it
- Real-time notification via Socket.IO (`reaction_removed` event)

---

## Database Schema

### MessageReaction Model
```python
class MessageReaction(Base):
    id: UUID
    message_id: UUID  # Foreign key to topic_messages
    user_id: UUID     # Foreign key to users
    emoji: str        # Emoji unicode or shortcode (max 50 chars)
    created_at: datetime
```

**Relationships:**
- `message`: Links to TopicMessage
- `user`: Links to User who reacted

---

## How Messages Include Reactions

### TopicMessageRead Schema
When you fetch messages, they **automatically include full reaction details**:
- `reaction_count`: Total number of reactions on the message
- `reactions`: List of `ReactionSummary` objects (grouped by emoji)
- Reactions are eagerly loaded via `selectinload(TopicMessage.reactions)`

### Example Message Response
```json
{
  "id": "uuid",
  "topic_id": "uuid",
  "sender_id": "uuid",
  "content": "Great idea!",
  "sender_email": "user@example.com",
  "sender_full_name": "John Doe",
  "reaction_count": 7,
  "reactions": [
    {
      "emoji": "👍",
      "count": 5,
      "users": ["uuid1", "uuid2", "uuid3", "uuid4", "uuid5"]
    },
    {
      "emoji": "❤️",
      "count": 2,
      "users": ["uuid6", "uuid7"]
    }
  ],
  "created_at": "2025-11-14T13:00:00Z",
  ...
}
```

### ReactionSummary Schema
Reactions are grouped by emoji with:
- `emoji`: The emoji string
- `count`: Number of users who reacted with this emoji
- `users`: List of user UUIDs who reacted
- `user_reacted`: Whether current user reacted (optional field)

---

## Real-Time Updates (Socket.IO)

### Events Emitted

#### reaction_added
```json
{
  "topic_id": "uuid",
  "message_id": "uuid",
  "user_id": "uuid",
  "emoji": "👍"
}
```

#### reaction_removed
```json
{
  "topic_id": "uuid",
  "message_id": "uuid",
  "user_id": "uuid",
  "emoji": "👍"
}
```

---

## Frontend Integration Example

### Add Reaction
```javascript
const addReaction = async (messageId, emoji) => {
  const response = await fetch(
    `/channels/topics/messages/${messageId}/reactions`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ emoji })
    }
  );
  return response.json();
};

// Usage
await addReaction('message-uuid', '👍');
await addReaction('message-uuid', '❤️');
await addReaction('message-uuid', '😂');
```

### Remove Reaction
```javascript
const removeReaction = async (messageId, emoji) => {
  await fetch(
    `/channels/topics/messages/${messageId}/reactions/${encodeURIComponent(emoji)}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
};

// Usage
await removeReaction('message-uuid', '👍');
```

### Listen for Real-Time Updates
```javascript
socket.on('reaction_added', (data) => {
  console.log(`${data.emoji} added to message ${data.message_id}`);
  // Update UI to show new reaction
});

socket.on('reaction_removed', (data) => {
  console.log(`${data.emoji} removed from message ${data.message_id}`);
  // Update UI to remove reaction
});
```

---

## Service Layer

The reaction logic is handled by `TopicReactionService`:

### Key Methods
- `add_reaction(session, message_id, user_id, emoji)` - Adds a reaction (idempotent)
- `remove_reaction(session, message_id, user_id, emoji)` - Removes a reaction

### Features
- Automatic duplicate prevention
- Transaction management with rollback on error
- Comprehensive logging
- Error handling

---

## Testing the API

### Using cURL

**Add Reaction:**
```bash
curl -X POST "http://localhost:8000/channels/topics/messages/{message_id}/reactions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"emoji": "👍"}'
```

**Remove Reaction:**
```bash
curl -X DELETE "http://localhost:8000/channels/topics/messages/{message_id}/reactions/👍" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Supported Emoji Types

The system supports:
1. **Unicode Emojis**: 👍, ❤️, 😂, 🎉, 🔥, etc.
2. **Emoji Shortcodes**: :thumbsup:, :heart:, :joy:, etc.
3. **Custom Emojis**: Any string up to 50 characters

---

## Summary

✅ **Emoji reactions are fully implemented and working!**

- Add/remove reactions via REST API
- Real-time updates via Socket.IO
- Duplicate prevention
- Reaction counts on messages
- User tracking (who reacted with what)
- Full authentication and authorization

The system is production-ready and just needs frontend integration to display and interact with reactions.
