"""add alert location columns

Revision ID: 9f3f0c3101aa
Revises: d3355619a5a9
Create Date: 2026-03-04 18:57:49.318171
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "9f3f0c3101aa"
down_revision: Union[str, Sequence[str], None] = "d3355619a5a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, col_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return any(c["name"] == col_name for c in insp.get_columns(table_name))


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    """Upgrade schema."""
    table = "alerts"

    _add_column_if_missing(table, sa.Column("location_label", sa.String(length=255), nullable=True))

    _add_column_if_missing(table, sa.Column("address_line1", sa.String(length=255), nullable=True))
    _add_column_if_missing(table, sa.Column("address_line2", sa.String(length=255), nullable=True))
    _add_column_if_missing(table, sa.Column("city", sa.String(length=128), nullable=True))
    _add_column_if_missing(table, sa.Column("state_region", sa.String(length=64), nullable=True))
    _add_column_if_missing(table, sa.Column("postal_code", sa.String(length=32), nullable=True))
    _add_column_if_missing(table, sa.Column("country", sa.String(length=64), nullable=True))

    _add_column_if_missing(table, sa.Column("latitude", sa.Float(), nullable=True))
    _add_column_if_missing(table, sa.Column("longitude", sa.Float(), nullable=True))
    _add_column_if_missing(table, sa.Column("plus_code", sa.String(length=64), nullable=True))

    _add_column_if_missing(table, sa.Column("landmark", sa.String(length=255), nullable=True))
    _add_column_if_missing(table, sa.Column("directions_hint", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    table = "alerts"

    # Drop in reverse order; only if they exist.
    for name in [
        "directions_hint",
        "landmark",
        "plus_code",
        "longitude",
        "latitude",
        "country",
        "postal_code",
        "state_region",
        "city",
        "address_line2",
        "address_line1",
        "location_label",
    ]:
        if _has_column(table, name):
            op.drop_column(table, name)