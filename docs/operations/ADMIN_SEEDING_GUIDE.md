# Admin User Seeding Guide

Since the system requires at least one admin user to create channels and topics, you need to seed an initial admin user into the database. Here are three methods to do this:

---

## Method 1: Python Seeding Script (Recommended) ⭐

This is the **easiest and safest** method with an interactive menu.

### Step 1: Run the Script

```bash
# Make sure you're in the project directory with venv activated
python seed_admin.py
```

### Step 2: Choose an Option

```
🌱 Admin User Management
====================================
1. Create new admin user (interactive)
2. Promote existing user to admin
3. List all admin users
4. Seed predefined admins
5. Exit

Select an option (1-5):
```

### Option 1: Create New Admin (Interactive)

```bash
Select an option: 1

Enter admin email: admin@yourcompany.com
Enter full name (optional): John Admin
Enter password: ********
Confirm password: ********

✅ Admin user created successfully!
   Email: admin@yourcompany.com
   Role: admin
   ID: 550e8400-e29b-41d4-a716-446655440000
```

### Option 2: Promote Existing User

If you already have a regular user account:

```bash
Select an option: 2

Enter user email to promote: john@yourcompany.com

✅ User john@yourcompany.com promoted to admin!
   ID: 550e8400-e29b-41d4-a716-446655440000
   Role: admin
```

### Option 3: List All Admins

```bash
Select an option: 3

👥 Current Admin Users
====================================

📧 admin@yourcompany.com
   Name: John Admin
   ID: 550e8400-e29b-41d4-a716-446655440000
   Superuser: True
   Verified: True
```

### Option 4: Seed Predefined Admins

Edit `seed_admin.py` first to add your admin details:

```python
async def seed_multiple_admins():
    """Seed multiple predefined admin users."""
    admins = [
        {
            "email": "admin@armadaden.com",
            "password": "YourSecurePassword123!",  # Change this!
            "full_name": "System Administrator"
        },
        {
            "email": "admin2@armadaden.com",
            "password": "AnotherSecurePassword456!",
            "full_name": "Secondary Admin"
        },
    ]
    # ...
```

Then run:
```bash
Select an option: 4
```

---

## Method 2: Alembic Data Migration

This method seeds the admin during database migration.

### Step 1: Edit the Migration File

Open `alembic/versions/seed_initial_admin.py` and update:

```python
# Change the email
'email': 'your-admin@yourcompany.com',

# Generate a password hash
# In Python:
from app.core.security import get_password_hash
print(get_password_hash("YourSecurePassword"))
# Copy the output and replace hashed_password

'hashed_password': 'YOUR_GENERATED_HASH_HERE',
'full_name': 'Your Name',
```

### Step 2: Run the Migration

```bash
alembic upgrade head
```

Output:
```
INFO  [alembic.runtime.migration] Running upgrade add_channels_topics_system -> seed_initial_admin
✅ Initial admin user created: your-admin@yourcompany.com
⚠️  IMPORTANT: Change the default password immediately!
```

### Step 3: Verify

```bash
# Connect to your database
psql -U your_username -d armada_den

# Check admin users
SELECT email, role, is_superuser FROM users WHERE role = 'admin';
```

---

## Method 3: Direct SQL Script

Quick method if you prefer SQL.

### Step 1: Generate Password Hash

First, generate a password hash in Python:

```bash
python -c "from app.core.security import get_password_hash; print(get_password_hash('YourPassword123'))"
```

Copy the output (starts with `$2b$12$...`)

### Step 2: Edit SQL Script

Open `seed_admin.sql` and replace:

```sql
'admin@armadaden.com',  -- Your email
'$2b$12$...',           -- Your generated hash
'System Administrator', -- Your name
```

### Step 3: Run SQL Script

```bash
# Method A: Using psql
psql -U your_username -d armada_den -f seed_admin.sql

# Method B: Using psql interactive
psql -U your_username -d armada_den
\i seed_admin.sql
```

Output:
```
NOTICE:  ✅ Admin user created: admin@armadaden.com
NOTICE:  ⚠️  Default password is: Admin@123
NOTICE:  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!
```

---

## Method 4: Using Python Console

Quick one-liner for development.

```bash
# Activate venv
.venv\Scripts\activate

# Start Python
python
```

