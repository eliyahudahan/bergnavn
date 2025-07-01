"""merge conflicting heads

Revision ID: aebb30329dab
Revises: 3355c0cd0f82, 3719a673908a
Create Date: 2025-07-01 13:28:56.140859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aebb30329dab'
down_revision = ('3355c0cd0f82', '3719a673908a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
