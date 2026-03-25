"""add sent_at to alert_delivery_logs

Revision ID: d4c4d2a6ed80
Revises: 3f58ceca9491
Create Date: 2026-03-21 23:18:46.122964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4c4d2a6ed80'
down_revision: Union[str, Sequence[str], None] = '3f58ceca9491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
