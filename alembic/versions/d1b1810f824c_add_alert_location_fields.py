"""add alert location fields

Revision ID: d1b1810f824c
Revises: b253d6888eed
Create Date: 2026-03-04 18:36:51.327727

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d1b1810f824c"
down_revision: Union[str, Sequence[str], None] = "b253d6888eed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Address + human label
    op.add_column("alerts", sa.Column("location_label", sa.String(length=255), nullable=True))

    op.add_column("alerts", sa.Column("address_line1", sa.String(length=255), nullable=True))
    op.add_column("alerts", sa.Column("address_line2", sa.String(length=255), nullable=True))
    op.add_column("alerts", sa.Column("city", sa.String(length=128), nullable=True))
    op.add_column("alerts", sa.Column("state_region", sa.String(length=64), nullable=True))
    op.add_column("alerts", sa.Column("postal_code", sa.String(length=32), nullable=True))
    op.add_column("alerts", sa.Column("country", sa.String(length=64), nullable=True))

    # Geo
    op.add_column("alerts", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("alerts", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("alerts", sa.Column("plus_code", sa.String(length=32), nullable=True))

    # Helpful context for humans
    op.add_column("alerts", sa.Column("landmark", sa.String(length=255), nullable=True))
    op.add_column("alerts", sa.Column("directions_hint", sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Reverse order is safest
    op.drop_column("alerts", "directions_hint")
    op.drop_column("alerts", "landmark")

    op.drop_column("alerts", "plus_code")
    op.drop_column("alerts", "longitude")
    op.drop_column("alerts", "latitude")

    op.drop_column("alerts", "country")
    op.drop_column("alerts", "postal_code")
    op.drop_column("alerts", "state_region")
    op.drop_column("alerts", "city")
    op.drop_column("alerts", "address_line2")
    op.drop_column("alerts", "address_line1")

    op.drop_column("alerts", "location_label")