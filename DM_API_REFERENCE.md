# Direct Messaging API Reference

Quick reference for all Direct Messaging endpoints.

## Base URL
```
/api/direct-messages
```

All endpoints require authentication via Bearer token.

---

## Endpoints

### 1. Send Message
**POST** `/`

Send a new direct message to another user.

**Request Body:**
```json
{
  "receiver_id": "uuid",
  "content": "Message text",
  "reply_to_id": "uuid (optional)",
  "attachments": [
    {
      "url": "https://storage.url/file.pdf",
      "filename": "document.pdf",
      "size": 102400,
      "mime_type": "application/pdf"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "sender_id": "uuid",
  "receiver_id": "uuid",
  "content": "Message text",
  "is_read": false,
  "created_at": "2025-12-04T19:00:00Z",
  "attachments": [...],
  "reactions": []
}
```

**Errors:**
- `400`: Invalid receiver ID or receiver is a bot
- `404`: Receiver not found

---

### 2. Get Conversations
**GET** `/conversations`

Get all conversations for the current user with unread counts.

**Response:** `200 OK`
```json
{
  "conversations": [
    {
      "user": {
        "id": "uuid",
        "email": "user@example.com",
        "full_name": "John Doe",
        "is_online": true,
        "last_seen_at": "2025-12-04T19:00:00Z"
      },
      "last_message": {
        "id": "uuid",
        "content": "Last message text",
        "created_at": "2025-12-04T19:00:00Z",
        "is_read": false
      },
      "unread_count": 3,
      "last_message_at": "2025-12-04T19:00:00Z"
    }
  ],
  "total": 10
}
```

---

### 3. Get Messages with User
**GET** `/with/{user_id}`

Get paginated messages between current user and another user.

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 50, max: 100): Messages per page

**Response:** `200 OK`
```json
{
  "messages": [
    {
      "id": "uuid",
      "sender_id": "uuid",
      "receiver_id": "uuid",
      "content": "Message text",
      "reply_to_id": null,
      "is_read": true,
      "read_at": "2025-12-04T19:05:00Z",
      "is_edited": false,
      "edited_at": null,
      "is_deleted": false,
      "deleted_at": null,
      "created_at": "2025-12-04T19:00:00Z",
      "attachments": [],
      "reactions": [
        {
          "emoji": "👍",
          "count": 2,
          "users": ["uuid1", "uuid2"],
          "user_reacted": true
        }
      ],
      "sender_email": "sender@example.com",
      "sender_full_name": "Jane Smith",
      "receiver_email": "receiver@example.com",
      "receiver_full_name": "John Doe"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "has_more": true
}
```

**Note:** Fetching messages automatically marks them as read.

**Errors:**
- `400`: Invalid user ID format

---

### 4. Get Eligible Users
**GET** `/users`

Get all non-bot users that can be messaged.

**Query Parameters:**
- `search` (optional): Search term for filtering by name or email

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_online": true,
    "last_seen_at": "2025-12-04T19:00:00Z"
  }
]
```

---

### 5. Edit Message
**PATCH** `/{message_id}`

Edit a message (sender only).

**Request Body:**
```json
{
  "content": "Updated message text"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "content": "Updated message text",
  "is_edited": true,
  "edited_at": "2025-12-04T19:10:00Z",
  ...
}
```

**Errors:**
- `400`: Invalid message ID format
- `404`: Message not found or unauthorized

---

### 6. Delete Message
**DELETE** `/{message_id}`

Delete a message (sender only, soft delete).

**Response:** `204 No Content`

**Errors:**
- `400`: Invalid message ID format
- `404`: Message not found or unauthorized

---

### 7. Mark Message as Read
**POST** `/{message_id}/read`

Mark a specific message as read (receiver only).

**Response:** `204 No Content`

**Errors:**
- `400`: Invalid message ID format
- `404`: Message not found or already read

---

### 8. Add Reaction
**POST** `/{message_id}/reactions`

Add an emoji reaction to a message.

**Request Body:**
```json
{
  "emoji": "👍"
}
```

**Response:** `201 Created`
```json
[
  {
    "emoji": "👍",
    "count": 2,
    "users": ["uuid1", "uuid2"],
    "user_reacted": true
  },
  {
    "emoji": "❤️",
    "count": 1,
    "users": ["uuid3"],
    "user_reacted": false
  }
]
```

**Note:** Returns updated reaction summary for the message.

**Errors:**
- `400`: Invalid message ID format

---

### 9. Remove Reaction
**DELETE** `/{message_id}/reactions/{emoji}`

Remove an emoji reaction from a message.

**Response:** `200 OK`
```json
[
  {
    "emoji": "❤️",
    "count": 1,
    "users": ["uuid3"],
    "user_reacted": false
  }
]
```

**Note:** Returns updated reaction summary for the message.

**Errors:**
- `400`: Invalid message ID format
- `404`: Reaction not found

---

## Authentication

All endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

---

## Error Responses

Standard error format:
```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Rate Limiting

Consider implementing rate limiting for:
- Message sending: 60 messages per minute
- Reaction operations: 120 per minute
- Read operations: No limit

---

## WebSocket Events (Future)

For real-time updates, consider implementing:

```javascript
// Join DM room
socket.emit('dm:join', { user_id: 'other_user_uuid' });

// Listen for new messages
socket.on('dm:new_message', (message) => {
  // Handle new message
});

// Listen for read receipts
socket.on('dm:message_read', (data) => {
  // Update UI
});

// Listen for reactions
socket.on('dm:reaction_added', (data) => {
  // Update message reactions
});

// Send typing indicator
socket.emit('dm:typing', { user_id: 'other_user_uuid', is_typing: true });
```

---

## Examples

### JavaScript/Fetch

```javascript
// Send message
const response = await fetch('/api/direct-messages/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    receiver_id: 'user-uuid',
    content: 'Hello!'
  })
});
const message = await response.json();

// Get conversations
const conversations = await fetch('/api/direct-messages/conversations', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Get messages with user
const messages = await fetch('/api/direct-messages/with/user-uuid?page=1', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Add reaction
const reactions = await fetch(`/api/direct-messages/${messageId}/reactions`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ emoji: '👍' })
}).then(r => r.json());
```

### Python/Requests

```python
import requests

headers = {'Authorization': f'Bearer {token}'}

# Send message
response = requests.post(
    'http://localhost:8000/api/direct-messages/',
    headers=headers,
    json={
        'receiver_id': 'user-uuid',
        'content': 'Hello!'
    }
)
message = response.json()

# Get conversations
conversations = requests.get(
    'http://localhost:8000/api/direct-messages/conversations',
    headers=headers
).json()

# Get messages
messages = requests.get(
    'http://localhost:8000/api/direct-messages/with/user-uuid',
    headers=headers,
    params={'page': 1, 'page_size': 50}
).json()
```

---

## Push Notifications

When a user receives a new DM, they get a push notification with:

**Notification Data:**
```json
{
  "title": "New message from Jane Smith",
  "body": "Message preview text...",
  "data": {
    "type": "direct_message",
    "sender_id": "uuid",
    "message_id": "uuid",
    "sender_name": "Jane Smith"
  }
}
```

Users must have an active FCM subscription (see `/api/notifications/subscribe`).
