"""clear_old_web_push_subscriptions

Revision ID: 1c7345284f00
Revises: 3d35f70cf39b
Create Date: 2025-11-28 16:31:50.141351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c7345284f00'
down_revision: Union[str, Sequence[str], None] = '3d35f70cf39b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Delete all old Web Push subscriptions (those with HTTP/HTTPS endpoints)
    # FCM tokens don't start with http, so this preserves any FCM subscriptions
    op.execute("""
        DELETE FROM push_subscriptions 
        WHERE endpoint LIKE 'http%'
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # No downgrade - we can't restore deleted subscriptions
    # Users will need to re-subscribe
    pass
