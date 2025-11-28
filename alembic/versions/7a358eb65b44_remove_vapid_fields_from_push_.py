"""remove_vapid_fields_from_push_subscriptions

Revision ID: 7a358eb65b44
Revises: 1c7345284f00
Create Date: 2025-11-28 17:26:59.981764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a358eb65b44'
down_revision: Union[str, Sequence[str], None] = '1c7345284f00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Remove VAPID fields (p256dh, auth) from push_subscriptions."""
    # Drop the p256dh and auth columns as we're migrating to FCM only
    op.drop_column('push_subscriptions', 'p256dh')
    op.drop_column('push_subscriptions', 'auth')


def downgrade() -> None:
    """Downgrade schema - Restore VAPID fields."""
    # Add back the columns if we need to rollback
    op.add_column('push_subscriptions', sa.Column('p256dh', sa.String(), nullable=True))
    op.add_column('push_subscriptions', sa.Column('auth', sa.String(), nullable=True))
