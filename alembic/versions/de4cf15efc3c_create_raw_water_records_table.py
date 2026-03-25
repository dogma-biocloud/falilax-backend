"""create raw_water_records table

Revision ID: de4cf15efc3c
Revises: e2cfd682a049
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "de4cf15efc3c"
down_revision: Union[str, Sequence[str], None] = "e2cfd682a049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "raw_water_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("external_record_id", sa.String(length=255), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("parsing_status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_raw_water_records_id",
        "raw_water_records",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_raw_water_records_id", table_name="raw_water_records")
    op.drop_table("raw_water_records")