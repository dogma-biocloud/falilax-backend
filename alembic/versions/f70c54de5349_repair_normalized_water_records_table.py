"""repair normalized_water_records table

Revision ID: f70c54de5349
Revises: fe012f07545d
Create Date: 2026-03-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f70c54de5349"
down_revision: Union[str, Sequence[str], None] = "fe012f07545d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "normalized_water_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_record_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("location_name", sa.String(length=255), nullable=False),
        sa.Column("parameter_code", sa.String(length=64), nullable=False),
        sa.Column("parameter_name", sa.String(length=255), nullable=False),
        sa.Column("measured_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("original_value", sa.Float(), nullable=True),
        sa.Column("original_unit", sa.String(length=32), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sample_date", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_normalized_water_records_id",
        "normalized_water_records",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_normalized_water_records_id",
        table_name="normalized_water_records",
    )
    op.drop_table("normalized_water_records")