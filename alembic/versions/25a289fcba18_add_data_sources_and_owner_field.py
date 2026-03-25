"""add data_sources and owner field

Revision ID: 25a289fcba18
Revises: 5a9a8d725829
Create Date: 2026-03-17 08:01:07.057864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "25a289fcba18"
down_revision: Union[str, Sequence[str], None] = "5a9a8d725829"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("endpoint_url", sa.Text(), nullable=True),
        sa.Column("auth_type", sa.String(length=50), nullable=True),
        sa.Column("parser_type", sa.String(length=50), nullable=False, server_default="generic"),
        sa.Column("refresh_interval_minutes", sa.Integer(), nullable=True),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("county", sa.String(length=100), nullable=True),
        sa.Column("default_location_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["default_location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_data_sources_id"), "data_sources", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_data_sources_id"), table_name="data_sources")
    op.drop_table("data_sources")