from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("alerts", sa.Column("delivery_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("alerts", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("alerts", sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("alerts", "last_error_at")
    op.drop_column("alerts", "last_error")
    op.drop_column("alerts", "delivery_attempts")