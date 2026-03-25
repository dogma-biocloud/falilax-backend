from alembic import op
import sqlalchemy as sa


# 🔴 You MUST update this after checking existing migrations
revision = "add_sent_at_alert_delivery_logs"
down_revision = None  # TEMP — we will fix this next
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "alert_delivery_logs",
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("alert_delivery_logs", "sent_at")