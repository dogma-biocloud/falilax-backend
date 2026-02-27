from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "709e0702a8c1"
down_revision = "4c5a87da38ee"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "water_samples",
        "collected_at",
        existing_type=sa.VARCHAR(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="collected_at::timestamptz",
        existing_nullable=False,
    )

    op.alter_column(
        "water_samples",
        "created_at",
        existing_type=sa.VARCHAR(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at::timestamptz",
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "water_samples",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.VARCHAR(),
        postgresql_using="created_at::text",
        existing_nullable=False,
    )

    op.alter_column(
        "water_samples",
        "collected_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.VARCHAR(),
        postgresql_using="collected_at::text",
        existing_nullable=False,
    )