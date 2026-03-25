"""alert delivery retries and errors

Revision ID: c136e0513134
Revises: 1357bdcb4241
Create Date: 2026-03-05 18:49:34.195431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c136e0513134'
down_revision: Union[str, Sequence[str], None] = '1357bdcb4241'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
