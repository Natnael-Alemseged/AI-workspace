# Channels & Topics Feature Documentation

## Overview

This feature implements a role-based channel and topic system for organized team communication. It extends the existing chat functionality with hierarchical organization, user mentions, reactions, and admin-controlled access.

## Architecture

### Role System

**User Roles:**
- `ADMIN`: Can create/manage channels, topics, and add/remove users
- `USER`: Can participate in topics they're added to

### Hierarchy

```
Channels (e.g., "Design", "Development")
  └── Topics (e.g., "Logo Redesign", "API Architecture")
      └── Messages (with mentions, reactions, replies)
```

## Database Models

### 1. User Role Enhancement
- Added `role` field to `User` model (ADMIN/USER)
- Default role: USER

### 2. Channel Model
- **Fields**: name, description, icon, color, created_by, timestamps
- **Purpose**: Top-level organization (e.g., Design, Development, Marketing)
- **Access**: Admin-only creation and management

### 3. Topic Model
- **Fields**: channel_id, name, description, is_pinned, created_by, timestamps
- **Purpose**: Discussion threads within channels
- **Access**: Admin creates, adds specific users as members

### 4. TopicMember Model
- **Fields**: topic_id, user_id, joined_at, last_read_at, is_active
- **Purpose**: Track topic membership and read status

### 5. TopicMessage Model
- **Fields**: topic_id, sender_id, content, reply_to_id, edit/delete tracking
- **Purpose**: Messages within topics
- **Features**: Reply threading, edit history, soft delete

### 6. MessageMention Model
- **Fields**: message_id, mentioned_user_id, is_read
- **Purpose**: Track @mentions (e.g., "@nati")
- **Features**: Mention extraction from content, notification system

### 7. MessageReaction Model
- **Fields**: message_id, user_id, emoji
- **Purpose**: Emoji reactions to messages
- **Constraint**: Unique per user/message/emoji combination

## API Endpoints

### Channel Endpoints (Admin Only)

```
POST   /api/channels                    - Create channel
GET    /api/channels                    - List all channels
GET    /api/channels/{channel_id}       - Get channel details
PATCH  /api/channels/{channel_id}       - Update channel
DELETE /api/channels/{channel_id}       - Delete channel
```

### Topic Endpoints

```
POST   /api/channels/topics                        - Create topic (admin)
GET    /api/channels/{channel_id}/topics           - List channel topics
GET    /api/channels/topics/my                     - List user's topics
GET    /api/channels/topics/{topic_id}             - Get topic details
PATCH  /api/channels/topics/{topic_id}             - Update topic (admin)
POST   /api/channels/topics/{topic_id}/members/{user_id}   - Add member (admin)
DELETE /api/channels/topics/{topic_id}/members/{user_id}   - Remove member (admin)
```

### Message Endpoints

```
POST   /api/channels/topics/messages                     - Create message
GET    /api/channels/topics/{topic_id}/messages          - List messages
PATCH  /api/channels/topics/messages/{message_id}        - Edit message
DELETE /api/channels/topics/messages/{message_id}        - Delete message
```

### Reaction Endpoints

```
POST   /api/channels/topics/messages/{message_id}/reactions        - Add reaction
DELETE /api/channels/topics/messages/{message_id}/reactions/{emoji} - Remove reaction
```

## Socket.IO Events

### Client → Server Events

```javascript
// Join a topic
socket.emit('join_topic', { topic_id: 'uuid' });

// Leave a topic
socket.emit('leave_topic', { topic_id: 'uuid' });

// Typing indicator
socket.emit('topic_typing', { topic_id: 'uuid', is_typing: true });

// Mention notification
socket.emit('mention_notification', {
  mentioned_user_id: 'uuid',
  topic_id: 'uuid',
  message_id: 'uuid'
});
```

### Server → Client Events

```javascript
// Topic events
socket.on('topic_created', (data) => { /* { topic_id, channel_id, name, created_by } */ });
socket.on('topic_updated', (data) => { /* { topic_id, updated_by } */ });
socket.on('topic_joined', (data) => { /* { topic_id } */ });
socket.on('topic_left', (data) => { /* { topic_id } */ });

// Member events
socket.on('member_added', (data) => { /* { topic_id, user_id, added_by } */ });
socket.on('member_removed', (data) => { /* { topic_id, user_id, removed_by } */ });
socket.on('user_joined_topic', (data) => { /* { topic_id, user_id } */ });
socket.on('user_left_topic', (data) => { /* { topic_id, user_id } */ });

// Message events
socket.on('new_topic_message', (data) => { /* { topic_id, message: {...} } */ });
socket.on('topic_message_edited', (data) => { /* { topic_id, message_id, content, edited_by } */ });
socket.on('topic_message_deleted', (data) => { /* { topic_id, message_id, deleted_by } */ });

// Typing indicator
socket.on('user_typing_topic', (data) => { /* { topic_id, user_id, is_typing } */ });

// Mention notification
socket.on('mentioned', (data) => { /* { topic_id, message_id, mentioned_by } */ });

// Reaction events
socket.on('reaction_added', (data) => { /* { topic_id, message_id, user_id, emoji } */ });
socket.on('reaction_removed', (data) => { /* { topic_id, message_id, user_id, emoji } */ });
```

## Features

