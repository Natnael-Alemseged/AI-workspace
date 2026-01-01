# Direct Messaging (DM) System Implementation

## Overview

This document describes the complete implementation of the Direct Messaging system for Armada Den. The DM system enables one-to-one private conversations between users, with support for text messages, file attachments, reactions, read/unread tracking, and push notifications.

## Architecture

### Database Models

#### 1. User Model Enhancement
**File**: `app/models/user.py`

Added `is_bot` field to distinguish between human users and bot users:
```python
is_bot = Column(Boolean, default=False, nullable=False)
```

DMs only work between users where `is_bot = False`.

#### 2. DirectMessage Model
**File**: `app/models/direct_message.py`

Core message model with the following features:
- **Sender/Receiver**: Links to User model
- **Content**: Text message content
- **Reply Support**: Optional `reply_to_id` for threaded conversations
- **Read Tracking**: `is_read`, `read_at` fields
- **Edit Tracking**: `is_edited`, `edited_at` fields
- **Soft Delete**: `is_deleted`, `deleted_at` fields
- **Timestamps**: `created_at` for message ordering

#### 3. DirectMessageReaction Model
**File**: `app/models/direct_message.py`

Emoji reactions on messages:
- Links to message and user
- Stores emoji (unicode or shortcode)
- Timestamp for reaction

#### 4. DirectMessageAttachment Model
**File**: `app/models/direct_message.py`

File attachments for messages:
- Supabase storage URL
- Original filename
- File size and MIME type
- Timestamp

### Service Layer

**File**: `app/services/direct_message_service.py`

The `DirectMessageService` class provides all business logic:

#### Key Methods

1. **`send_message()`**
   - Validates receiver exists and is not a bot
   - Creates message with optional attachments
   - Sends push notification to receiver
   - Returns created message

2. **`get_messages()`**
   - Fetches paginated messages between two users
   - Automatically marks messages as read
   - Includes sender/receiver info, attachments, and reactions
   - Returns messages in reverse chronological order

3. **`get_conversations()`**
   - Lists all users the current user has chatted with
   - Includes last message, unread count, and timestamp
   - Sorted by most recent activity

4. **`get_eligible_users()`**
   - Returns all non-bot, active users (excluding current user)
   - Optional search by name or email
   - Used for "Add Chat" functionality

5. **`mark_message_as_read()`**
   - Marks specific message as read
   - Updates `is_read` and `read_at` fields

6. **`update_message()`**
   - Allows sender to edit their message
   - Updates `is_edited` and `edited_at` fields

7. **`delete_message()`**
   - Soft deletes message (sender only)
   - Updates `is_deleted` and `deleted_at` fields

8. **`add_reaction()` / `remove_reaction()`**
   - Add or remove emoji reactions
   - Prevents duplicate reactions

9. **`get_reaction_summary()`**
   - Groups reactions by emoji
   - Shows count and list of users who reacted
   - Indicates if current user reacted

### API Routes

**File**: `app/api/routes/direct_message_routes.py`

All routes are prefixed with `/direct-messages` and require authentication.

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Send a new direct message |
| GET | `/conversations` | Get all conversations with unread counts |
| GET | `/with/{user_id}` | Get messages with a specific user (paginated) |
| GET | `/users` | Get all eligible users for messaging |
| PATCH | `/{message_id}` | Edit a message |
| DELETE | `/{message_id}` | Delete a message |
| POST | `/{message_id}/read` | Mark message as read |
| POST | `/{message_id}/reactions` | Add a reaction |
| DELETE | `/{message_id}/reactions/{emoji}` | Remove a reaction |

### Pydantic Schemas

**File**: `app/schemas/direct_message.py`

#### Request Schemas
- `DirectMessageCreate`: Send new message
- `DirectMessageUpdate`: Edit message
- `ReactionCreate`: Add reaction
- `AttachmentData`: File attachment info

