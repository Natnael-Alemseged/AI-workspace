# Socket vs REST API Message Structure - Consistency Guide

## Issue
Socket.IO events were missing sender information (`sender_email`, `sender_full_name`) that the REST API includes, causing the frontend to not display names for real-time messages.

## Solution
✅ **Fixed!** Socket emissions now include the same fields as REST API responses.

## Message Structure Comparison

### REST API Response
**Endpoint:** `GET /api/channels/topics/{topic_id}/messages`

```json
{
  "messages": [
    {
      "id": "uuid",
      "topic_id": "uuid",
      "sender_id": "uuid",
      "content": "Message content",
      "reply_to_id": null,
      "is_edited": false,
      "edited_at": null,
      "is_deleted": false,
      "deleted_at": null,
      "created_at": "2025-11-15T18:00:00Z",
      
      // ✅ Sender info included
      "sender_email": "user@example.com",
      "sender_full_name": "John Doe",
      
      // ✅ Counts and reactions
      "mention_count": 0,
      "reaction_count": 0,
      "reactions": []
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50,
  "has_more": false
}
```

### Socket.IO Event (NOW FIXED)
**Event:** `new_topic_message`

```json
{
  "topic_id": "uuid",
  "message": {
    "id": "uuid",
    "sender_id": "uuid",
    "content": "Message content",
    "reply_to_id": null,
    "is_edited": false,
    "is_deleted": false,
    "created_at": "2025-11-15T18:00:00Z",
    
    // ✅ NOW INCLUDED - Sender info
    "sender_email": "user@example.com",
    "sender_full_name": "John Doe",
    
    // ✅ NOW INCLUDED - Counts and reactions
    "mention_count": 0,
    "reaction_count": 0,
    "reactions": []
  }
}
```

## AI Bot Messages

### REST API Response
```json
{
  "id": "uuid",
  "sender_id": "00000000-0000-0000-0000-000000000001",
  "content": "AI response...",
  "sender_email": "emailai@armada.bot",
  "sender_full_name": "Email AI",
  ...
}
```

### Socket.IO Event (NOW FIXED)
```json
{
  "topic_id": "uuid",
  "message": {
    "id": "uuid",
    "sender_id": "00000000-0000-0000-0000-000000000001",
    "content": "AI response...",
    "reply_to_id": "original-message-uuid",
    
    // ✅ NOW INCLUDED - Bot sender info
    "sender_email": "emailai@armada.bot",
    "sender_full_name": "Email AI",
    
    "mention_count": 0,
    "reaction_count": 0,
    "reactions": []
  }
}
```

## Frontend Integration

### TypeScript Interface
```typescript
interface TopicMessage {
  id: string;
  topic_id: string;
  sender_id: string;
  content: string;
  reply_to_id: string | null;
  is_edited: boolean;
  edited_at: string | null;
  is_deleted: boolean;
  deleted_at: string | null;
  created_at: string;
  
  // ✅ These fields are now consistent across REST and Socket
  sender_email: string | null;
  sender_full_name: string | null;
  
  mention_count: number;
  reaction_count: number;
  reactions: ReactionSummary[];
}
```

### Display Message Name
```typescript
function MessageComponent({ message }: { message: TopicMessage }) {
  // ✅ This now works for both REST API and Socket messages
  const displayName = message.sender_full_name || message.sender_email || 'Unknown';
  
  return (
    <div className="message">
      <div className="message-header">
        <span className="sender-name">{displayName}</span>
        <span className="timestamp">{formatTime(message.created_at)}</span>
      </div>
      <div className="message-content">{message.content}</div>
    </div>
  );
}
```

### Socket Listener
```typescript
socket.on('new_topic_message', (data: {
  topic_id: string;
  message: TopicMessage;
}) => {
  // ✅ Message structure is identical to REST API
  // No special handling needed!
  addMessageToChat(data.message);
});
```

## Fields Included in Both REST and Socket

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Message ID |
| `topic_id` | UUID | Topic ID |
| `sender_id` | UUID | Sender user ID (or bot ID) |
| `content` | string | Message content |
| `reply_to_id` | UUID \| null | ID of message being replied to |
| `is_edited` | boolean | Whether message was edited |
| `edited_at` | datetime \| null | When message was edited |
| `is_deleted` | boolean | Whether message was deleted |
| `deleted_at` | datetime \| null | When message was deleted |
| `created_at` | datetime | When message was created |
| **`sender_email`** ✅ | string \| null | Sender's email |
| **`sender_full_name`** ✅ | string \| null | Sender's full name |
| **`mention_count`** ✅ | number | Number of mentions |
| **`reaction_count`** ✅ | number | Number of reactions |
| **`reactions`** ✅ | array | Reaction summaries |

## Benefits

✅ **Consistent Data Structure** - Same fields in REST and Socket  
✅ **No Special Handling** - Frontend can use same component for both  
✅ **Names Display Correctly** - sender_full_name is always present  
✅ **Bot Support** - AI bots have proper sender info  
✅ **Future-Proof** - Easy to add new fields consistently  

## Testing

### Test REST API
```bash
GET /api/channels/topics/{topic_id}/messages?page=1&page_size=50

# Verify response includes:
# - sender_email
# - sender_full_name
# - mention_count
# - reaction_count
# - reactions
```

### Test Socket
```typescript
socket.on('new_topic_message', (data) => {
  console.log('Socket message:', data.message);
  
  // ✅ Should include:
  // - sender_email
  // - sender_full_name
  // - mention_count
  // - reaction_count
  // - reactions
});
```

### Test AI Bot Messages
```bash
POST /api/channels/topics/{topic_id}/messages
{
  "content": "@EmailAI send email to test@example.com"
}

# Wait for socket event with AI response
# Verify it includes:
# - sender_email: "emailai@armada.bot"
# - sender_full_name: "Email AI"
```

## Summary

🎉 **Socket and REST API are now consistent!**

- ✅ Both include `sender_email` and `sender_full_name`
- ✅ Both include `mention_count`, `reaction_count`, `reactions`
- ✅ Frontend can use the same interface/component for both
- ✅ Names display correctly in real-time messages
- ✅ AI bot messages have proper sender info

No frontend changes needed - just verify that names now display correctly! 🚀
