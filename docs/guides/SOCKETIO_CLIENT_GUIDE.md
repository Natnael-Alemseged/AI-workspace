# Socket.IO Client Integration Guide

## Connection Setup

```javascript
import io from 'socket.io-client';

// Get JWT token from your auth system
const token = localStorage.getItem('access_token');

// Connect to Socket.IO server
const socket = io('http://localhost:8000', {
  path: '/socket.io',
  auth: {
    token: token
  },
  transports: ['websocket', 'polling']
});

// Connection events
socket.on('connect', () => {
  console.log('Connected to Socket.IO server');
});

socket.on('connected', (data) => {
  console.log('Authenticated as user:', data.user_id);
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
});

socket.on('error', (error) => {
  console.error('Socket.IO error:', error);
});
```

## Topic Management

### Join a Topic

```javascript
// Join topic to receive real-time updates
socket.emit('join_topic', { topic_id: 'topic-uuid-here' });

socket.on('topic_joined', (data) => {
  console.log('Successfully joined topic:', data.topic_id);
  // Load topic messages
  fetchTopicMessages(data.topic_id);
});

socket.on('user_joined_topic', (data) => {
  console.log(`User ${data.user_id} joined topic ${data.topic_id}`);
  // Update UI to show new member
});
```

### Leave a Topic

```javascript
socket.emit('leave_topic', { topic_id: 'topic-uuid-here' });

socket.on('topic_left', (data) => {
  console.log('Left topic:', data.topic_id);
});

socket.on('user_left_topic', (data) => {
  console.log(`User ${data.user_id} left topic ${data.topic_id}`);
  // Update UI to remove member
});
```

## Real-time Messaging

### Receive New Messages

```javascript
socket.on('new_topic_message', (data) => {
  const { topic_id, message } = data;
  
  // Add message to UI
  addMessageToTopic(topic_id, {
    id: message.id,
    sender_id: message.sender_id,
    content: message.content,
    created_at: message.created_at,
    reply_to_id: message.reply_to_id
  });
  
  // Play notification sound if not from current user
  if (message.sender_id !== currentUserId) {
    playNotificationSound();
  }
});
```

### Send Messages (via REST API)

```javascript
// Messages are sent via REST API, then broadcast via Socket.IO
async function sendMessage(topicId, content, mentionedUserIds = [], replyToId = null) {
  const response = await fetch('/api/channels/topics/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      topic_id: topicId,
      content: content,
      mentioned_user_ids: mentionedUserIds,
      reply_to_id: replyToId
    })
  });
  
  const message = await response.json();
  // Message will be broadcast to all topic members via Socket.IO
  return message;
}
```

### Message Edits

```javascript
socket.on('topic_message_edited', (data) => {
  const { topic_id, message_id, content, edited_by } = data;
  
  // Update message in UI
  updateMessageContent(message_id, content);
  
  // Show "edited" indicator
  showEditedIndicator(message_id);
});
```

### Message Deletions

```javascript
socket.on('topic_message_deleted', (data) => {
  const { topic_id, message_id, deleted_by } = data;
  
  // Remove or gray out message in UI
  markMessageAsDeleted(message_id);
});
```

## Typing Indicators

### Send Typing Status

```javascript
let typingTimeout;

function handleTyping(topicId) {
  // Send typing start
  socket.emit('topic_typing', {
    topic_id: topicId,
    is_typing: true
  });
  
  // Clear previous timeout
  clearTimeout(typingTimeout);
  
  // Stop typing after 3 seconds of inactivity
  typingTimeout = setTimeout(() => {
    socket.emit('topic_typing', {
      topic_id: topicId,
      is_typing: false
    });
  }, 3000);
}

// Attach to input field
messageInput.addEventListener('input', () => {
  handleTyping(currentTopicId);
});
```

### Receive Typing Status

```javascript
const typingUsers = new Map(); // topicId -> Set of userIds

socket.on('user_typing_topic', (data) => {
  const { topic_id, user_id, is_typing } = data;
  
  if (!typingUsers.has(topic_id)) {
    typingUsers.set(topic_id, new Set());
  }
  
  if (is_typing) {
    typingUsers.get(topic_id).add(user_id);
  } else {
    typingUsers.get(topic_id).delete(user_id);
  }
  
  // Update UI
  updateTypingIndicator(topic_id, Array.from(typingUsers.get(topic_id)));
});

// Display typing indicator
function updateTypingIndicator(topicId, userIds) {
  const indicator = document.getElementById(`typing-${topicId}`);
  
  if (userIds.length === 0) {
    indicator.textContent = '';
  } else if (userIds.length === 1) {
    indicator.textContent = `${getUserName(userIds[0])} is typing...`;
  } else if (userIds.length === 2) {
    indicator.textContent = `${getUserName(userIds[0])} and ${getUserName(userIds[1])} are typing...`;
  } else {
    indicator.textContent = `${userIds.length} people are typing...`;
  }
}
```

