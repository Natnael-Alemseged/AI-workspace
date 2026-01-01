# Direct Messaging Quick Start Guide

Get started with the DM system in 5 minutes.

## 1. Apply Database Migration

```bash
cd "d:\code projects\back end\armada den\armada-den"
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade 3030c40d141d -> 3356464281d5, add_direct_messaging_system
```

## 2. Test with cURL

### Get Your Auth Token
First, login to get a JWT token:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'
```

Save the `access_token` from the response.

### Send a Message
```bash
curl -X POST http://localhost:8000/api/direct-messages/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_id": "RECEIVER_USER_UUID",
    "content": "Hello! This is my first DM."
  }'
```

### Get Conversations
```bash
curl -X GET http://localhost:8000/api/direct-messages/conversations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Messages with a User
```bash
curl -X GET "http://localhost:8000/api/direct-messages/with/USER_UUID?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Browse Users
```bash
curl -X GET "http://localhost:8000/api/direct-messages/users?search=john" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 3. Frontend Integration (React Example)

### Install Dependencies
```bash
npm install axios
```

### Create DM Service
```javascript
// services/dmService.js
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const dmService = {
  // Get auth headers
  getHeaders: () => ({
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json'
  }),

  // Get all conversations
  getConversations: async () => {
    const response = await axios.get(
      `${API_BASE}/direct-messages/conversations`,
      { headers: dmService.getHeaders() }
    );
    return response.data;
  },

  // Get messages with a user
  getMessages: async (userId, page = 1) => {
    const response = await axios.get(
      `${API_BASE}/direct-messages/with/${userId}`,
      { 
        params: { page, page_size: 50 },
        headers: dmService.getHeaders() 
      }
    );
    return response.data;
  },

  // Send a message
  sendMessage: async (receiverId, content, attachments = []) => {
    const response = await axios.post(
      `${API_BASE}/direct-messages/`,
      { receiver_id: receiverId, content, attachments },
      { headers: dmService.getHeaders() }
    );
    return response.data;
  },

  // Get eligible users
  getUsers: async (search = '') => {
    const response = await axios.get(
      `${API_BASE}/direct-messages/users`,
      { 
        params: { search },
        headers: dmService.getHeaders() 
      }
    );
    return response.data;
  },

  // Add reaction
  addReaction: async (messageId, emoji) => {
    const response = await axios.post(
      `${API_BASE}/direct-messages/${messageId}/reactions`,
      { emoji },
      { headers: dmService.getHeaders() }
    );
    return response.data;
  },

  // Remove reaction
  removeReaction: async (messageId, emoji) => {
    const response = await axios.delete(
      `${API_BASE}/direct-messages/${messageId}/reactions/${emoji}`,
      { headers: dmService.getHeaders() }
    );
    return response.data;
  },

  // Edit message
  editMessage: async (messageId, content) => {
    const response = await axios.patch(
      `${API_BASE}/direct-messages/${messageId}`,
      { content },
      { headers: dmService.getHeaders() }
    );
    return response.data;
  },

  // Delete message
  deleteMessage: async (messageId) => {
    await axios.delete(
      `${API_BASE}/direct-messages/${messageId}`,
      { headers: dmService.getHeaders() }
    );
  }
};

export default dmService;
```

### Conversation List Component
```jsx
// components/ConversationList.jsx
import React, { useEffect, useState } from 'react';
import dmService from '../services/dmService';

function ConversationList({ onSelectConversation }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await dmService.getConversations();
      setConversations(data.conversations);
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="conversation-list">
      <h2>Messages</h2>
      {conversations.map(conv => (
        <div 
          key={conv.user.id}
          className="conversation-item"
          onClick={() => onSelectConversation(conv.user)}
        >
          <div className="user-info">
            <strong>{conv.user.full_name || conv.user.email}</strong>
            {conv.user.is_online && <span className="online-dot">●</span>}
          </div>
          <div className="last-message">
            {conv.last_message?.content}
          </div>
          {conv.unread_count > 0 && (
            <span className="unread-badge">{conv.unread_count}</span>
          )}
        </div>
      ))}
    </div>
  );
}

export default ConversationList;
```

