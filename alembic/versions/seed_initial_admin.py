"""seed initial admin user

Revision ID: seed_initial_admin
Revises: add_channels_topics_system
Create Date: 2024-11-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'seed_initial_admin'
down_revision = 'add_channels_topics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Seed an initial admin user.
    
    IMPORTANT: Change the email and password hash before running this migration!
    To generate a password hash, run:
    
    from app.core.security import get_password_hash
    print(get_password_hash("your_password"))
    """
    
    # Define the users table structure
    users_table = table(
        'users',
        column('id', String),
        column('email', String),
        column('hashed_password', String),
        column('full_name', String),
        column('role', String),
        column('is_active', sa.Boolean),
        column('is_superuser', sa.Boolean),
        column('is_verified', sa.Boolean),
    )
    
    # Check if admin already exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM users WHERE email = :email"),
        {"email": "admin@armadaden.com"}
    ).scalar()
    
    if result > 0:
        print("⚠️  Admin user already exists, skipping seed.")
        return
    
    # IMPORTANT: Replace this with your actual hashed password!
    # Generate with: from app.core.security import get_password_hash; print(get_password_hash("your_password"))
    hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNk8L6T3u"  # This is "Admin@123"
    
    # Insert admin user
    op.bulk_insert(
        users_table,
        [
            {
                'id': str(uuid.uuid4()),
                'email': 'admin@armadaden.com',
                'hashed_password': hashed_password,
                'full_name': 'System Administrator',
                'role': 'admin',
                'is_active': True,
                'is_superuser': True,
                'is_verified': True,
            }
        ]
    )
    
    print("✅ Initial admin user created: admin@armadaden.com")
    print("⚠️  IMPORTANT: Change the default password immediately!")


def downgrade() -> None:
    """Remove the seeded admin user."""
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM users WHERE email = :email"),
        {"email": "admin@armadaden.com"}
    )
    print("🗑️  Removed seeded admin user")
