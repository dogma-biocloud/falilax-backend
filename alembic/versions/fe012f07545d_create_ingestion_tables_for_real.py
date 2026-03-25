"""create ingestion tables for real"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "fe012f07545d"
down_revision: Union[str, Sequence[str], None] = "1cdcdab77596"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # DATA SOURCES
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("organization_name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("endpoint_url", sa.Text(), nullable=True),
        sa.Column("auth_type", sa.String(50), nullable=True),
        sa.Column("parser_type", sa.String(50), nullable=False, server_default="generic"),
        sa.Column("refresh_interval_minutes", sa.Integer(), nullable=True),
        sa.Column("region", sa.String(255), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("county", sa.String(100), nullable=True),
        sa.Column("default_location_id", sa.Integer(), sa.ForeignKey("locations.id")),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # INGESTION RUNS
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="started"),
        sa.Column("records_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_loaded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column("log_summary", sa.Text()),
    )

    # RAW WATER RECORDS
    op.create_table(
        "raw_water_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), sa.ForeignKey("ingestion_runs.id"), nullable=False),
        sa.Column("external_record_id", sa.String(255)),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("parsing_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("raw_water_records")
    op.drop_table("ingestion_runs")
    op.drop_table("data_sources")