"""make_hashed_password_nullable_for_oauth

Revision ID: d949d1629252
Revises: 4166023639f2
Create Date: 2025-11-10 06:46:22.006863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd949d1629252'
down_revision: Union[str, Sequence[str], None] = '4166023639f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite doesn't support ALTER COLUMN DROP NOT NULL
    # We need to recreate the table with the new schema
    # First, create a temporary table with the new schema
    op.execute("""
        CREATE TABLE users_temp (
            id VARCHAR NOT NULL,
            email VARCHAR NOT NULL,
            full_name VARCHAR,
            hashed_password VARCHAR,  -- Now nullable
            is_active BOOLEAN NOT NULL,
            is_superuser BOOLEAN NOT NULL,
            is_verified BOOLEAN NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (email)
        )
    """)

    # Copy data from old table to new table
    op.execute("""
        INSERT INTO users_temp (id, email, full_name, hashed_password, is_active, is_superuser, is_verified, created_at, updated_at)
        SELECT id, email, full_name, hashed_password, is_active, is_superuser, is_verified, created_at, updated_at
        FROM users
    """)

    # Drop old table
    op.drop_table('users')

    # Rename new table to users
    op.execute("ALTER TABLE users_temp RENAME TO users")

    # Recreate indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_created_at', 'users', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite doesn't support ALTER COLUMN ADD NOT NULL
    # We need to recreate the table with the old schema
    # First, create a temporary table with the old schema
    op.execute("""
        CREATE TABLE users_temp (
            id VARCHAR NOT NULL,
            email VARCHAR NOT NULL,
            full_name VARCHAR,
            hashed_password VARCHAR NOT NULL,  -- Back to non-nullable
            is_active BOOLEAN NOT NULL,
            is_superuser BOOLEAN NOT NULL,
            is_verified BOOLEAN NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (email)
        )
    """)

    # Copy data from old table to new table (only users with passwords)
    op.execute("""
        INSERT INTO users_temp (id, email, full_name, hashed_password, is_active, is_superuser, is_verified, created_at, updated_at)
        SELECT id, email, full_name, hashed_password, is_active, is_superuser, is_verified, created_at, updated_at
        FROM users
        WHERE hashed_password IS NOT NULL
    """)

    # Drop old table
    op.drop_table('users')

    # Rename new table to users
    op.execute("ALTER TABLE users_temp RENAME TO users")

    # Recreate indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_created_at', 'users', ['created_at'], unique=False)
