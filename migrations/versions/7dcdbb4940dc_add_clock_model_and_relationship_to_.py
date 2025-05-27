"""Add Clock model and relationship to Cruise

Revision ID: 7dcdbb4940dc
Revises: dbc244ec5744
Create Date: 2025-05-27 13:31:33.192391

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7dcdbb4940dc'
down_revision = 'dbc244ec5744'
branch_labels = None
depends_on = None


def upgrade():
    # Create the clocks table
    op.create_table(
        'clocks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('cruise_id', sa.Integer, sa.ForeignKey('cruises.id'), nullable=False),
        sa.Column('timezone', sa.String(length=100), nullable=False),
        sa.Column('offset', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )


def downgrade():
    # Drop the clocks table on downgrade
    op.drop_table('clocks')

