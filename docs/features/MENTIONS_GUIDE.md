# @Mentions Feature Guide

## Overview
The application supports **@mentions** in topic messages, allowing users to tag and notify other members of the topic.

---

## API Endpoint: Get Topic Members

### Fetch Members for @Mentions
**GET** `/channels/topics/{topic_id}/members`

**Purpose:** Get all active members of a topic to display in an @mention autocomplete dropdown.

**Authentication:** Required (Bearer token)

**Authorization:** User must be a member of the topic

**Response:** `200 OK`
```json
[
  {
    "id": "member-uuid",
    "user_id": "user-uuid-1",
    "user_email": "john.doe@example.com",
    "user_full_name": "John Doe",
    "joined_at": "2025-11-01T10:00:00Z",
    "last_read_at": "2025-11-14T13:00:00Z",
    "is_active": true
  },
  {
    "id": "member-uuid-2",
    "user_id": "user-uuid-2",
    "user_email": "jane.smith@example.com",
    "user_full_name": "Jane Smith",
    "joined_at": "2025-11-02T11:00:00Z",
    "last_read_at": "2025-11-14T12:30:00Z",
    "is_active": true
  }
]
```

**Error Responses:**
- `403 Forbidden` - User is not a member of the topic
- `500 Internal Server Error` - Server error

---

## Frontend Integration

### 1. Fetch Members When User Types "@"

```javascript
const fetchTopicMembers = async (topicId) => {
  const response = await fetch(
    `/channels/topics/${topicId}/members`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch members');
  }
  
  return response.json();
};

// Usage in your message input component
const handleInputChange = async (text) => {
  // Check if user typed "@"
  const lastChar = text[text.length - 1];
  const cursorPosition = getCursorPosition();
  
  if (lastChar === '@') {
    // Fetch members for autocomplete
    const members = await fetchTopicMembers(currentTopicId);
    showMentionDropdown(members);
  }
};
```

### 2. Display Autocomplete Dropdown

```javascript
const MentionDropdown = ({ members, onSelect }) => {
  return (
    <div className="mention-dropdown">
      {members.map(member => (
        <div 
          key={member.user_id}
          className="mention-item"
          onClick={() => onSelect(member)}
        >
          <div className="member-name">{member.user_full_name}</div>
          <div className="member-email">{member.user_email}</div>
        </div>
      ))}
    </div>
  );
};
```

### 3. Filter Members as User Types

```javascript
const filterMembers = (members, searchText) => {
  const search = searchText.toLowerCase();
  return members.filter(member => 
    member.user_full_name?.toLowerCase().includes(search) ||
    member.user_email?.toLowerCase().includes(search)
  );
};

// Example: User types "@joh"
const handleMentionSearch = (searchText) => {
  const filtered = filterMembers(allMembers, searchText);
  setFilteredMembers(filtered);
};
```

### 4. Insert Mention into Message

```javascript
const insertMention = (member, cursorPosition) => {
  const beforeCursor = messageText.substring(0, cursorPosition - 1); // -1 to remove "@"
  const afterCursor = messageText.substring(cursorPosition);
  
  // Insert mention (you can use email or full name)
  const mention = `@${member.user_email}`;
  const newText = beforeCursor + mention + ' ' + afterCursor;
  
  setMessageText(newText);
  
  // Track mentioned user IDs for the API
  setMentionedUserIds([...mentionedUserIds, member.user_id]);
};
```

### 5. Send Message with Mentions

```javascript
const sendMessage = async () => {
  const response = await fetch(
    `/channels/topics/${topicId}/messages`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        content: messageText,
        mentioned_user_ids: mentionedUserIds, // Array of UUIDs
        reply_to_id: replyToId || null
      })
    }
  );
  
  return response.json();
};
```

---

## Complete React Example

