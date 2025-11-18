# Real-Time Chat Feature Documentation

## Overview

This document describes the real-time chat feature added to the Armada Den FastAPI backend. The feature supports both 1-on-1 and group chats with real-time communication via Socket.IO, media file support via Supabase Storage, and comprehensive message management including edit, delete, reply, and forward functionality.

## Features

- ✅ **1-on-1 and Group Chats**: Support for direct messaging and group conversations
- ✅ **Real-Time Communication**: Socket.IO for instant message delivery
- ✅ **Media Support**: Upload and share images, videos, audio, and files
- ✅ **Message Management**: Edit, delete, reply to, and forward messages
- ✅ **Read Receipts**: Track when messages are read by users
- ✅ **Typing Indicators**: Show when users are typing
- ✅ **JWT Authentication**: Secure access control using existing JWT tokens
- ✅ **Access Control**: Room admins can manage members and settings

## Architecture

### Database Models

Located in `app/models/chat.py`:

1. **ChatRoom**: Stores chat room information
   - Supports both DIRECT (1-on-1) and GROUP types
   - Tracks creator, name, description, and avatar

2. **ChatRoomMember**: Manages room membership
   - Links users to rooms
   - Tracks admin status and last read timestamp
   - Supports soft deletion

3. **ChatMessage**: Stores all messages
   - Supports text and media (image, video, audio, file)
   - Tracks edits and deletions
   - Supports replies and forwards

4. **MessageReadReceipt**: Tracks message read status
   - Records when each user reads each message

### API Endpoints

Located in `app/api/routes/chat.py`:

#### Users

- `GET /api/users/users` - Get all users for chat selection (paginated, with search)
  - Returns user info with last message, unread count, and room_id for direct chats
  - Query params: `page`, `page_size`, `search` (optional)

#### Chat Rooms

- `POST /api/chat/rooms` - Create a new chat room
- `GET /api/chat/rooms` - Get user's chat rooms (paginated)
- `GET /api/chat/rooms/{room_id}` - Get room details
- `PATCH /api/chat/rooms/{room_id}` - Update room (admin only)
- `POST /api/chat/rooms/{room_id}/members/{user_id}` - Add member (admin only)
- `DELETE /api/chat/rooms/{room_id}/members/{user_id}` - Remove member (admin or self)

#### Messages

- `POST /api/chat/messages` - Create a new message
- `GET /api/chat/rooms/{room_id}/messages` - Get room messages (paginated)
- `PATCH /api/chat/messages/{message_id}` - Edit a message
- `DELETE /api/chat/messages/{message_id}` - Delete a message
- `POST /api/chat/rooms/{room_id}/read` - Mark messages as read

#### Media Upload

- `POST /api/chat/upload` - Upload media file
- `GET /api/chat/upload/signed-url` - Get signed URL for direct upload

### Socket.IO Events

Located in `app/services/socketio_service.py`:

#### Client → Server Events

- `connect` - Authenticate and establish connection
- `join_room` - Join a chat room
- `leave_room` - Leave a chat room
- `send_message` - Send a message (notification only)
- `typing` - Send typing indicator
- `message_edited` - Broadcast message edit
- `message_deleted` - Broadcast message deletion
- `mark_as_read` - Mark messages as read

#### Server → Client Events

- `connected` - Connection established
- `room_joined` - Successfully joined room
- `room_left` - Successfully left room
- `user_joined` - Another user joined room
- `user_left` - Another user left room
- `new_message` - New message received
- `message_edited` - Message was edited
- `message_deleted` - Message was deleted
- `messages_read` - Messages marked as read
- `user_typing` - User is typing
- `room_created` - New room created
- `room_updated` - Room details updated
- `member_added` - Member added to room
- `member_removed` - Member removed from room
- `error` - Error occurred

## Setup Instructions

### 1. Install Dependencies

```bash
pip install python-socketio supabase python-multipart
```

Or update your project:

```bash
pip install -e .
```

### 2. Configure Environment Variables

