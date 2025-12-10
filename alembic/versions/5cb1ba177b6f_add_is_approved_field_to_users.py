"""add_is_approved_field_to_users

Revision ID: 5cb1ba177b6f
Revises: 3356464281d5
Create Date: 2025-12-10 16:23:46.161794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cb1ba177b6f'
down_revision: Union[str, Sequence[str], None] = '3356464281d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_approved column with default False
    op.add_column('users', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'))
    
    # Set existing users to approved=True to maintain current functionality
    op.execute("UPDATE users SET is_approved = true WHERE is_bot = false")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_approved column
    op.drop_column('users', 'is_approved')