## Mentions

### Handle Mention Notifications

```javascript
socket.on('mentioned', (data) => {
  const { topic_id, message_id, mentioned_by } = data;
  
  // Show notification
  showNotification({
    title: 'You were mentioned',
    body: `${getUserName(mentioned_by)} mentioned you in a message`,
    onClick: () => {
      navigateToMessage(topic_id, message_id);
    }
  });
  
  // Update unread mentions count
  incrementMentionCount(topic_id);
});
```

### Parse Mentions in UI

```javascript
function renderMessageWithMentions(content) {
  // Replace @mentions with clickable elements
  return content.replace(
    /@(\w+)|@"([^"]+)"/g,
    (match, username, fullname) => {
      const name = username || fullname;
      const userId = getUserIdByName(name);
      return `<span class="mention" data-user-id="${userId}">@${name}</span>`;
    }
  );
}
```

### Mention Autocomplete

```javascript
function setupMentionAutocomplete(inputElement, topicId) {
  let autocompleteList = null;
  
  inputElement.addEventListener('input', async (e) => {
    const cursorPos = e.target.selectionStart;
    const textBeforeCursor = e.target.value.substring(0, cursorPos);
    const mentionMatch = textBeforeCursor.match(/@(\w*)$/);
    
    if (mentionMatch) {
      const query = mentionMatch[1];
      
      // Fetch topic members
      const members = await fetchTopicMembers(topicId);
      
      // Filter by query
      const matches = members.filter(m => 
        m.user_email.toLowerCase().includes(query.toLowerCase()) ||
        (m.user_full_name && m.user_full_name.toLowerCase().includes(query.toLowerCase()))
      );
      
      // Show autocomplete dropdown
      showAutocomplete(matches, (selectedUser) => {
        const beforeMention = textBeforeCursor.substring(0, mentionMatch.index);
        const afterCursor = e.target.value.substring(cursorPos);
        const mention = selectedUser.user_full_name 
          ? `@"${selectedUser.user_full_name}"` 
          : `@${selectedUser.user_email}`;
        
        e.target.value = beforeMention + mention + ' ' + afterCursor;
        e.target.focus();
      });
    } else {
      hideAutocomplete();
    }
  });
}
```

## Reactions

### Add Reaction

```javascript
async function addReaction(messageId, emoji) {
  const response = await fetch(`/api/channels/topics/messages/${messageId}/reactions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ emoji })
  });
  
  // Real-time update will come via Socket.IO
}

