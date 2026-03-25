"""alert delivery retries and errors

Revision ID: 1357bdcb4241
Revises: 9f3f0c3101aa
Create Date: 2026-03-05 18:49:14.337862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1357bdcb4241'
down_revision: Union[str, Sequence[str], None] = '9f3f0c3101aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
