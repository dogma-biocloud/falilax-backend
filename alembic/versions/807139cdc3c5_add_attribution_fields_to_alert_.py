"""add attribution fields to alert_delivery_logs

Revision ID: 807139cdc3c5
Revises: d4c4d2a6ed80
Create Date: 2026-03-22 12:32:35.170109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '807139cdc3c5'
down_revision: Union[str, Sequence[str], None] = 'd4c4d2a6ed80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