#### Response Schemas
- `DirectMessageRead`: Single message with full details
- `MessageListResponse`: Paginated message list
- `ConversationRead`: Conversation with user info and unread count
- `ConversationListResponse`: List of all conversations
- `UserBasicInfo`: User info for conversation list
- `ReactionSummary`: Grouped reaction data
- `AttachmentRead`: File attachment details

### Push Notifications

**Integration**: `app/services/direct_message_service.py` → `_send_new_message_notification()`

When a message is sent:
1. Retrieves receiver's FCM push subscriptions
2. Sends notification with:
   - Title: "New message from {sender_name}"
   - Body: Message preview (first 100 chars)
   - Data: `type`, `sender_id`, `message_id`, `sender_name`

Uses existing `notification_service` and `fcm_service` infrastructure.

## Database Migration

**File**: `alembic/versions/3356464281d5_add_direct_messaging_system.py`

### Changes

1. **Add `is_bot` column to `users` table**
   - Type: Boolean
   - Default: false
   - Not nullable

2. **Create `direct_messages` table**
   - Primary key: `id` (UUID)
   - Foreign keys: `sender_id`, `receiver_id`, `reply_to_id`
   - Indexes on: `sender_id`, `receiver_id`, `reply_to_id`, `is_read`, `created_at`

3. **Create `direct_message_reactions` table**
   - Primary key: `id` (UUID)
   - Foreign keys: `message_id`, `user_id`
   - Indexes on: `message_id`, `user_id`

4. **Create `direct_message_attachments` table**
   - Primary key: `id` (UUID)
   - Foreign key: `message_id`
   - Index on: `message_id`

### Running the Migration

```bash
# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Frontend Integration Guide

### 1. Conversation List View

**Endpoint**: `GET /direct-messages/conversations`

**Response**:
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
        "content": "Hey, how are you?",
        "created_at": "2025-12-04T19:00:00Z",
        "is_read": false,
        ...
      },
      "unread_count": 3,
      "last_message_at": "2025-12-04T19:00:00Z"
    }
  ],
  "total": 10
}
```

**UI Display**:
- Show user avatar, name, and online status
- Display last message preview
- Show unread badge with count
- Sort by most recent activity

### 2. Message Thread View

**Endpoint**: `GET /direct-messages/with/{user_id}?page=1&page_size=50`

**Response**:
```json
{
  "messages": [
    {
      "id": "uuid",
      "sender_id": "uuid",
      "receiver_id": "uuid",
      "content": "Hello!",
      "is_read": true,
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
      "sender_full_name": "Jane Smith"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "has_more": true
}
```

**UI Features**:
- Display messages in chronological order (reverse the array)
- Show sender info (name, avatar)
- Display attachments with download links
- Show reactions below messages
- Implement infinite scroll for pagination
- Auto-mark as read when viewing

### 3. Send Message

**Endpoint**: `POST /direct-messages/`

**Request**:
```json
{
  "receiver_id": "uuid",
  "content": "Hello there!",
  "reply_to_id": null,
  "attachments": [
    {
      "url": "https://storage.example.com/file.pdf",
      "filename": "document.pdf",
      "size": 102400,
      "mime_type": "application/pdf"
    }
  ]
}
```

**Response**: Returns created message object

### 4. Add Chat (Browse Users)

**Endpoint**: `GET /direct-messages/users?search=john`

**Response**:
```json
[
  {
    "id": "uuid",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_online": true,
    "last_seen_at": "2025-12-04T19:00:00Z"
  }
]
```

**UI**:
- Show searchable list of all users
- Filter out bots automatically
- Click user to start new conversation

### 5. Reactions

**Add Reaction**: `POST /direct-messages/{message_id}/reactions`
```json
{
  "emoji": "👍"
}
```

**Remove Reaction**: `DELETE /direct-messages/{message_id}/reactions/{emoji}`

**Response**: Returns updated reaction summary

### 6. Edit Message

**Endpoint**: `PATCH /direct-messages/{message_id}`