```python
import asyncio
from app.db import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as session:
        admin = User(
            email="admin@test.com",
            hashed_password=get_password_hash("Admin@123"),
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
            is_verified=True
        )
        session.add(admin)
        await session.commit()
        print(f"✅ Admin created: {admin.email}")

asyncio.run(create_admin())
```

---

## Verification

After seeding, verify the admin user was created:

### Method 1: Using the Seeding Script

```bash
python seed_admin.py
# Select option 3 to list all admins
```

### Method 2: Using SQL

```sql
SELECT 
    email, 
    full_name, 
    role, 
    is_superuser, 
    is_verified 
FROM users 
WHERE role = 'admin';
```

### Method 3: Using the API

```bash
# Login with admin credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com",
    "password": "YourPassword123"
  }'

# You should receive an access_token
```

---

## Testing Admin Capabilities

Once your admin user is created, test the admin-only endpoints:

### 1. Get Access Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com",
    "password": "YourPassword123"
  }'
```

Save the `access_token` from the response.

### 2. Create a Channel (Admin Only)

```bash
curl -X POST http://localhost:8000/api/channels \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "General",
    "description": "General discussions",
    "icon": "💬",
    "color": "#3B82F6"
  }'
```

If successful, you'll get a channel object back. If you get "Only admins can create channels", the role wasn't set correctly.

### 3. Create a Topic (Admin Only)

```bash
curl -X POST http://localhost:8000/api/channels/topics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "channel_id": "CHANNEL_ID_FROM_STEP_2",
    "name": "Welcome",
    "description": "Welcome to the platform",
    "member_ids": []
  }'
```

---

## Security Best Practices

### 1. Change Default Passwords Immediately

If you used any default passwords in the seeding scripts:

```bash
# Use the API to change password
curl -X PATCH http://localhost:8000/api/users/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "password": "NewSecurePassword123!"
  }'
```

### 2. Use Strong Passwords

- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Avoid common words or patterns
- Use a password manager

### 3. Remove Seeding Scripts in Production

```bash
# After seeding, remove or secure these files:
rm seed_admin.py
rm seed_admin.sql
# Or move them to a secure location
```

### 4. Limit Admin Accounts

- Only create admin accounts for trusted users
- Use regular user accounts for day-to-day operations
- Audit admin actions regularly

### 5. Enable 2FA (Future Enhancement)

Consider implementing two-factor authentication for admin accounts.

---

## Troubleshooting

### Issue: "User already exists"

**Solution**: Use option 2 in the seeding script to promote the existing user to admin.

### Issue: "Only admins can create channels" after seeding

**Solution**: Verify the user's role in the database:

```sql
SELECT email, role, is_superuser FROM users WHERE email = 'your-email@example.com';
```

If role is NULL or 'user', update it:

```sql
UPDATE users 
SET role = 'admin', is_superuser = true, is_verified = true 
WHERE email = 'your-email@example.com';
```

### Issue: Password hash generation fails

**Solution**: Make sure you have bcrypt installed:

```bash
pip install bcrypt
# or
pip install passlib[bcrypt]
```

### Issue: "Module not found" when running seed_admin.py

**Solution**: Make sure you're in the project directory and venv is activated:

```bash
cd "d:\code projects\back end\armada den\armada-den"
.venv\Scripts\activate
python seed_admin.py
```

### Issue: Database connection error

**Solution**: Check your `.env` file has correct database credentials:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/armada_den
```

---

## Quick Reference

| Method | Difficulty | Use Case |
|--------|-----------|----------|
| Python Script | ⭐ Easy | Development, multiple admins |
| Alembic Migration | ⭐⭐ Medium | Automated deployment |
| SQL Script | ⭐⭐ Medium | Quick setup, database access |
| Python Console | ⭐⭐⭐ Advanced | One-off, debugging |

**Recommendation**: Use the **Python Seeding Script** (`seed_admin.py`) for the easiest experience.

---

## Next Steps

After seeding your admin user:

1. ✅ Login with admin credentials
2. ✅ Create your first channel
3. ✅ Create topics within the channel
4. ✅ Add regular users to topics
5. ✅ Test messaging, mentions, and reactions
6. ✅ Change the default password
7. ✅ Create additional admin users if needed

Happy coding! 🚀
