from alembic import op
import sqlalchemy as sa


revision = '5eeab2e5bad5'
down_revision = '8ed5e3acc939'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('voyage_legs', sa.Column('distance_nm', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('voyage_legs', 'distance_nm')

