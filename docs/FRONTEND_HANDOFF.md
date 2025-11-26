# Frontend Team Handoff - Notifications Feature

## 🎯 Overview

The backend for **Global Alerts, Online Status & Offline Notifications** is complete and ready for frontend integration.

---

## 📚 Documentation You Need

### Primary Document
**`FRONTEND_IMPLEMENTATION_GUIDE.md`** - Your main reference
- Complete Socket.IO event documentation
- Web Push notification setup
- React implementation examples
- Code snippets and hooks
- Testing checklist

### Quick Reference
**`QUICK_SETUP_GUIDE.md`** - For quick lookups
- API endpoint reference
- Common troubleshooting
- Verification steps

---

## 🔑 What You Need from Backend

### 1. VAPID Public Key
Get it from this endpoint:
```bash
GET /api/notifications/vapid-public-key
```

Response:
```json
{
  "public_key": "BKxN..."
}
```

You'll need this for push notification subscriptions.

### 2. Socket.IO Server URL
```
ws://localhost:8000  (development)
wss://api.armadaden.com  (production)
```

### 3. Authentication
All Socket.IO connections require JWT token:
```javascript
const socket = io(SERVER_URL, {
  auth: { token: yourJWTToken }
});
```

---

## 🎨 Features to Implement

### 1. Online Status Indicators ⭐
**What:** Show green dot next to online users
**Socket Event:** `user_status_change`
**Payload:**
```typescript
{
  user_id: string;
  is_online: boolean;
  last_seen_at: string;
}
```

### 2. Unread Message Badges ⭐
**What:** Show unread count on topic list items
**Socket Event:** `new_message` (increment), `mark_as_read` (reset)
**API:** Fetch initial counts from backend

### 3. Global Notification Toast ⭐
**What:** Show toast notification for any new message
**Socket Event:** `global_message_alert`
**Payload:**
```typescript
{
  room_id: string;
  topic_id: string;
  sender_id: string;
  message_preview: string;
}
```

### 4. Push Notifications ⭐⭐
**What:** Browser notifications when app is closed
**Requires:**
- Service worker registration
- Notification permission request
- Push subscription via API

---

## 🔌 API Endpoints

### Get VAPID Public Key
```
GET /api/notifications/vapid-public-key
```

### Subscribe to Push
```
POST /api/notifications/subscribe
Body: {
  endpoint: string,
  p256dh: string,
  auth: string
}
```

### Unsubscribe
```
DELETE /api/notifications/unsubscribe/{subscription_id}
```

### List Subscriptions
```
GET /api/notifications/subscriptions
```

---

## 📡 Socket.IO Events

### Listen For (Server → Client)

```typescript
// User online/offline status
socket.on('user_status_change', (data) => {
  // Update user status in UI
});

// Global message alert
socket.on('global_message_alert', (data) => {
  // Show toast notification
});

// New message in room
socket.on('new_message', (data) => {
  // Update chat UI
});

// Messages marked as read
socket.on('messages_read', (data) => {
  // Update read receipts
});
```

### Emit (Client → Server)

```typescript
// Join a topic
socket.emit('join_topic', { topic_id: 'uuid' });

// Leave a topic
socket.emit('leave_topic', { topic_id: 'uuid' });

// Mark messages as read
socket.emit('mark_as_read', {
  room_id: 'uuid',
  topic_id: 'uuid',
  message_ids: ['uuid1', 'uuid2']
});
```

---

## 🚀 Quick Start Implementation

### Step 1: Socket.IO Connection
```typescript
import io from 'socket.io-client';

const socket = io('http://localhost:8000', {
  auth: { token: yourJWTToken }
});

socket.on('connected', (data) => {
  console.log('Connected:', data);
});
```

