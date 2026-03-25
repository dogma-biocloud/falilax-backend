"""merge alert migrations

Revision ID: d3355619a5a9
Revises: 37b1d2b4f7a0, d1b1810f824c
Create Date: 2026-03-04 18:52:41.307953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3355619a5a9'
down_revision: Union[str, Sequence[str], None] = ('37b1d2b4f7a0', 'd1b1810f824c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
