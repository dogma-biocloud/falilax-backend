"""alerts_dedupe_upgrade

Revision ID: b253d6888eed
Revises: 709e0702a8c1
Create Date: 2026-03-02 18:25:24.704124
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b253d6888eed"
down_revision = "709e0702a8c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade schema:
      - Add alerts.parameter_code (varchar64) default 'unknown'
      - Add alerts.last_seen_at (timestamptz) default now()
      - Add alerts.occurrence_count (int) default 1
      - Backfill existing rows
      - Deduplicate any existing duplicates
      - Add UNIQUE index for dedupe key
    """

    # 1) Add columns safely (idempotent)
    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS parameter_code VARCHAR(64) NOT NULL DEFAULT 'unknown';
        """
    )

    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now();
        """
    )

    op.execute(
        """
        ALTER TABLE alerts
        ADD COLUMN IF NOT EXISTS occurrence_count INTEGER NOT NULL DEFAULT 1;
        """
    )

    # 2) Backfill (for rows created before these columns existed)
    op.execute(
        """
        UPDATE alerts
        SET
          parameter_code    = COALESCE(parameter_code, 'unknown'),
          last_seen_at      = COALESCE(last_seen_at, created_at),
          occurrence_count  = COALESCE(occurrence_count, 1);
        """
    )

    # 3) Deduplicate existing rows BEFORE creating the unique index
    # Keep the newest row per dedupe key; aggregate occurrence_count and last_seen_at.
    op.execute(
        """
        WITH ranked AS (
          SELECT
            id,
            user_id,
            scope_type,
            scope_id,
            tier,
            parameter_code,
            last_seen_at,
            created_at,
            occurrence_count,
            ROW_NUMBER() OVER (
              PARTITION BY user_id, scope_type, scope_id, tier, parameter_code
              ORDER BY last_seen_at DESC, id DESC
            ) AS rn
          FROM alerts
        ),
        agg AS (
          SELECT
            user_id,
            scope_type,
            scope_id,
            tier,
            parameter_code,
            SUM(occurrence_count) AS total_count,
            MAX(last_seen_at)     AS max_last_seen
          FROM ranked
          GROUP BY user_id, scope_type, scope_id, tier, parameter_code
        ),
        keepers AS (
          SELECT *
          FROM ranked
          WHERE rn = 1
        )
        UPDATE alerts a
        SET
          occurrence_count = agg.total_count,
          last_seen_at     = agg.max_last_seen
        FROM agg
        JOIN keepers k
          ON k.user_id = agg.user_id
         AND k.scope_type = agg.scope_type
         AND k.scope_id = agg.scope_id
         AND k.tier = agg.tier
         AND k.parameter_code = agg.parameter_code
        WHERE a.id = k.id;
        """
    )

    # Delete the non-keeper duplicates
    op.execute(
        """
        WITH ranked AS (
          SELECT
            id,
            ROW_NUMBER() OVER (
              PARTITION BY user_id, scope_type, scope_id, tier, parameter_code
              ORDER BY last_seen_at DESC, id DESC
            ) AS rn
          FROM alerts
        )
        DELETE FROM alerts a
        USING ranked r
        WHERE a.id = r.id
          AND r.rn > 1;
        """
    )

    # 4) Create the unique index (idempotent)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_alerts_dedupe
        ON alerts (user_id, scope_type, scope_id, tier, parameter_code);
        """
    )


def downgrade() -> None:
    """
    Downgrade schema:
      - Drop unique index
      - Drop new columns
    """

    op.execute("DROP INDEX IF EXISTS ux_alerts_dedupe;")

    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS occurrence_count;")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS last_seen_at;")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS parameter_code;")