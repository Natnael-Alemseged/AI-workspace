# Quick Start Guide: Channels & Topics Feature

## Prerequisites

- Python 3.9+
- PostgreSQL database
- Existing Armada Den installation

## Step 1: Run Database Migration

```bash
# Navigate to project directory
cd "d:\code projects\back end\armada den\armada-den"

# Activate virtual environment
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Run migration
alembic upgrade head
```

This creates all necessary tables:
- `channels`
- `topics`
- `topic_members`
- `topic_messages`
- `message_mentions`
- `message_reactions`
- Adds `role` column to `users`

## Step 2: Create Admin User

You need at least one admin user to create channels and topics.

### Recommended: Use the Seeding Script ⭐

```bash
# Run the interactive seeding script
python seed_admin.py
```

Then select option 1 to create a new admin user interactively, or option 2 to promote an existing user.

**For detailed instructions, see [ADMIN_SEEDING_GUIDE.md](ADMIN_SEEDING_GUIDE.md)**

### Quick Alternative: Via Database

```sql
-- Connect to your PostgreSQL database
psql -U your_username -d armada_den

-- Update existing user role to admin
UPDATE users 
SET role = 'admin', is_superuser = true, is_verified = true
WHERE email = 'your-admin-email@example.com';
```

### Alternative: Via Python Script

Create a file `promote_admin.py`:

```python
import asyncio
from sqlalchemy import select, update
from app.db import AsyncSessionLocal
from app.models.user import User, UserRole

async def promote_to_admin(email: str):
    async with AsyncSessionLocal() as session:
        # Find user
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User with email {email} not found")
            return
        
        # Update role
        user.role = UserRole.ADMIN
        await session.commit()
        
        print(f"Successfully promoted {email} to admin")

if __name__ == "__main__":
    email = input("Enter user email to promote: ")
    asyncio.run(promote_to_admin(email))
```

Run it:
```bash
python promote_admin.py
```

## Step 3: Start the Server

```bash
# Make sure you're in the project directory with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

## Step 4: Test with API Calls

### 4.1 Get Authentication Token

First, login to get your JWT token:

```bash
# Login (adjust based on your auth setup)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-admin-email@example.com",
    "password": "your-password"
  }'
```

Save the `access_token` from the response.

### 4.2 Create a Channel (Admin Only)

```bash
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Development",
    "description": "All development discussions",
    "icon": "💻",
    "color": "#3B82F6"
  }'
```

Save the `id` from the response (channel_id).

### 4.3 List All Channels

```bash
curl -X GET http://localhost:8000/api/channels \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4.4 Create a Topic (Admin Only)

First, get user IDs to add as members:

```bash
# List users
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Create topic:

```bash
curl -X POST http://localhost:8000/api/channels/topics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "channel_id": "YOUR_CHANNEL_ID",
    "name": "API Architecture",
    "description": "Discuss API design decisions",
    "member_ids": ["USER_ID_1", "USER_ID_2"]
  }'
```

Save the `id` from the response (topic_id).

### 4.5 Send a Message

```bash
curl -X POST http://localhost:8000/api/channels/topics/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "topic_id": "YOUR_TOPIC_ID",
    "content": "Hello everyone! This is our first message.",
    "mentioned_user_ids": []
  }'
```

### 4.6 Send Message with Mention

```bash
curl -X POST http://localhost:8000/api/channels/topics/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "topic_id": "YOUR_TOPIC_ID",
    "content": "Hey @john, can you review this?",
    "mentioned_user_ids": ["JOHN_USER_ID"]
  }'
```

### 4.7 Add Reaction

```bash
curl -X POST http://localhost:8000/api/channels/topics/messages/MESSAGE_ID/reactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "emoji": "👍"
  }'
```

### 4.8 Get Topic Messages

```bash
curl -X GET "http://localhost:8000/api/channels/topics/YOUR_TOPIC_ID/messages?page=1&page_size=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Step 5: Test Socket.IO Connection

### Using Browser Console

```javascript
// Open browser console (F12) and run:

// 1. Load Socket.IO client
const script = document.createElement('script');
script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
document.head.appendChild(script);

// 2. After script loads, connect
script.onload = () => {
  const token = 'YOUR_ACCESS_TOKEN';
  
  const socket = io('http://localhost:8000', {
    path: '/socket.io',
    auth: { token }
  });
  
  socket.on('connect', () => {
    console.log('Connected!');
    
    // Join a topic
    socket.emit('join_topic', { topic_id: 'YOUR_TOPIC_ID' });
  });
  
  socket.on('topic_joined', (data) => {
    console.log('Joined topic:', data);
  });
  
  socket.on('new_topic_message', (data) => {
    console.log('New message:', data);
  });
  
  socket.on('user_typing_topic', (data) => {
    console.log('User typing:', data);
  });
  
  socket.on('error', (error) => {
    console.error('Error:', error);
  });
  
  // Make socket available globally for testing
  window.testSocket = socket;
};

// 3. Test typing indicator
window.testSocket.emit('topic_typing', {
  topic_id: 'YOUR_TOPIC_ID',
  is_typing: true
});
```