### 1. User Mentions
- **Syntax**: `@username` or `@"Full Name"`
- **Detection**: Automatic extraction from message content
- **Validation**: Only topic members can be mentioned
- **Notifications**: Real-time via Socket.IO + database tracking
- **Read Status**: Track if mention has been seen

### 2. Message Reactions
- **Type**: Emoji reactions (unicode or shortcode)
- **Constraint**: One reaction per user per emoji per message
- **Aggregation**: Grouped by emoji with user lists
- **Real-time**: Instant updates via Socket.IO

### 3. Message Threading
- **Reply To**: Reference parent message with `reply_to_id`
- **Display**: Show replied message content in UI
- **Navigation**: Jump to parent message

### 4. Edit & Delete
- **Edit**: Track edit history with `is_edited` and `edited_at`
- **Delete**: Soft delete with `is_deleted` and `deleted_at`
- **Permissions**: Sender can edit/delete, admins can delete any

### 5. Typing Indicators
- Real-time typing status broadcast to topic members
- Excludes sender from receiving their own typing status

### 6. Read Tracking
- `last_read_at` timestamp per topic member
- Calculate unread counts
- Mark messages as read functionality

## Permission System

### Admin Capabilities
- Create/update/delete channels
- Create/update topics
- Add/remove users from topics
- Delete any message
- Pin/unpin topics

### User Capabilities
- View channels (all users)
- Participate in topics they're members of
- Send messages in their topics
- Edit/delete own messages
- Add reactions
- Mention other topic members

## Migration

Run the migration to create new tables:

```bash
alembic upgrade head
```

This creates:
- `channels` table
- `topics` table
- `topic_members` table
- `topic_messages` table
- `message_mentions` table
- `message_reactions` table
- Adds `role` column to `users` table

## Usage Examples

### 1. Admin Creates Channel

```python
POST /api/channels
{
  "name": "Development",
  "description": "All development discussions",
  "icon": "💻",
  "color": "#3B82F6"
}
```

### 2. Admin Creates Topic with Members

```python
POST /api/channels/topics
{
  "channel_id": "uuid",
  "name": "API Architecture",
  "description": "Discuss API design decisions",
  "member_ids": ["user1_uuid", "user2_uuid", "user3_uuid"]
}
```

### 3. User Sends Message with Mentions

```python
POST /api/channels/topics/messages
{
  "topic_id": "uuid",
  "content": "Hey @nati, can you review this? Also cc @\"John Doe\"",
  "mentioned_user_ids": ["nati_uuid", "john_uuid"]
}
```

### 4. User Adds Reaction

```python
POST /api/channels/topics/messages/{message_id}/reactions
{
  "emoji": "👍"
}
```

### 5. User Replies to Message

```python
POST /api/channels/topics/messages
{
  "topic_id": "uuid",
  "content": "I agree with your point",
  "reply_to_id": "parent_message_uuid"
}
```

## Integration with Existing Chat

The new channel/topic system **coexists** with the existing chat system:

- **Existing Chat**: Direct messages and group chats (ChatRoom, ChatMessage)
- **New System**: Organized channels and topics (Channel, Topic, TopicMessage)
- **Shared**: Socket.IO infrastructure, authentication, user management

Both systems use the same Socket.IO connection and authentication mechanism.

## Best Practices

### For Admins
1. Create logical channel groupings (e.g., by department or project)
2. Use descriptive topic names
3. Add relevant users to topics
4. Pin important topics
5. Use colors and icons for visual organization

### For Users
1. Use @mentions to notify specific users
2. Reply to messages to maintain context
3. Use reactions for quick feedback
4. Edit messages instead of deleting and reposting
5. Check unread counts regularly

## Security Considerations

1. **Authentication**: All endpoints require valid JWT token
2. **Authorization**: Admin-only operations verified at service layer
3. **Membership**: Users can only access topics they're members of
4. **Mentions**: Only topic members can be mentioned
5. **Soft Deletes**: Messages are never hard-deleted, maintaining audit trail

## Performance Optimizations

1. **Pagination**: All list endpoints support pagination
2. **Eager Loading**: Related data loaded efficiently with SQLAlchemy
3. **Indexes**: Database indexes on foreign keys and timestamps
4. **Caching**: Consider Redis for active topic lists
5. **Socket.IO Rooms**: Efficient message broadcasting per topic

## Future Enhancements

- [ ] File attachments in topic messages
- [ ] Message search within topics
- [ ] Topic templates
- [ ] User presence indicators
- [ ] Message pinning within topics
- [ ] Thread view for replies
- [ ] Notification preferences per topic
- [ ] Topic archiving
- [ ] Analytics and insights
- [ ] Integration with AI agents

## Testing

Test the feature with:

```bash
# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload

# Connect Socket.IO client
# Test authentication with JWT token
# Test channel creation (as admin)
# Test topic creation and member management
# Test messaging with mentions and reactions
```

## Troubleshooting

### Issue: "Only admins can create channels"
**Solution**: Ensure user has `role='admin'` or `is_superuser=True`

### Issue: "User is not a member of this topic"
**Solution**: Admin must add user to topic first via `/topics/{topic_id}/members/{user_id}`

### Issue: Socket.IO not connecting
**Solution**: Check JWT token in auth data, verify CORS settings

### Issue: Mentions not working
**Solution**: Ensure mentioned users are topic members, check username format

## Support

For issues or questions:
1. Check this documentation
2. Review API endpoint responses for error details
3. Check server logs for detailed error messages
4. Verify database migrations are up to date
