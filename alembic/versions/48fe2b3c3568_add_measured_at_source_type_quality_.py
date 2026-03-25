"""add measured_at source_type quality_flag to measurements

Revision ID: 48fe2b3c3568
Revises: f5c3e8d9ebbc
Create Date: 2026-03-11 19:42:38.687882
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "48fe2b3c3568"
down_revision: Union[str, Sequence[str], None] = "f5c3e8d9ebbc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "measurements",
        sa.Column(
            "measured_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "measurements",
        sa.Column(
            "source_type",
            sa.String(length=32),
            server_default="manual",
            nullable=False,
        ),
    )
    op.add_column(
        "measurements",
        sa.Column(
            "quality_flag",
            sa.String(length=32),
            server_default="valid",
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_measurements_sample_id"),
        "measurements",
        ["sample_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_measurements_sample_id"), table_name="measurements")
    op.drop_column("measurements", "quality_flag")
    op.drop_column("measurements", "source_type")
    op.drop_column("measurements", "measured_at")