socket.on('reaction_added', (data) => {
  const { message_id, user_id, emoji } = data;
  
  // Update reaction count in UI
  addReactionToMessage(message_id, emoji, user_id);
});
```

### Remove Reaction

```javascript
async function removeReaction(messageId, emoji) {
  const encodedEmoji = encodeURIComponent(emoji);
  await fetch(`/api/channels/topics/messages/${messageId}/reactions/${encodedEmoji}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
}

socket.on('reaction_removed', (data) => {
  const { message_id, user_id, emoji } = data;
  
  // Update reaction count in UI
  removeReactionFromMessage(message_id, emoji, user_id);
});
```

### Reaction Picker UI

```javascript
function showReactionPicker(messageId) {
  const commonEmojis = ['👍', '❤️', '😂', '😮', '😢', '🎉', '🚀', '👀'];
  
  const picker = document.createElement('div');
  picker.className = 'reaction-picker';
  
  commonEmojis.forEach(emoji => {
    const button = document.createElement('button');
    button.textContent = emoji;
    button.onclick = () => {
      addReaction(messageId, emoji);
      picker.remove();
    };
    picker.appendChild(button);
  });
  
  // Position near message
  const messageElement = document.getElementById(`message-${messageId}`);
  messageElement.appendChild(picker);
}
```

## Topic Updates

### Listen for Topic Changes

```javascript
socket.on('topic_created', (data) => {
  const { topic_id, channel_id, name, created_by } = data;
  
  // Add new topic to channel list
  addTopicToChannel(channel_id, {
    id: topic_id,
    name: name,
    created_by: created_by
  });
});

socket.on('topic_updated', (data) => {
  const { topic_id, updated_by } = data;
  
  // Refresh topic details
  refreshTopicDetails(topic_id);
});

socket.on('member_added', (data) => {
  const { topic_id, user_id, added_by } = data;
  
  // Update member list
  addMemberToTopic(topic_id, user_id);
  
  // If it's current user, show notification
  if (user_id === currentUserId) {
    showNotification({
      title: 'Added to Topic',
      body: `You were added to a topic by ${getUserName(added_by)}`
    });
  }
});

socket.on('member_removed', (data) => {
  const { topic_id, user_id, removed_by } = data;
  
  // Update member list
  removeMemberFromTopic(topic_id, user_id);
  
  // If it's current user, navigate away
  if (user_id === currentUserId) {
    navigateAwayFromTopic(topic_id);
    showNotification({
      title: 'Removed from Topic',
      body: 'You were removed from a topic'
    });
  }
});
```

## Complete React Example

```javascript
import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';

function TopicChat({ topicId, currentUserId, token }) {
  const [socket, setSocket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [typingUsers, setTypingUsers] = useState([]);
  const [messageInput, setMessageInput] = useState('');

  useEffect(() => {
    // Initialize socket
    const newSocket = io('http://localhost:8000', {
      path: '/socket.io',
      auth: { token }
    });

    newSocket.on('connect', () => {
      // Join topic
      newSocket.emit('join_topic', { topic_id: topicId });
    });

    newSocket.on('new_topic_message', (data) => {
      if (data.topic_id === topicId) {
        setMessages(prev => [...prev, data.message]);
      }
    });

    newSocket.on('user_typing_topic', (data) => {
      if (data.topic_id === topicId && data.user_id !== currentUserId) {
        setTypingUsers(prev => {
          if (data.is_typing) {
            return [...prev, data.user_id];
          } else {
            return prev.filter(id => id !== data.user_id);
          }
        });
      }
    });

    newSocket.on('mentioned', (data) => {
      if (data.topic_id === topicId) {
        // Show mention notification
        alert(`You were mentioned by ${data.mentioned_by}`);
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.emit('leave_topic', { topic_id: topicId });
      newSocket.disconnect();
    };
  }, [topicId, token, currentUserId]);

  const sendMessage = async () => {
    if (!messageInput.trim()) return;

    await fetch('/api/channels/topics/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        topic_id: topicId,
        content: messageInput,
        mentioned_user_ids: [] // Extract from content
      })
    });

    setMessageInput('');
  };

  const handleTyping = () => {
    if (socket) {
      socket.emit('topic_typing', {
        topic_id: topicId,
        is_typing: true
      });

      // Stop typing after 3 seconds
      setTimeout(() => {
        socket.emit('topic_typing', {
          topic_id: topicId,
          is_typing: false
        });
      }, 3000);
    }
  };

  return (
    <div className="topic-chat">
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className="message">
            <strong>{msg.sender_id}:</strong> {msg.content}
          </div>
        ))}
      </div>
      
      {typingUsers.length > 0 && (
        <div className="typing-indicator">
          {typingUsers.length} user(s) typing...
        </div>
      )}
      
      <div className="input-area">
        <input
          value={messageInput}
          onChange={(e) => {
            setMessageInput(e.target.value);
            handleTyping();
          }}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type a message... Use @username to mention"
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default TopicChat;
```

## Error Handling

```javascript
socket.on('error', (error) => {
  console.error('Socket.IO error:', error);
  
  if (error.message === 'Not authenticated') {
    // Redirect to login
    window.location.href = '/login';
  } else if (error.message.includes('not a member')) {
    // Show access denied message
    showError('You do not have access to this topic');
  }
});

// Handle disconnections
socket.on('disconnect', (reason) => {
  if (reason === 'io server disconnect') {
    // Server disconnected, try to reconnect
    socket.connect();
  }
  // else the socket will automatically try to reconnect
});

// Reconnection events
socket.on('reconnect', (attemptNumber) => {
  console.log('Reconnected after', attemptNumber, 'attempts');
  // Rejoin all topics
  rejoinAllTopics();
});

socket.on('reconnect_error', (error) => {
  console.error('Reconnection error:', error);
});
```

## Best Practices

1. **Always clean up**: Disconnect socket and leave rooms on component unmount
2. **Debounce typing indicators**: Don't send too many typing events
3. **Handle reconnections**: Rejoin topics after reconnection
4. **Validate user permissions**: Check if user can perform actions before attempting
5. **Optimize message rendering**: Use virtual scrolling for large message lists
6. **Cache user data**: Avoid repeated API calls for user names/avatars
7. **Handle offline mode**: Queue messages when offline, send when reconnected
8. **Use message IDs**: For deduplication and optimistic updates
