"""safe_migration_fix_duplicate_columns

Revision ID: 47e53f867723
Revises: bbee1932f444
Create Date: 2025-10-27 14:42:49.220971

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47e53f867723'
down_revision = 'bbee1932f444'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
