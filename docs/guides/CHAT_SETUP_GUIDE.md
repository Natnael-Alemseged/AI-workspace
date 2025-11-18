# Chat Feature Quick Setup Guide

## Prerequisites

- Python 3.12+
- PostgreSQL or SQLite database
- Supabase account (for media storage)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# Install/update dependencies
pip install -e .
```

The following packages will be installed:
- `python-socketio>=5.11.0` - Real-time communication
- `supabase>=2.3.0` - Media storage
- `python-multipart>=0.0.6` - File uploads

### 2. Configure Supabase

#### Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project or use existing one
3. Note your project URL and anon key

#### Create Storage Bucket
1. Navigate to Storage in Supabase dashboard
2. Create a new bucket named `chat-media`
3. Configure bucket settings:
   - **Public bucket**: If you want direct URL access
   - **Private bucket**: For authenticated access only (recommended)

#### Get Credentials
1. Go to Project Settings → API
2. Copy:
   - Project URL (e.g., `https://xxxxx.supabase.co`)
   - Anon/Public key

### 3. Update Environment Variables

Add to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_BUCKET=chat-media
```

### 4. Run Database Migration

```bash
# Apply the chat tables migration
alembic upgrade head
```

This creates:
- `chat_rooms` - Chat room information
- `chat_room_members` - Room membership
- `chat_messages` - All messages
- `message_read_receipts` - Read tracking

### 5. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start with:
- REST API: `http://localhost:8000/api/chat/*`
- Socket.IO: `ws://localhost:8000/socket.io`
- API Docs: `http://localhost:8000/docs`

### 6. Verify Installation

#### Test REST API

```bash
# Get JWT token first (login)
curl -X POST http://localhost:8000/api/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=yourpassword"

# Use the token to test chat endpoint
curl -X GET http://localhost:8000/api/chat/rooms \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Test Socket.IO Connection

Using Python:

```python
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('✅ Connected to Socket.IO server')

@sio.event
def connected(data):
    print(f'✅ Authenticated as user: {data["user_id"]}')

# Connect with JWT token
sio.connect(
    'http://localhost:8000',
    socketio_path='/socket.io',
    auth={'token': 'YOUR_JWT_TOKEN'}
)

sio.wait()
```

## Quick Test Workflow

### 1. Create a Direct Chat

```bash
curl -X POST http://localhost:8000/api/chat/rooms \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "room_type": "direct",
    "member_ids": ["OTHER_USER_UUID"]
  }'
```

### 2. Send a Message

```bash
curl -X POST http://localhost:8000/api/chat/messages \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "ROOM_UUID",
    "message_type": "text",
    "content": "Hello, World!"
  }'
```

### 3. Upload Media

```bash
curl -X POST http://localhost:8000/api/chat/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

### 4. Get Room Messages

```bash
curl -X GET "http://localhost:8000/api/chat/rooms/ROOM_UUID/messages?page=1&page_size=50" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Troubleshooting

### Issue: "SUPABASE_URL and SUPABASE_KEY must be set"

**Solution**: Ensure `.env` file contains valid Supabase credentials and restart the server.

### Issue: "Failed to upload media"

**Solutions**:
1. Verify Supabase bucket exists and is named `chat-media`
2. Check Supabase credentials are correct
3. Ensure bucket permissions allow uploads
4. Check file size limits

### Issue: Socket.IO connection fails

**Solutions**:
1. Verify JWT token is valid and not expired
2. Check CORS settings in `ALLOWED_ORIGINS`
3. Ensure Socket.IO path is `/socket.io`
4. Check server logs for authentication errors

### Issue: Migration fails

**Solutions**:
1. Check if previous migrations are applied: `alembic current`
2. Verify database connection in `.env`
3. For PostgreSQL, ensure user has CREATE TABLE permissions
4. If enums exist, drop them manually:
   ```sql
   DROP TYPE IF EXISTS messagetype CASCADE;
   DROP TYPE IF EXISTS chatroomtype CASCADE;
   ```

### Issue: "User is not a member of this room"

**Solution**: Ensure the user is added to the room via `POST /api/chat/rooms/{room_id}/members/{user_id}`

## Testing with Postman

1. Import the collection from `CHAT_FEATURE_README.md`
2. Set environment variables:
   - `base_url`: `http://localhost:8000`
   - `jwt_token`: Your JWT token from login
3. Run the requests in order:
   - Login → Create Room → Send Message → Get Messages

## Next Steps

1. **Frontend Integration**: Use Socket.IO client library in your frontend
2. **Push Notifications**: Integrate with Firebase Cloud Messaging or similar
3. **File Preview**: Add thumbnail generation for images/videos
4. **Search**: Implement full-text search for messages
5. **Analytics**: Track message metrics and user engagement

## API Documentation

Full API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support

For detailed documentation, see `CHAT_FEATURE_README.md`

For issues:
1. Check server logs for errors
2. Verify environment variables
3. Test database connection
4. Review Supabase dashboard for storage issues
