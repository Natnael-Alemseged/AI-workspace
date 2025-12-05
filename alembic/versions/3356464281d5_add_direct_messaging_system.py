"""add_direct_messaging_system

Revision ID: 3356464281d5
Revises: 3030c40d141d
Create Date: 2025-12-04 19:53:55.043976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3356464281d5'
down_revision: Union[str, Sequence[str], None] = '3030c40d141d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add direct messaging system."""
    # Add is_bot field to users table
    op.add_column('users', sa.Column('is_bot', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create direct_messages table
    op.create_table(
        'direct_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('sender_id', sa.UUID(), nullable=False),
        sa.Column('receiver_id', sa.UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('reply_to_id', sa.UUID(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reply_to_id'], ['direct_messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_direct_messages_sender_id'), 'direct_messages', ['sender_id'], unique=False)
    op.create_index(op.f('ix_direct_messages_receiver_id'), 'direct_messages', ['receiver_id'], unique=False)
    op.create_index(op.f('ix_direct_messages_reply_to_id'), 'direct_messages', ['reply_to_id'], unique=False)
    op.create_index(op.f('ix_direct_messages_is_read'), 'direct_messages', ['is_read'], unique=False)
    op.create_index(op.f('ix_direct_messages_created_at'), 'direct_messages', ['created_at'], unique=False)
    
    # Create direct_message_reactions table
    op.create_table(
        'direct_message_reactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('emoji', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['direct_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_direct_message_reactions_message_id'), 'direct_message_reactions', ['message_id'], unique=False)
    op.create_index(op.f('ix_direct_message_reactions_user_id'), 'direct_message_reactions', ['user_id'], unique=False)
    
    # Create direct_message_attachments table
    op.create_table(
        'direct_message_attachments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['direct_messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_direct_message_attachments_message_id'), 'direct_message_attachments', ['message_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove direct messaging system."""
    # Drop direct_message_attachments table
    op.drop_index(op.f('ix_direct_message_attachments_message_id'), table_name='direct_message_attachments')
    op.drop_table('direct_message_attachments')
    
    # Drop direct_message_reactions table
    op.drop_index(op.f('ix_direct_message_reactions_user_id'), table_name='direct_message_reactions')
    op.drop_index(op.f('ix_direct_message_reactions_message_id'), table_name='direct_message_reactions')
    op.drop_table('direct_message_reactions')
    
    # Drop direct_messages table
    op.drop_index(op.f('ix_direct_messages_created_at'), table_name='direct_messages')
    op.drop_index(op.f('ix_direct_messages_is_read'), table_name='direct_messages')
    op.drop_index(op.f('ix_direct_messages_reply_to_id'), table_name='direct_messages')
    op.drop_index(op.f('ix_direct_messages_receiver_id'), table_name='direct_messages')
    op.drop_index(op.f('ix_direct_messages_sender_id'), table_name='direct_messages')
    op.drop_table('direct_messages')
    
    # Remove is_bot field from users table
    op.drop_column('users', 'is_bot')
