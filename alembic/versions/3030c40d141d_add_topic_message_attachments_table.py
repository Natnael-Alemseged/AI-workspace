"""add_topic_message_attachments_table

Revision ID: 3030c40d141d
Revises: 7a358eb65b44
Create Date: 2025-11-28 18:23:33.062187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3030c40d141d'
down_revision: Union[str, Sequence[str], None] = '7a358eb65b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create topic_message_attachments table for multiple file support."""
    # Create attachments table
    op.create_table(
        'topic_message_attachments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['topic_messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topic_message_attachments_message_id'), 'topic_message_attachments', ['message_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove attachments table."""
    op.drop_index(op.f('ix_topic_message_attachments_message_id'), table_name='topic_message_attachments')
    op.drop_table('topic_message_attachments')
