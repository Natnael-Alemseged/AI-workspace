# Quick Setup Guide - Notifications Feature

## 🚀 Quick Start (5 Minutes)

Follow these steps to get the notifications feature up and running:

### Step 1: Generate VAPID Keys (1 minute)

Run the provided script:

```bash
python scripts/generate_vapid_keys.py
```

This will output something like:
```
VAPID_PRIVATE_KEY=BG3xPz...
VAPID_PUBLIC_KEY=BKxN...
```

### Step 2: Update .env File (1 minute)

Add the generated keys to your `.env` file:

```env
# Web Push Notification Configuration
VAPID_PRIVATE_KEY=<paste_private_key_here>
VAPID_PUBLIC_KEY=<paste_public_key_here>
VAPID_SUBJECT=mailto:admin@armadaden.com
```

### Step 3: Install Dependencies (1 minute)

If not already installed:

```bash
pip install pywebpush
```

### Step 4: Verify Migration (1 minute)

Check that the database migration was applied:

```bash
alembic current
```

You should see: `3d35f70cf39b (head)`

If not, run:
```bash
alembic upgrade head
```

### Step 5: Restart Server (1 minute)

Restart your FastAPI server:

```bash
uvicorn app.main:app --reload
```

## ✅ Verification

### Test the API Endpoints

1. **Get VAPID Public Key:**
```bash
curl http://localhost:8000/api/notifications/vapid-public-key
```

Expected response:
```json
{
  "public_key": "BKxN..."
}
```

2. **Test Socket.IO Connection:**
```javascript
// In browser console
const socket = io('http://localhost:8000', {
  auth: { token: 'your_jwt_token' }
});

socket.on('connected', (data) => {
  console.log('Connected:', data);
});

socket.on('user_status_change', (data) => {
  console.log('User status changed:', data);
});
```

### Check Database Tables

Verify the new columns exist:

```sql
-- Check users table
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('is_online', 'last_seen_at');

-- Check topic_members table
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'topic_members' 
AND column_name = 'unread_count';

-- Check push_subscriptions table
SELECT * FROM push_subscriptions LIMIT 1;
```

## 🎯 What's Working Now

After setup, you should have:

- ✅ Real-time online/offline status tracking
- ✅ Unread message counts per topic
- ✅ Global message alerts to all users
- ✅ Web Push notification infrastructure
- ✅ API endpoints for push subscription management

## 📝 Next Steps

1. **Share with Frontend Team:**
   - Send them `docs/FRONTEND_IMPLEMENTATION_GUIDE.md`
   - Provide the VAPID public key
   - Share API endpoint documentation

2. **Test End-to-End:**
   - Connect multiple clients
   - Send messages and verify notifications
   - Test push notifications with browser closed

3. **Monitor Logs:**
   - Check for any Socket.IO connection errors
   - Verify push notification delivery
   - Monitor database for subscription growth

## 🐛 Troubleshooting

### Issue: "Push notifications are not configured"

**Solution:** Verify VAPID keys are in `.env` and server was restarted.

### Issue: Migration fails with "column already exists"

**Solution:** The migration was already applied. Run `alembic current` to verify.

### Issue: Socket.IO not connecting

**Solution:** 
1. Check JWT token is valid
2. Verify CORS settings in `socketio_service.py`
3. Check browser console for errors

### Issue: Push notifications not received

**Solution:**
1. Verify VAPID keys are correct
2. Check browser supports push notifications
3. Ensure HTTPS is enabled (or using localhost)
4. Check service worker is registered

## 📚 Full Documentation

For complete implementation details, see:
- `docs/NOTIFICATIONS_IMPLEMENTATION_SUMMARY.md` - Backend implementation details
- `docs/FRONTEND_IMPLEMENTATION_GUIDE.md` - Frontend integration guide

## 🆘 Need Help?

1. Check the troubleshooting section above
2. Review server logs for errors
3. Verify all environment variables are set
4. Test with curl/Postman to isolate issues
