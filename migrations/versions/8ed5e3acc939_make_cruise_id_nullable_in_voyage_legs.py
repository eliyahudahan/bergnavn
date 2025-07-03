"""Make cruise_id nullable in voyage_legs

Revision ID: 8ed5e3acc939
Revises: 4fc5d623bb68
Create Date: 2025-07-03 14:42:40.800356
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8ed5e3acc939'
down_revision = '4fc5d623bb68'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('voyage_legs', 'cruise_id',
        existing_type=sa.INTEGER(),
        nullable=True)


def downgrade():
    op.alter_column('voyage_legs', 'cruise_id',
        existing_type=sa.INTEGER(),
        nullable=False)

