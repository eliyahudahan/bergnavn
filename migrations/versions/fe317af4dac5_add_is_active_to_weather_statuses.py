"""Add is_active to weather_statuses

Revision ID: fe317af4dac5
Revises: ced888ac2536
Create Date: 2025-07-07 14:05:14.659221

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe317af4dac5'
down_revision = 'ced888ac2536'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('weather_statuses', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()))

def downgrade():
    op.drop_column('weather_statuses', 'is_active')