**Request**:
```json
{
  "content": "Updated message content"
}
```

### 7. Delete Message

**Endpoint**: `DELETE /direct-messages/{message_id}`

**Response**: 204 No Content

## Real-time Updates (WebSocket)

While the current implementation uses REST APIs, you can extend it with WebSocket support for real-time message delivery. Consider:

1. **Socket.IO Events**:
   - `dm:new_message` - New message received
   - `dm:message_read` - Message marked as read
   - `dm:reaction_added` - Reaction added
   - `dm:typing` - User is typing

2. **Room Management**:
   - Join room: `dm:{user1_id}:{user2_id}` (sorted IDs)
   - Emit events to both participants

## Security Considerations

1. **Authorization**:
   - All endpoints require authentication
   - Users can only send messages as themselves
   - Users can only edit/delete their own messages
   - Read receipts only work for receivers

2. **Bot Protection**:
   - Cannot send DMs to users with `is_bot = True`
   - Validated in service layer

3. **Data Privacy**:
   - Soft deletes preserve data integrity
   - Consider implementing hard delete after X days
   - Implement message encryption for sensitive data

## Testing

### Manual Testing Checklist

- [ ] Send message to another user
- [ ] Receive push notification
- [ ] View conversation list with unread counts
- [ ] Open conversation and see messages marked as read
- [ ] Send message with file attachment
- [ ] Reply to a message
- [ ] Add and remove reactions
- [ ] Edit own message
- [ ] Delete own message
- [ ] Search for users
- [ ] Start new conversation
- [ ] Verify bots cannot receive DMs

### API Testing with cURL

```bash
# Get conversations
curl -X GET http://localhost:8000/api/direct-messages/conversations \
  -H "Authorization: Bearer YOUR_TOKEN"

# Send message
curl -X POST http://localhost:8000/api/direct-messages/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_id": "USER_UUID",
    "content": "Hello!"
  }'

# Get messages with user
curl -X GET http://localhost:8000/api/direct-messages/with/USER_UUID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Performance Optimization

### Database Indexes

All critical queries are indexed:
- `direct_messages.sender_id`
- `direct_messages.receiver_id`
- `direct_messages.is_read`
- `direct_messages.created_at`

### Query Optimization

1. **Conversation List**:
   - Uses window function to get latest message per conversation
   - Single query with joins for user info

2. **Message Fetching**:
   - Eager loading with `joinedload` and `selectinload`
   - Prevents N+1 query problems

3. **Pagination**:
   - Offset-based pagination for simplicity
   - Consider cursor-based for large datasets

## Future Enhancements

1. **Message Search**: Full-text search across messages
2. **Message Forwarding**: Forward messages to other users
3. **Voice Messages**: Audio message support
4. **Read Receipts**: Show when message was read
5. **Typing Indicators**: Real-time typing status
6. **Message Pinning**: Pin important messages
7. **Message Archiving**: Archive old conversations
8. **Bulk Operations**: Delete multiple messages
9. **Message Export**: Export conversation history
10. **Delivery Status**: Track message delivery

## Troubleshooting

### Common Issues

1. **Push notifications not working**:
   - Verify FCM credentials are configured
   - Check user has active push subscriptions
   - Review `fcm_service` logs

2. **Messages not marked as read**:
   - Ensure `GET /with/{user_id}` is called when viewing
   - Check `_mark_messages_as_read()` is executing

3. **Cannot send to user**:
   - Verify user exists and `is_bot = False`
   - Check user is active (`is_active = True`)

## Conclusion

The Direct Messaging system is now fully implemented with:
- ✅ One-to-one private conversations
- ✅ Read/unread tracking
- ✅ Message history with pagination
- ✅ Text and file support
- ✅ Push notifications
- ✅ Conversation list with unread counts
- ✅ User browsing for new chats
- ✅ Message reactions
- ✅ Edit and delete functionality
- ✅ Reply threading

The system is production-ready and follows Armada Den's architectural patterns.
