"""create ingestion_runs table

Revision ID: e2cfd682a049
Revises: b76b963a6f7d
Create Date: 2026-03-17 18:49:14.598926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2cfd682a049"
down_revision: Union[str, Sequence[str], None] = "b76b963a6f7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("records_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_loaded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("log_summary", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_ingestion_runs_id",
        "ingestion_runs",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_runs_id", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")