### Using Python Client

Create `test_socketio.py`:

```python
import socketio
import asyncio

async def test_connection():
    sio = socketio.AsyncClient()
    
    @sio.event
    async def connect():
        print('Connected to server')
        
        # Join topic
        await sio.emit('join_topic', {'topic_id': 'YOUR_TOPIC_ID'})
    
    @sio.event
    async def topic_joined(data):
        print('Joined topic:', data)
    
    @sio.event
    async def new_topic_message(data):
        print('New message:', data)
    
    @sio.event
    async def disconnect():
        print('Disconnected from server')
    
    # Connect with auth token
    await sio.connect(
        'http://localhost:8000',
        socketio_path='/socket.io',
        auth={'token': 'YOUR_ACCESS_TOKEN'}
    )
    
    # Keep connection alive
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(test_connection())
```

Run it:
```bash
pip install python-socketio[asyncio_client]
python test_socketio.py
```

## Step 6: Verify Everything Works

### Checklist

- [ ] Database migration completed successfully
- [ ] At least one user has admin role
- [ ] Server starts without errors
- [ ] Can create a channel (admin)
- [ ] Can create a topic (admin)
- [ ] Can add members to topic (admin)
- [ ] Can send messages in topic
- [ ] Can mention users with @username
- [ ] Can add reactions to messages
- [ ] Socket.IO connection works
- [ ] Real-time message updates work
- [ ] Typing indicators work

## Common Issues & Solutions

### Issue: "Only admins can create channels"

**Solution:**
```sql
-- Check user role
SELECT email, role FROM users WHERE email = 'your-email@example.com';

-- If role is NULL or 'user', update it
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
```

### Issue: "User is not a member of this topic"

**Solution:**
Admin must add user to topic first:
```bash
curl -X POST http://localhost:8000/api/channels/topics/TOPIC_ID/members/USER_ID \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### Issue: Socket.IO connection fails

**Solution:**
1. Check JWT token is valid
2. Verify CORS settings in `app/core/config.py`
3. Check server logs for authentication errors
4. Try with `transports: ['polling']` first, then add 'websocket'

### Issue: Migration fails

**Solution:**
```bash
# Check current migration version
alembic current

# If there are conflicts, check migration history
alembic history

# If needed, downgrade and re-upgrade
alembic downgrade -1
alembic upgrade head
```

### Issue: "Channel name already exists"

**Solution:**
Channel names must be unique. Either:
1. Use a different name
2. Delete the existing channel (admin only)
3. Update the existing channel instead

## Testing Workflow

### Complete Test Scenario

1. **Admin creates channel "Engineering"**
   ```bash
   POST /api/channels
   ```

2. **Admin creates topic "Sprint Planning"**
   ```bash
   POST /api/channels/topics
   ```

3. **Admin adds 3 users to topic**
   ```bash
   POST /api/channels/topics/{topic_id}/members/{user_id}
   ```

4. **User 1 joins topic via Socket.IO**
   ```javascript
   socket.emit('join_topic', { topic_id: '...' });
   ```

5. **User 1 sends message mentioning User 2**
   ```bash
   POST /api/channels/topics/messages
   Content: "Hey @user2, what do you think?"
   ```

6. **User 2 receives mention notification via Socket.IO**
   ```javascript
   socket.on('mentioned', (data) => { ... });
   ```

7. **User 3 adds reaction to message**
   ```bash
   POST /api/channels/topics/messages/{message_id}/reactions
   ```

8. **All users see reaction update in real-time**
   ```javascript
   socket.on('reaction_added', (data) => { ... });
   ```

9. **User 1 edits their message**
   ```bash
   PATCH /api/channels/topics/messages/{message_id}
   ```

10. **All users see edit update**
    ```javascript
    socket.on('topic_message_edited', (data) => { ... });
    ```

## Next Steps

1. **Build Frontend UI**
   - Use React, Vue, or vanilla JS
   - Implement channel list, topic list, message view
   - Add mention autocomplete
   - Add reaction picker

2. **Add Features**
   - File attachments
   - Message search
   - Notifications
   - User presence

3. **Deploy**
   - Set up production database
   - Configure environment variables
   - Set up reverse proxy (nginx)
   - Enable SSL/TLS

## API Documentation

Once server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Browse all available endpoints and test them interactively.

## Support Files

- **Feature Documentation**: `CHANNELS_TOPICS_FEATURE.md`
- **Socket.IO Client Guide**: `SOCKETIO_CLIENT_GUIDE.md`
- **Migration File**: `alembic/versions/add_channels_topics_system.py`

## Getting Help

1. Check server logs for detailed error messages
2. Review the feature documentation
3. Test with curl/Postman before implementing frontend
4. Use browser dev tools to debug Socket.IO connections
5. Check database for data consistency

Happy coding! 🚀