Add the following to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_BUCKET=chat-media
```

### 3. Set Up Supabase Storage

1. Create a new bucket in Supabase Storage named `chat-media`
2. Configure bucket permissions:
   - Make it private (authenticated users only)
   - Or make it public if you want direct access to media URLs

### 4. Run Database Migration

```bash
alembic upgrade head
```

This will create the following tables:
- `chat_rooms`
- `chat_room_members`
- `chat_messages`
- `message_read_receipts`

### 5. Start the Server

```bash
uvicorn app.main:app --reload
```

The Socket.IO server will be available at `ws://localhost:8000/socket.io`

## Usage Examples

### REST API Examples

#### Create a Direct Chat

```python
import requests

headers = {"Authorization": f"Bearer {jwt_token}"}

response = requests.post(
    "http://localhost:8000/api/chat/rooms",
    json={
        "room_type": "direct",
        "member_ids": ["other-user-uuid"]
    },
    headers=headers
)

room = response.json()
```

#### Create a Group Chat

```python
response = requests.post(
    "http://localhost:8000/api/chat/rooms",
    json={
        "name": "Project Team",
        "room_type": "group",
        "description": "Team collaboration chat",
        "member_ids": ["user1-uuid", "user2-uuid", "user3-uuid"]
    },
    headers=headers
)
```

#### Send a Text Message

```python
response = requests.post(
    "http://localhost:8000/api/chat/messages",
    json={
        "room_id": "room-uuid",
        "message_type": "text",
        "content": "Hello, team!"
    },
    headers=headers
)
```

#### Reply to a Message

```python
response = requests.post(
    "http://localhost:8000/api/chat/messages",
    json={
        "room_id": "room-uuid",
        "message_type": "text",
        "content": "Thanks for the update!",
        "reply_to_id": "original-message-uuid"
    },
    headers=headers
)
```

#### Upload Media

```python
files = {"file": open("image.jpg", "rb")}
response = requests.post(
    "http://localhost:8000/api/chat/upload",
    files=files,
    headers=headers
)

media_data = response.json()

# Send message with media
requests.post(
    "http://localhost:8000/api/chat/messages",
    json={
        "room_id": "room-uuid",
        "message_type": "image",
        "content": "Check out this image!",
        "media_url": media_data["url"],
        "media_filename": media_data["filename"],
        "media_size": media_data["size"],
        "media_mime_type": media_data["mime_type"]
    },
    headers=headers
)
```

### Socket.IO Client Examples

#### JavaScript/TypeScript Client

```typescript
import io from 'socket.io-client';

// Connect with JWT authentication
const socket = io('http://localhost:8000', {
  path: '/socket.io',
  auth: {
    token: 'your-jwt-token'
  }
});

// Connection events
socket.on('connected', (data) => {
  console.log('Connected:', data.user_id);
});

// Join a room
socket.emit('join_room', { room_id: 'room-uuid' });

socket.on('room_joined', (data) => {
  console.log('Joined room:', data.room_id);
});

// Listen for new messages
socket.on('new_message', (data) => {
  console.log('New message:', data.message);
  // Update UI with new message
});

// Send typing indicator
socket.emit('typing', {
  room_id: 'room-uuid',
  is_typing: true
});

// Listen for typing indicators
socket.on('user_typing', (data) => {
  console.log(`User ${data.user_id} is typing in room ${data.room_id}`);
});

// Mark messages as read
socket.emit('mark_as_read', {
  room_id: 'room-uuid',
  message_ids: ['msg1-uuid', 'msg2-uuid']
});

// Listen for read receipts
socket.on('messages_read', (data) => {
  console.log(`User ${data.user_id} read messages:`, data.message_ids);
});
```

#### Python Client

```python
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')

@sio.on('new_message')
def on_new_message(data):
    print(f"New message: {data}")

@sio.on('user_typing')
def on_typing(data):
    print(f"User {data['user_id']} is typing")

# Connect with authentication
sio.connect(
    'http://localhost:8000',
    socketio_path='/socket.io',
    auth={'token': 'your-jwt-token'}
)

# Join a room
sio.emit('join_room', {'room_id': 'room-uuid'})

# Send typing indicator
sio.emit('typing', {'room_id': 'room-uuid', 'is_typing': True})

sio.wait()
```

## Access Control

### Room Permissions

