"""Merge multiple heads

Revision ID: af55ca751c7c
Revises: 4f8d4be9d672, a2668fb2c079
Create Date: 2025-06-30 15:27:51.692659

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af55ca751c7c'
down_revision = ('4f8d4be9d672', 'a2668fb2c079')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
