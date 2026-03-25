from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f5c3e8d9ebbc"
down_revision = "69ca9219743d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alert_subscriptions",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True
        ),

        # who receives the alert
        sa.Column(
            "subscriber_type",
            sa.String(length=32),
            nullable=False
        ),

        sa.Column(
            "subscriber_id",
            sa.Integer(),
            nullable=True
        ),

        # routing scope (cluster / region / county / site / household)
        sa.Column(
            "scope_type",
            sa.String(length=32),
            nullable=False
        ),

        sa.Column(
            "scope_code",
            sa.String(length=128),
            nullable=False
        ),

        # delivery system
        sa.Column(
            "delivery_channel",
            sa.String(length=16),
            nullable=False,
            server_default="in_app"
        ),

        sa.Column(
            "recipient",
            sa.String(length=255),
            nullable=True
        ),

        # enable / disable subscription
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true")
        ),

        # creation timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()")
        ),
    )

    # index for fast geographic alert routing
    op.create_index(
        "ix_alert_subscriptions_scope",
        "alert_subscriptions",
        ["scope_type", "scope_code"],
        unique=False
    )


def downgrade():
    op.drop_index(
        "ix_alert_subscriptions_scope",
        table_name="alert_subscriptions"
    )

    op.drop_table("alert_subscriptions")