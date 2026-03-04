"""alert_delivery_and_attribution

Revision ID: 37b1d2b4f7a0
Revises: b253d6888eed
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "37b1d2b4f7a0"
down_revision: Union[str, None] = "b253d6888eed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema:
      Add alert delivery + attribution fields to support:
        - Source attribution (central vs line vs site)
        - Geographic targeting (cluster/region/county)
        - Hybrid delivery (email/sms/in-app)
        - Disclaimers & confidence to reduce liability/public charges risk
    """

    # --- Delivery (hybrid: sms/email/in_app) ---
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS delivery_channel VARCHAR(16) NOT NULL DEFAULT 'in_app';
        """
    )
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS recipient VARCHAR(255);
        """
    )
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMPTZ;
        """
    )

    # --- Attribution (where did the anomaly originate?) ---
    # origin_scope_type/origin_scope_id lets you say:
    #   central_system: <id>, distribution_line: <id>, site: <id>
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS origin_scope_type VARCHAR(32) NOT NULL DEFAULT 'unknown';
        """
    )
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS origin_scope_id INTEGER;
        """
    )

    # --- Geo targeting (group notifications by area) ---
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS cluster_code VARCHAR(64);
        """
    )
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS region_code VARCHAR(64);
        """
    )
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS county_code VARCHAR(64);
        """
    )

    # --- Safety / disclaimers / confidence ---
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS confidence VARCHAR(16) NOT NULL DEFAULT 'suspected';
        """
    )
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS disclaimer VARCHAR(500);
        """
    )

    # Indexes to speed up filtering/queues
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_alerts_delivery_queue
        ON alerts (status, scheduled_for);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_alerts_origin_scope
        ON alerts (origin_scope_type, origin_scope_id);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_alerts_geo
        ON alerts (cluster_code, region_code, county_code);
        """
    )

    # Backfill disclaimer (optional, safe default)
    op.execute(
        """
        UPDATE alerts
        SET disclaimer = COALESCE(
            disclaimer,
            'FalilaX provides informational water-quality alerts only. Not medical advice. If you believe there is immediate danger, contact local authorities or a qualified professional.'
        )
        WHERE disclaimer IS NULL;
        """
    )


def downgrade() -> None:
    """
    Downgrade schema: remove added columns/indexes.
    """

    op.execute("DROP INDEX IF EXISTS ix_alerts_geo;")
    op.execute("DROP INDEX IF EXISTS ix_alerts_origin_scope;")
    op.execute("DROP INDEX IF EXISTS ix_alerts_delivery_queue;")

    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS disclaimer;")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS confidence;")

    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS county_code;")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS region_code;")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS cluster_code;")

    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS origin_scope_id;")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS origin_scope_type;")

    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS scheduled_for;")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS recipient;")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS delivery_channel;")