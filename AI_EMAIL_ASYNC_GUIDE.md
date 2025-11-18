# AI Async Processing - Implementation Guide

## Overview
AI processing (both chat and topic messages) now uses an **async pattern** with WebSocket notifications for better UX. Users get instant feedback, and AI responses arrive via Socket.IO as threaded replies.

## Backend Implementation

### Endpoints

#### 1. Chat Room AI Email
```
POST /api/ai/email
```

**Request Body:**
```json
{
  "room_id": "uuid-of-chat-room",
  "content": "Draft an email to John about the meeting"
}
```

**Response (Immediate - 202 Accepted):**
```json
{
  "status": "processing",
  "message_id": "uuid-of-user-message",
  "message": "Email sent to AI, response will arrive shortly"
}
```

#### 2. Topic Messages with AI Mentions
```
POST /api/channels/topics/{topic_id}/messages
```

**Request Body:**
```json
{
  "content": "@EmailAI send an email to john@example.com saying hi",
  "mentioned_user_ids": [],
  "reply_to_id": null
}
```

**Response (Immediate - 201 Created):**
Returns the user's message immediately. AI processing happens in background.

```json
{
  "id": "uuid",
  "topic_id": "uuid",
  "sender_id": "uuid",
  "content": "@EmailAI send an email...",
  "created_at": "2025-11-15T14:53:00Z",
  ...
}
```

### Flow

1. **User sends email** → Endpoint creates message immediately
2. **Message emitted** → User sees their message in chat instantly
3. **Background processing** → AI processes email asynchronously
4. **AI response** → Sent via WebSocket as a **reply** to original message

## Frontend Integration

### 1. Send Email to AI

```typescript
const sendEmailToAI = async (roomId: string, content: string) => {
  try {
    const response = await axios.post('/api/ai/email', {
      room_id: roomId,
      content: content
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    console.log('Email queued:', response.data.message_id);
    // User's message already appears in chat via socket
    
  } catch (error) {
    console.error('Failed to send email:', error);
    showError('Failed to send email to AI');
  }
};
```

### 2. Socket Event Listeners

```typescript
// Listen for typing indicator
socket.on('typing', (data: {
  room_id: string;
  user_type: 'ai' | 'user';
  is_typing: boolean;
}) => {
  if (data.user_type === 'ai') {
    if (data.is_typing) {
      showTypingIndicator('AI is thinking...');
    } else {
      hideTypingIndicator();
    }
  }
});

// Listen for new messages (including AI replies)
socket.on('new_message', (data: {
  message: {
    id: string;
    room_id: string;
    sender_id: string | null;  // null for AI
    content: string;
    message_type: string;
    created_at: string;
    reply_to_id?: string;  // Present if this is a reply
    reply_to?: {           // Reply context
      id: string;
      content: string;
      sender_name: string;
    };
    is_edited: boolean;
    is_deleted: boolean;
  };
  sender: {
    id?: string;
    email?: string;
    full_name?: string;
    type?: 'ai';           // Present for AI messages
    name?: string;         // "Email Assistant"
    avatar?: string;       // "🤖"
  };
}) => {
  // Add message to chat
  addMessageToChat(data.message);
  
  // If it's an AI reply, highlight the original message briefly
  if (data.message.reply_to_id && data.sender.type === 'ai') {
    highlightMessage(data.message.reply_to_id, 1000);
  }
});

// Listen for AI errors
socket.on('ai_error', (data: {
  room_id: string;
  error: string;
  original_message_id: string;
}) => {
  showError(data.error);
  // Optionally mark the original message with an error indicator
});
```

### 3. Message Component with Reply Threading

