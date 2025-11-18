-- Seed initial admin user
-- Run this SQL script directly in your PostgreSQL database

-- IMPORTANT: Replace the UUID, email, and hashed_password with your values
-- To generate a password hash, use Python:
-- from app.core.security import get_password_hash
-- print(get_password_hash("your_password"))

-- Check if admin already exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@armadaden.com') THEN
        -- Insert admin user
        INSERT INTO users (
            id,
            email,
            hashed_password,
            full_name,
            role,
            is_active,
            is_superuser,
            is_verified
        ) VALUES (
            gen_random_uuid(),  -- PostgreSQL 13+ has this built-in
            'admin@armadaden.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNk8L6T3u',  -- Password: Admin@123
            'System Administrator',
            'admin',
            true,
            true,
            true
        );
        
        RAISE NOTICE '✅ Admin user created: admin@armadaden.com';
        RAISE NOTICE '⚠️  Default password is: Admin@123';
        RAISE NOTICE '⚠️  CHANGE THIS PASSWORD IMMEDIATELY!';
    ELSE
        RAISE NOTICE '⚠️  Admin user already exists, skipping.';
    END IF;
END $$;

-- Verify the admin was created
SELECT 
    id,
    email,
    full_name,
    role,
    is_active,
    is_superuser,
    is_verified
FROM users 
WHERE role = 'admin';
