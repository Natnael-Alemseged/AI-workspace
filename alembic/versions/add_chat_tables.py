"""add chat tables

Revision ID: chat_tables_001
Revises: d949d1629252
Create Date: 2025-11-11 14:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'chat_tables_001'
down_revision: Union[str, None] = 'd949d1629252'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_rooms table
    op.create_table(
        'chat_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('room_type', sa.Enum('DIRECT', 'GROUP', name='chatroomtype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_rooms_created_at'), 'chat_rooms', ['created_at'], unique=False)
    
    # Create chat_room_members table
    op.create_table(
        'chat_room_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_room_members_room_id'), 'chat_room_members', ['room_id'], unique=False)
    op.create_index(op.f('ix_chat_room_members_user_id'), 'chat_room_members', ['user_id'], unique=False)
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_type', sa.Enum('TEXT', 'IMAGE', 'VIDEO', 'AUDIO', 'FILE', name='messagetype'), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('media_filename', sa.String(), nullable=True),
        sa.Column('media_size', sa.Integer(), nullable=True),
        sa.Column('media_mime_type', sa.String(), nullable=True),
        sa.Column('reply_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('forwarded_from_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['forwarded_from_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['reply_to_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_created_at'), 'chat_messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_chat_messages_forwarded_from_id'), 'chat_messages', ['forwarded_from_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_reply_to_id'), 'chat_messages', ['reply_to_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_room_id'), 'chat_messages', ['room_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_sender_id'), 'chat_messages', ['sender_id'], unique=False)
    
    # Create message_read_receipts table
    op.create_table(
        'message_read_receipts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_read_receipts_message_id'), 'message_read_receipts', ['message_id'], unique=False)
    op.create_index(op.f('ix_message_read_receipts_user_id'), 'message_read_receipts', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_message_read_receipts_user_id'), table_name='message_read_receipts')
    op.drop_index(op.f('ix_message_read_receipts_message_id'), table_name='message_read_receipts')
    op.drop_table('message_read_receipts')
    
    op.drop_index(op.f('ix_chat_messages_sender_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_room_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_reply_to_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_forwarded_from_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_created_at'), table_name='chat_messages')
    op.drop_table('chat_messages')
    
    op.drop_index(op.f('ix_chat_room_members_user_id'), table_name='chat_room_members')
    op.drop_index(op.f('ix_chat_room_members_room_id'), table_name='chat_room_members')
    op.drop_table('chat_room_members')
    
    op.drop_index(op.f('ix_chat_rooms_created_at'), table_name='chat_rooms')
    op.drop_table('chat_rooms')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS messagetype')
    op.execute('DROP TYPE IF EXISTS chatroomtype')