### Message Thread Component
```jsx
// components/MessageThread.jsx
import React, { useEffect, useState } from 'react';
import dmService from '../services/dmService';

function MessageThread({ user }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadMessages();
    }
  }, [user]);

  const loadMessages = async () => {
    try {
      const data = await dmService.getMessages(user.id);
      setMessages(data.messages.reverse()); // Reverse for chronological order
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      const message = await dmService.sendMessage(user.id, newMessage);
      setMessages([...messages, message]);
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleReaction = async (messageId, emoji) => {
    try {
      const reactions = await dmService.addReaction(messageId, emoji);
      // Update message reactions in state
      setMessages(messages.map(msg => 
        msg.id === messageId ? { ...msg, reactions } : msg
      ));
    } catch (error) {
      console.error('Error adding reaction:', error);
    }
  };

  if (!user) return <div>Select a conversation</div>;
  if (loading) return <div>Loading messages...</div>;

  return (
    <div className="message-thread">
      <div className="thread-header">
        <h3>{user.full_name || user.email}</h3>
        {user.is_online && <span>Online</span>}
      </div>

      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.sender_id === user.id ? 'received' : 'sent'}`}>
            <div className="message-content">{msg.content}</div>
            <div className="message-meta">
              <span>{new Date(msg.created_at).toLocaleTimeString()}</span>
              {msg.is_edited && <span>(edited)</span>}
            </div>
            {msg.attachments?.map(att => (
              <a key={att.id} href={att.url} target="_blank" rel="noopener noreferrer">
                📎 {att.filename}
              </a>
            ))}
            <div className="reactions">
              {msg.reactions?.map(reaction => (
                <span 
                  key={reaction.emoji}
                  className={reaction.user_reacted ? 'reacted' : ''}
                  onClick={() => handleReaction(msg.id, reaction.emoji)}
                >
                  {reaction.emoji} {reaction.count}
                </span>
              ))}
              <button onClick={() => handleReaction(msg.id, '👍')}>👍</button>
              <button onClick={() => handleReaction(msg.id, '❤️')}>❤️</button>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSend} className="message-input">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default MessageThread;
```

### Main App Component
```jsx
// App.jsx
import React, { useState } from 'react';
import ConversationList from './components/ConversationList';
import MessageThread from './components/MessageThread';
import './App.css';

function App() {
  const [selectedUser, setSelectedUser] = useState(null);

  return (
    <div className="app">
      <ConversationList onSelectConversation={setSelectedUser} />
      <MessageThread user={selectedUser} />
    </div>
  );
}

export default App;
```

### Basic Styling
```css
/* App.css */
.app {
  display: flex;
  height: 100vh;
}

.conversation-list {
  width: 300px;
  border-right: 1px solid #ddd;
  overflow-y: auto;
}

.conversation-item {
  padding: 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.conversation-item:hover {
  background: #f5f5f5;
}

.online-dot {
  color: #00ff00;
  margin-left: 5px;
}

.unread-badge {
  background: #007bff;
  color: white;
  border-radius: 50%;
  padding: 2px 8px;
  font-size: 12px;
}

.message-thread {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.thread-header {
  padding: 15px;
  border-bottom: 1px solid #ddd;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.message {
  margin-bottom: 15px;
  max-width: 70%;
}

.message.sent {
  margin-left: auto;
  background: #007bff;
  color: white;
  padding: 10px;
  border-radius: 10px;
}

.message.received {
  background: #f0f0f0;
  padding: 10px;
  border-radius: 10px;
}

.reactions {
  margin-top: 5px;
}

.reactions span {
  margin-right: 5px;
  cursor: pointer;
  padding: 2px 5px;
  border-radius: 5px;
}

.reactions span.reacted {
  background: #e0e0e0;
}

.message-input {
  display: flex;
  padding: 15px;
  border-top: 1px solid #ddd;
}

.message-input input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-right: 10px;
}

.message-input button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}
```

## 4. Test Push Notifications

### Subscribe to Push Notifications
```bash
curl -X POST http://localhost:8000/api/notifications/subscribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"endpoint":"YOUR_FCM_TOKEN"}'
```

### Send a Test Message
Send a message to another user who has subscribed. They should receive a push notification.

## 5. Common Operations

### Mark Bot Users
```sql
-- Mark specific users as bots
UPDATE users SET is_bot = true WHERE email IN ('bot1@example.com', 'bot2@example.com');
```

### Query Unread Messages
```sql
-- Get unread message count for a user
SELECT COUNT(*) FROM direct_messages 
WHERE receiver_id = 'USER_UUID' AND is_read = false;
```

### Get Recent Conversations
```sql
-- Get users with recent messages
SELECT DISTINCT ON (other_user_id) *
FROM (
  SELECT 
    CASE 
      WHEN sender_id = 'USER_UUID' THEN receiver_id 
      ELSE sender_id 
    END as other_user_id,
    created_at
  FROM direct_messages
  WHERE sender_id = 'USER_UUID' OR receiver_id = 'USER_UUID'
  ORDER BY created_at DESC
) subq;
```

## 6. Troubleshooting

### Check Migration Status
```bash
alembic current
```

### View Migration History
```bash
alembic history
```

### Rollback Migration
```bash
alembic downgrade -1
```

### Check Database Tables
```sql
\dt  -- List all tables (PostgreSQL)
SELECT * FROM direct_messages LIMIT 5;
```

### Enable Debug Logging
```python
# In your config
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 7. Next Steps

- ✅ Read `DIRECT_MESSAGING_IMPLEMENTATION.md` for detailed documentation
- ✅ Check `DM_API_REFERENCE.md` for complete API docs
- ✅ Review `DM_IMPLEMENTATION_SUMMARY.md` for overview
- ✅ Implement WebSocket for real-time updates (optional)
- ✅ Add typing indicators (optional)
- ✅ Implement message search (optional)

## Need Help?

- Check application logs for errors
- Review the implementation documentation
- Test with Postman/cURL first
- Verify authentication tokens are valid
- Ensure database migration was successful

---

**You're all set! Start building amazing DM features! 🚀**
