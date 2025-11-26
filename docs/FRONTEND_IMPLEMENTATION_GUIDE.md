# Frontend Implementation Guide: Global Alerts, Online Status & Offline Notifications

This guide provides comprehensive instructions for implementing the frontend features to work with the backend's global alerts, online status tracking, and offline push notifications.

---

## Table of Contents

1. [Overview](#overview)
2. [Socket.IO Events](#socketio-events)
3. [Online Status Tracking](#online-status-tracking)
4. [Unread Count Management](#unread-count-management)
5. [Web Push Notifications](#web-push-notifications)
6. [API Endpoints](#api-endpoints)
7. [Implementation Examples](#implementation-examples)

---

## Overview

The backend now supports:
- **Real-time online/offline status** for all users
- **Unread message counts** per topic
- **Global message alerts** broadcast to all connected users
- **Web Push notifications** for offline users

---

## Socket.IO Events

### Events to Listen For

#### 1. `user_status_change`
Broadcast when a user connects or disconnects.

**Payload:**
```typescript
{
  user_id: string;
  is_online: boolean;
  last_seen_at: string; // ISO 8601 timestamp
}
```

**Usage:**
```typescript
socket.on('user_status_change', (data) => {
  console.log(`User ${data.user_id} is now ${data.is_online ? 'online' : 'offline'}`);
  // Update UI to show online/offline status
  updateUserStatus(data.user_id, data.is_online, data.last_seen_at);
});
```

---

#### 2. `global_message_alert`
Broadcast to all users when a new message is sent (for global notification badges).

**Payload:**
```typescript
{
  room_id: string;
  topic_id: string | null;
  sender_id: string;
  message_preview: string; // First 100 characters
}
```

**Usage:**
```typescript
socket.on('global_message_alert', (data) => {
  console.log(`New message in topic ${data.topic_id} from ${data.sender_id}`);
  // Show notification badge or toast
  showGlobalNotification(data);
});
```

---

#### 3. `new_message`
Broadcast to all users in a specific room/topic.

**Payload:**
```typescript
{
  room_id: string;
  message: {
    id: string;
    content: string;
    sender_id: string;
    created_at: string;
    // ... other message fields
  }
}
```

---

#### 4. `messages_read`
Broadcast when a user marks messages as read.

**Payload:**
```typescript
{
  room_id: string;
  user_id: string;
  message_ids: string[];
}
```

---

### Events to Emit

#### 1. `join_topic`
Join a topic room to receive real-time updates.

**Payload:**
```typescript
{
  topic_id: string;
}
```

**Usage:**
```typescript
socket.emit('join_topic', { topic_id: 'topic-uuid-here' });
```

---

#### 2. `leave_topic`
Leave a topic room.

**Payload:**
```typescript
{
  topic_id: string;
}
```

---

#### 3. `send_message`
Send a message (after creating it via REST API).

**Payload:**
```typescript
{
  room_id: string;
  topic_id: string;
  message: {
    id: string;
    content: string;
    // ... other fields
  }
}
```

---

#### 4. `mark_as_read`
Mark messages as read and reset unread count.

**Payload:**
```typescript
{
  room_id: string;
  topic_id: string;
  message_ids: string[];
}
```

**Usage:**
```typescript
socket.emit('mark_as_read', {
  room_id: 'room-uuid',
  topic_id: 'topic-uuid',
  message_ids: ['msg-1', 'msg-2']
});
```

---

## Online Status Tracking

### Implementation Steps

1. **Listen for status changes:**
```typescript
import { useEffect, useState } from 'react';

const [onlineUsers, setOnlineUsers] = useState<Set<string>>(new Set());

useEffect(() => {
  socket.on('user_status_change', (data) => {
    setOnlineUsers(prev => {
      const newSet = new Set(prev);
      if (data.is_online) {
        newSet.add(data.user_id);
      } else {
        newSet.delete(data.user_id);
      }
      return newSet;
    });
  });

  return () => {
    socket.off('user_status_change');
  };
}, []);
```

2. **Display online status:**
```tsx
const UserAvatar = ({ userId, userName }) => {
  const isOnline = onlineUsers.has(userId);
  
  return (
    <div className="relative">
      <img src={`/avatars/${userId}`} alt={userName} />
      {isOnline && (
        <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
      )}
    </div>
  );
};
```

3. **Fetch initial online status:**
```typescript
// Get user details including online status from REST API
const fetchUserStatus = async (userId: string) => {
  const response = await fetch(`/api/users/${userId}`);
  const user = await response.json();
  return {
    is_online: user.is_online,
    last_seen_at: user.last_seen_at
  };
};
```

---

## Unread Count Management

### Implementation Steps

1. **Store unread counts per topic:**
```typescript
const [unreadCounts, setUnreadCounts] = useState<Record<string, number>>({});

// Fetch initial unread counts from API
useEffect(() => {
  const fetchUnreadCounts = async () => {
    const response = await fetch('/api/topics/unread-counts', {
      headers: { Authorization: `Bearer ${token}` }
    });
    const counts = await response.json();
    setUnreadCounts(counts);
  };
  
  fetchUnreadCounts();
}, []);
```

2. **Update unread count on new messages:**
```typescript
useEffect(() => {
  socket.on('new_message', (data) => {
    // Only increment if not in the active topic
    if (data.room_id !== activeTopicId) {
      setUnreadCounts(prev => ({
        ...prev,
        [data.room_id]: (prev[data.room_id] || 0) + 1
      }));
    }
  });

  return () => {
    socket.off('new_message');
  };
}, [activeTopicId]);
```

3. **Reset unread count when viewing topic:**
```typescript
const markTopicAsRead = async (topicId: string) => {
  // Emit Socket.IO event
  socket.emit('mark_as_read', {
    room_id: topicId,
    topic_id: topicId,
    message_ids: [] // Can be empty to reset all
  });
  
  // Update local state
  setUnreadCounts(prev => ({
    ...prev,
    [topicId]: 0
  }));
};
```

4. **Display unread badge:**
```tsx
const TopicListItem = ({ topic }) => {
  const unreadCount = unreadCounts[topic.id] || 0;
  
  return (
    <div className="flex items-center justify-between">
      <span>{topic.name}</span>
      {unreadCount > 0 && (
        <span className="bg-red-500 text-white rounded-full px-2 py-1 text-xs">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </div>
  );
};
```

---

## Web Push Notifications

### Setup Steps

#### 1. Request Notification Permission
```typescript
const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    console.log('This browser does not support notifications');
    return false;
  }

  const permission = await Notification.requestPermission();
  return permission === 'granted';
};
```

#### 2. Get VAPID Public Key
```typescript
const getVapidPublicKey = async () => {
  const response = await fetch('/api/notifications/vapid-public-key');
  const data = await response.json();
  return data.public_key;
};
```

#### 3. Register Service Worker
```typescript
// In your main app file or service worker registration
const registerServiceWorker = async () => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      console.log('Service Worker registered:', registration);
      return registration;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return null;
    }
  }
};
```

#### 4. Subscribe to Push Notifications
```typescript
const subscribeToPushNotifications = async () => {
  // 1. Request permission
  const hasPermission = await requestNotificationPermission();
  if (!hasPermission) {
    console.log('Notification permission denied');
    return;
  }

  // 2. Register service worker
  const registration = await registerServiceWorker();
  if (!registration) return;

  // 3. Get VAPID public key
  const vapidPublicKey = await getVapidPublicKey();

  // 4. Convert VAPID key to Uint8Array
  const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);

  // 5. Subscribe to push
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: convertedVapidKey
  });

  // 6. Send subscription to backend
  await fetch('/api/notifications/subscribe', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      endpoint: subscription.endpoint,
      p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
      auth: arrayBufferToBase64(subscription.getKey('auth'))
    })
  });

  console.log('Push notification subscription successful');
};

// Helper functions
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function arrayBufferToBase64(buffer: ArrayBuffer | null): string {
  if (!buffer) return '';
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}
```

#### 5. Service Worker (sw.js)
```javascript
// sw.js - Place in public folder
self.addEventListener('push', (event) => {
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: data.icon || '/icon-192x192.png',
    badge: data.badge || '/badge-72x72.png',
    tag: data.tag || 'default',
    data: data.data,
    requireInteraction: false,
    vibrate: [200, 100, 200]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const data = event.notification.data;
  
  // Navigate to the topic when notification is clicked
  if (data.topic_id) {
    event.waitUntil(
      clients.openWindow(`/topics/${data.topic_id}`)
    );
  }
});
```

#### 6. Unsubscribe from Push Notifications
```typescript
const unsubscribeFromPush = async () => {
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();
  
  if (subscription) {
    // Unsubscribe from browser
    await subscription.unsubscribe();
    
    // Remove from backend
    await fetch('/api/notifications/unsubscribe-by-endpoint', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint
      })
    });
    
    console.log('Unsubscribed from push notifications');
  }
};
```

---

## API Endpoints

### Notification Endpoints

#### `GET /api/notifications/vapid-public-key`
Get the VAPID public key for push subscriptions.

**Response:**
```json
{
  "public_key": "BG3xPz..."
}
```

---

#### `POST /api/notifications/subscribe`
Subscribe to push notifications.

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "p256dh": "BKxN...",
  "auth": "dGVz..."
}
```

**Response:**
```json
{
  "id": "subscription-uuid",
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

#### `DELETE /api/notifications/unsubscribe/{subscription_id}`
Unsubscribe by subscription ID.

**Response:** 204 No Content

---

#### `DELETE /api/notifications/unsubscribe-by-endpoint`
Unsubscribe by endpoint URL.

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

**Response:** 204 No Content

---

#### `GET /api/notifications/subscriptions`
Get all push subscriptions for the current user.

**Response:**
```json
[
  {
    "id": "subscription-uuid",
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## Implementation Examples

### Complete React Hook for Notifications

```typescript
import { useEffect, useState } from 'react';
import { useAuth } from './useAuth'; // Your auth hook
import { useSocket } from './useSocket'; // Your socket hook

export const useNotifications = () => {
  const { token } = useAuth();
  const socket = useSocket();
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState<Set<string>>(new Set());
  const [unreadCounts, setUnreadCounts] = useState<Record<string, number>>({});

  // Setup push notifications
  useEffect(() => {
    const setupPush = async () => {
      if (!token) return;
      
      const hasPermission = await requestNotificationPermission();
      if (hasPermission) {
        await subscribeToPushNotifications();
        setIsSubscribed(true);
      }
    };

    setupPush();
  }, [token]);

  // Listen for online status changes
  useEffect(() => {
    if (!socket) return;

    socket.on('user_status_change', (data) => {
      setOnlineUsers(prev => {
        const newSet = new Set(prev);
        if (data.is_online) {
          newSet.add(data.user_id);
        } else {
          newSet.delete(data.user_id);
        }
        return newSet;
      });
    });

    return () => {
      socket.off('user_status_change');
    };
  }, [socket]);

  // Listen for global message alerts
  useEffect(() => {
    if (!socket) return;

    socket.on('global_message_alert', (data) => {
      // Show in-app notification
      showToast(`New message from ${data.sender_id}`, data.message_preview);
    });

    return () => {
      socket.off('global_message_alert');
    };
  }, [socket]);

  // Mark topic as read
  const markAsRead = (topicId: string) => {
    if (!socket) return;
    
    socket.emit('mark_as_read', {
      room_id: topicId,
      topic_id: topicId,
      message_ids: []
    });

    setUnreadCounts(prev => ({
      ...prev,
      [topicId]: 0
    }));
  };

  return {
    isSubscribed,
    onlineUsers,
    unreadCounts,
    markAsRead
  };
};
```

---

## Testing Checklist

- [ ] User online status updates in real-time when connecting/disconnecting
- [ ] Unread counts increment when receiving messages in inactive topics
- [ ] Unread counts reset when viewing a topic
- [ ] Global message alerts appear for all users
- [ ] Push notifications work when browser is closed
- [ ] Push notifications navigate to correct topic when clicked
- [ ] Service worker registers successfully
- [ ] VAPID public key is retrieved correctly
- [ ] Subscription persists across browser sessions
- [ ] Unsubscribe removes subscription from backend

---

## Troubleshooting

### Push Notifications Not Working

1. **Check VAPID keys are configured:**
   - Ensure `VAPID_PRIVATE_KEY` and `VAPID_PUBLIC_KEY` are set in `.env`
   - Generate keys using: `npx web-push generate-vapid-keys`

2. **Check browser support:**
   - Push notifications require HTTPS (except localhost)
   - Not all browsers support push notifications

3. **Check service worker:**
   - Verify service worker is registered: `navigator.serviceWorker.controller`
   - Check browser console for service worker errors

4. **Check permissions:**
   - Verify notification permission: `Notification.permission`
   - Re-request permission if denied

### Online Status Not Updating

1. **Check Socket.IO connection:**
   - Verify socket is connected: `socket.connected`
   - Check authentication token is valid

2. **Check event listeners:**
   - Ensure `user_status_change` listener is registered
   - Check for duplicate listeners

### Unread Counts Incorrect

1. **Check topic membership:**
   - Verify user is a member of the topic
   - Check `last_read_at` timestamp

2. **Check mark_as_read event:**
   - Verify event is emitted when viewing topic
   - Check backend logs for event processing

---

## Additional Resources

- [Web Push API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Socket.IO Client Documentation](https://socket.io/docs/v4/client-api/)
- [VAPID Specification](https://tools.ietf.org/html/rfc8292)

---

## Support

For questions or issues, please contact the backend team or create an issue in the repository.
