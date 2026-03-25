"""add parameter_definitions table

Revision ID: 5ffce1020786
Revises: 48fe2b3c3568
Create Date: 2026-03-12 06:28:41.450283
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5ffce1020786"
down_revision: Union[str, Sequence[str], None] = "48fe2b3c3568"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "parameter_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parameter_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("expected_unit", sa.String(length=32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("threshold_profile", sa.String(length=64), nullable=True),
        sa.Column("alerts_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_parameter_definitions_parameter_code"),
        "parameter_definitions",
        ["parameter_code"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_parameter_definitions_parameter_code"), table_name="parameter_definitions")
    op.drop_table("parameter_definitions")