### Step 2: Listen for Status Changes
```typescript
const [onlineUsers, setOnlineUsers] = useState<Set<string>>(new Set());

socket.on('user_status_change', (data) => {
  setOnlineUsers(prev => {
    const newSet = new Set(prev);
    data.is_online ? newSet.add(data.user_id) : newSet.delete(data.user_id);
    return newSet;
  });
});
```

### Step 3: Show Online Status
```tsx
<div className="relative">
  <Avatar user={user} />
  {onlineUsers.has(user.id) && (
    <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full" />
  )}
</div>
```

### Step 4: Request Push Notifications
```typescript
// 1. Request permission
const permission = await Notification.requestPermission();

// 2. Get VAPID key
const { public_key } = await fetch('/api/notifications/vapid-public-key').then(r => r.json());

// 3. Subscribe
const registration = await navigator.serviceWorker.register('/sw.js');
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: urlBase64ToUint8Array(public_key)
});

// 4. Send to backend
await fetch('/api/notifications/subscribe', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    endpoint: subscription.endpoint,
    p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
    auth: arrayBufferToBase64(subscription.getKey('auth'))
  })
});
```

---

## 🧪 Testing Checklist

### Basic Functionality
- [ ] Socket.IO connects successfully
- [ ] Online status updates when users connect/disconnect
- [ ] Unread counts increment on new messages
- [ ] Unread counts reset when viewing topic
- [ ] Global alerts show for all messages

### Push Notifications
- [ ] Permission request appears
- [ ] Service worker registers
- [ ] Subscription created successfully
- [ ] Notifications received when browser closed
- [ ] Clicking notification opens correct topic

### Edge Cases
- [ ] Multiple tabs/windows sync correctly
- [ ] Reconnection after network loss
- [ ] Token expiration handling
- [ ] Subscription cleanup on logout

---

## 🐛 Common Issues & Solutions

### Issue: Socket.IO not connecting
**Solution:** Check JWT token is valid and CORS is configured

### Issue: Push notifications not working
**Solution:** 
1. Verify HTTPS (or localhost)
2. Check browser support
3. Ensure service worker is registered
4. Verify VAPID key is correct

### Issue: Online status not updating
**Solution:** Ensure `user_status_change` listener is registered before connection

### Issue: Unread counts incorrect
**Solution:** Emit `mark_as_read` when user views topic

---

## 📦 Required Frontend Dependencies

```json
{
  "socket.io-client": "^4.5.0"
}
```

---

## 🎨 UI/UX Recommendations

### Online Status
- Green dot for online
- Gray dot for offline
- Show "last seen" on hover

### Unread Badges
- Red badge with count
- Show "99+" for counts over 99
- Clear on topic view

### Notifications
- Toast in top-right corner
- 5-second auto-dismiss
- Click to navigate to topic

### Push Notifications
- Request permission after user interaction
- Show settings toggle in user menu
- Allow per-topic notification preferences (future)

---

## 📞 Questions?

### Backend Team Contact
- Check `IMPLEMENTATION_COMPLETE.md` for full details
- Review `FRONTEND_IMPLEMENTATION_GUIDE.md` for code examples
- Test API endpoints with Postman/curl

### Useful Commands
```bash
# Test VAPID endpoint
curl http://localhost:8000/api/notifications/vapid-public-key

# Test Socket.IO in browser console
const socket = io('http://localhost:8000', { auth: { token: 'YOUR_TOKEN' }});
socket.on('connected', console.log);
```

---

## ✅ Definition of Done

Frontend implementation is complete when:
- [ ] Online status indicators work in real-time
- [ ] Unread counts display and update correctly
- [ ] Global message alerts appear as toasts
- [ ] Push notifications work when browser is closed
- [ ] Service worker is registered and functional
- [ ] All Socket.IO events are handled
- [ ] Error states are handled gracefully
- [ ] UI is responsive and accessible

---

## 🎉 Ready to Start!

Everything you need is in `FRONTEND_IMPLEMENTATION_GUIDE.md`. Start there, and refer back to this document for quick lookups.

**Good luck! 🚀**