```jsx
import { useState, useEffect, useRef } from 'react';

const MessageInput = ({ topicId, onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [members, setMembers] = useState([]);
  const [filteredMembers, setFilteredMembers] = useState([]);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionedUserIds, setMentionedUserIds] = useState([]);
  const [mentionSearchText, setMentionSearchText] = useState('');
  const inputRef = useRef(null);

  // Fetch members when component mounts
  useEffect(() => {
    const fetchMembers = async () => {
      try {
        const response = await fetch(
          `/channels/topics/${topicId}/members`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        );
        const data = await response.json();
        setMembers(data);
      } catch (error) {
        console.error('Failed to fetch members:', error);
      }
    };

    fetchMembers();
  }, [topicId]);

  const handleInputChange = (e) => {
    const text = e.target.value;
    setMessage(text);

    // Check for @ mentions
    const cursorPosition = e.target.selectionStart;
    const textBeforeCursor = text.substring(0, cursorPosition);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');

    if (lastAtIndex !== -1) {
      const searchText = textBeforeCursor.substring(lastAtIndex + 1);
      
      // Only show mentions if @ is at start or after a space
      const charBeforeAt = textBeforeCursor[lastAtIndex - 1];
      if (!charBeforeAt || charBeforeAt === ' ' || charBeforeAt === '\n') {
        setMentionSearchText(searchText);
        const filtered = members.filter(m =>
          m.user_full_name?.toLowerCase().includes(searchText.toLowerCase()) ||
          m.user_email?.toLowerCase().includes(searchText.toLowerCase())
        );
        setFilteredMembers(filtered);
        setShowMentions(true);
        return;
      }
    }

    setShowMentions(false);
  };

  const handleMentionSelect = (member) => {
    const cursorPosition = inputRef.current.selectionStart;
    const textBeforeCursor = message.substring(0, cursorPosition);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
    
    const beforeMention = message.substring(0, lastAtIndex);
    const afterCursor = message.substring(cursorPosition);
    
    const newMessage = `${beforeMention}@${member.user_email} ${afterCursor}`;
    setMessage(newMessage);
    
    // Track mentioned user
    if (!mentionedUserIds.includes(member.user_id)) {
      setMentionedUserIds([...mentionedUserIds, member.user_id]);
    }
    
    setShowMentions(false);
    inputRef.current.focus();
  };

  const handleSend = async () => {
    if (!message.trim()) return;

    try {
      await onSendMessage({
        content: message,
        mentioned_user_ids: mentionedUserIds,
        reply_to_id: null
      });

      // Reset
      setMessage('');
      setMentionedUserIds([]);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return (
    <div className="message-input-container">
      <textarea
        ref={inputRef}
        value={message}
        onChange={handleInputChange}
        placeholder="Type @ to mention someone..."
        className="message-input"
      />
      
      {showMentions && filteredMembers.length > 0 && (
        <div className="mention-dropdown">
          {filteredMembers.map(member => (
            <div
              key={member.user_id}
              className="mention-item"
              onClick={() => handleMentionSelect(member)}
            >
              <div className="member-name">{member.user_full_name}</div>
              <div className="member-email">{member.user_email}</div>
            </div>
          ))}
        </div>
      )}
      
      <button onClick={handleSend}>Send</button>
    </div>
  );
};

export default MessageInput;
```

---

## Backend Processing

When a message is created with mentions:

1. **Content is parsed** for @mentions (email or full name)
2. **mentioned_user_ids** from the request are validated
3. **MessageMention records** are created for each mentioned user
4. **Only topic members** can be mentioned (validation happens automatically)
5. **Mentioned users** receive notifications (via Socket.IO or other means)

---

## Testing the Endpoint

### Using cURL

```bash
curl -X GET "http://localhost:8000/channels/topics/{topic_id}/members" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Expected Response

```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "user_email": "user@example.com",
    "user_full_name": "User Name",
    "joined_at": "2025-11-14T10:00:00Z",
    "last_read_at": "2025-11-14T13:00:00Z",
    "is_active": true
  }
]
```

---

## Summary

✅ **Endpoint implemented:** `GET /channels/topics/{topic_id}/members`  
✅ **Returns:** All active members with email and full name  
✅ **Authorization:** Only topic members can fetch the list  
✅ **Use case:** Populate @mention autocomplete dropdown  
✅ **Sorted by:** Join date (oldest first)  
✅ **Eager loading:** User info is pre-loaded for performance  

The backend is ready for @mention functionality. Just integrate the endpoint into your frontend autocomplete component!
