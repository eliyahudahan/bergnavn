"""Merge all heads before adding port_id columns

Revision ID: 5e69322f5e60
Revises: 446d55e96113, 631b182f345c
Create Date: 2025-07-01 15:00:13.659357

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e69322f5e60'
down_revision = ('446d55e96113', '631b182f345c')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
