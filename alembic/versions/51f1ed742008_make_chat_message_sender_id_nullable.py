"""make_chat_message_sender_id_nullable

Revision ID: 51f1ed742008
Revises: 6ac44120e7b8
Create Date: 2025-11-15 18:04:56.904876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51f1ed742008'
down_revision: Union[str, Sequence[str], None] = '6ac44120e7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make sender_id nullable to allow AI bot messages
    op.alter_column('chat_messages', 'sender_id',
                    existing_type=sa.UUID(),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make sender_id non-nullable again
    op.alter_column('chat_messages', 'sender_id',
                    existing_type=sa.UUID(),
                    nullable=False)