```tsx
interface Message {
  id: string;
  content: string;
  created_at: string;
  reply_to_id?: string;
  reply_to?: {
    id: string;
    content: string;
    sender_name: string;
  };
  sender: {
    id?: string;
    type?: 'ai';
    name?: string;
    avatar?: string;
  };
}

function MessageComponent({ message }: { message: Message }) {
  const isAI = message.sender.type === 'ai';
  
  return (
    <div className={`message ${isAI ? 'ai-message' : 'user-message'}`}>
      {/* Show reply preview if this is a reply */}
      {message.reply_to && (
        <div 
          className="reply-preview"
          onClick={() => scrollToMessage(message.reply_to_id)}
        >
          <div className="reply-indicator">↩️</div>
          <div className="reply-content">
            <span className="reply-sender">{message.reply_to.sender_name}</span>
            <span className="reply-text">{message.reply_to.content}</span>
          </div>
        </div>
      )}
      
      {/* Main message content */}
      <div className="message-content">
        <div className="message-header">
          <span className="sender-avatar">
            {isAI ? '🤖' : message.sender.avatar || '👤'}
          </span>
          <span className="sender-name">
            {isAI ? 'Email Assistant' : message.sender.name}
          </span>
        </div>
        <div className="message-text">{message.content}</div>
        <div className="message-time">
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  );
}
```

### 4. CSS for Reply Threading

```css
.reply-preview {
  background: rgba(0, 0, 0, 0.05);
  border-left: 3px solid #0066cc;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.reply-preview:hover {
  background: rgba(0, 0, 0, 0.08);
}

.reply-indicator {
  display: inline-block;
  margin-right: 8px;
  font-size: 14px;
}

.reply-sender {
  font-weight: 600;
  color: #0066cc;
  margin-right: 8px;
}

.reply-text {
  color: #666;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* AI message styling */
.ai-message {
  background: #f0f4ff;
  border-left: 3px solid #4a90e2;
}

/* Highlight animation when AI replies */
@keyframes highlight-flash {
  0%, 100% { background: transparent; }
  50% { background: rgba(0, 102, 204, 0.1); }
}

.message.highlighted {
  animation: highlight-flash 1s ease-in-out;
}
```

## User Experience Flow

```
1. User types email request
   ┌─────────────────────────────┐
   │ 👤 You                      │
   │ Draft an email to John      │
   │ about the meeting           │
   └─────────────────────────────┘

2. Message appears instantly ✓

3. AI typing indicator shows
   💭 AI is thinking...

4. AI response arrives as threaded reply
   ┌─────────────────────────────┐
   │ ↩️ You                      │
   │ Draft an email to John...   │
   ├─────────────────────────────┤
   │ 🤖 Email Assistant          │
   │ Here's a draft email:       │
   │                             │
   │ Subject: Meeting Follow-up  │
   │ Hi John, ...                │
   └─────────────────────────────┘
```

## Benefits

✅ **Instant Feedback** - User sees their message immediately  
✅ **No Timeouts** - AI can take as long as needed  
✅ **Real-time Updates** - Typing indicator shows AI is working  
✅ **Clear Threading** - AI response is visually linked to the request  
✅ **Better UX** - Feels like a natural chat conversation  
✅ **Scalability** - Backend can queue and process requests efficiently  

## Error Handling

If AI processing fails, users receive an `ai_error` event:

```typescript
socket.on('ai_error', (data) => {
  // Show error notification
  toast.error(data.error);
  
  // Optionally show error indicator on the original message
  markMessageAsError(data.original_message_id);
});
```

## Testing

1. **Send email request** to `/api/ai/email`
2. **Verify immediate response** (202 status)
3. **Check user message** appears in chat via socket
4. **Wait for typing indicator** (`typing` event with `is_typing: true`)
5. **Verify AI response** arrives via `new_message` event
6. **Check reply threading** - `reply_to_id` links to original message
7. **Test error handling** - disconnect AI service and verify error event

## Notes

- AI messages have `sender_id: null` (no user account)
- Reply context includes first 100 characters of original message
- Typing indicator automatically stops when response is sent
- Background tasks use FastAPI's `BackgroundTasks` for simplicity
- For production scale, consider migrating to Celery/Redis Queue
