"""merge chat and admin branches

Revision ID: ad5888aad145
Revises: chat_tables_001, seed_initial_admin
Create Date: 2025-11-15 17:33:01.018125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad5888aad145'
down_revision: Union[str, Sequence[str], None] = ('chat_tables_001', 'seed_initial_admin')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