- **Creator**: Automatically becomes admin
- **Admin**: Can:
  - Update room details (name, description, avatar)
  - Add/remove members
  - Delete any message in the room
  
- **Member**: Can:
  - Send messages
  - Edit own messages
  - Delete own messages
  - Leave the room

### Message Permissions

- **Edit**: Only the sender can edit their messages
- **Delete**: Sender or room admin can delete messages
- **Reply/Forward**: Any room member can reply to or forward messages

## Database Schema

```sql
-- Chat Rooms
CREATE TABLE chat_rooms (
    id UUID PRIMARY KEY,
    name VARCHAR,
    room_type ENUM('DIRECT', 'GROUP'),
    description TEXT,
    avatar_url VARCHAR,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN
);

-- Room Members
CREATE TABLE chat_room_members (
    id UUID PRIMARY KEY,
    room_id UUID REFERENCES chat_rooms(id),
    user_id UUID REFERENCES users(id),
    joined_at TIMESTAMP WITH TIME ZONE,
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_admin BOOLEAN,
    is_active BOOLEAN
);

-- Messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    room_id UUID REFERENCES chat_rooms(id),
    sender_id UUID REFERENCES users(id),
    message_type ENUM('TEXT', 'IMAGE', 'VIDEO', 'AUDIO', 'FILE'),
    content TEXT,
    media_url VARCHAR,
    media_filename VARCHAR,
    media_size INTEGER,
    media_mime_type VARCHAR,
    reply_to_id UUID REFERENCES chat_messages(id),
    forwarded_from_id UUID REFERENCES chat_messages(id),
    is_edited BOOLEAN,
    edited_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);

-- Read Receipts
CREATE TABLE message_read_receipts (
    id UUID PRIMARY KEY,
    message_id UUID REFERENCES chat_messages(id),
    user_id UUID REFERENCES users(id),
    read_at TIMESTAMP WITH TIME ZONE
);
```

## Testing

### Test Socket.IO Connection

```bash
# Install socket.io-client for testing
npm install -g socket.io-client

# Or use Python
pip install python-socketio[client]
```

### Manual Testing Checklist

- [ ] Create a direct chat
- [ ] Create a group chat
- [ ] Send text messages
- [ ] Upload and send media files
- [ ] Edit a message
- [ ] Delete a message
- [ ] Reply to a message
- [ ] Forward a message
- [ ] Mark messages as read
- [ ] Test typing indicators
- [ ] Add member to group
- [ ] Remove member from group
- [ ] Update room details
- [ ] Test real-time notifications

## Troubleshooting

### Socket.IO Connection Issues

1. **CORS errors**: Ensure `ALLOWED_ORIGINS` in config includes your client URL
2. **Authentication failed**: Verify JWT token is valid and not expired
3. **Connection timeout**: Check if server is running and Socket.IO path is correct

### Media Upload Issues

1. **Upload failed**: Verify Supabase credentials are correct
2. **File too large**: Check Supabase bucket size limits
3. **Invalid file type**: Ensure MIME type is supported

### Database Issues

1. **Migration failed**: Check if previous migrations are applied
2. **Foreign key errors**: Ensure users table exists
3. **Enum errors**: Drop and recreate enums if needed

## Performance Considerations

- **Pagination**: All list endpoints support pagination to handle large datasets
- **Indexes**: Database indexes on foreign keys and timestamps for fast queries
- **Soft Deletes**: Messages are soft-deleted to maintain conversation history
- **Connection Pooling**: AsyncSession pooling for efficient database access

## Security Considerations

- **JWT Authentication**: All endpoints and Socket.IO connections require valid JWT
- **Access Control**: Room membership verified before any operation
- **Media Storage**: Supabase signed URLs for secure media access
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection**: SQLAlchemy ORM prevents SQL injection attacks

## Future Enhancements

- [ ] Message reactions (emoji reactions)
- [ ] Voice/video calling integration
- [ ] Message search functionality
- [ ] File preview generation
- [ ] Message threading
- [ ] User presence (online/offline status)
- [ ] Push notifications
- [ ] Message encryption (end-to-end)
- [ ] Chat export functionality
- [ ] Advanced admin controls (mute, ban)

## Support

For issues or questions, please refer to the main project documentation or contact the development team.
