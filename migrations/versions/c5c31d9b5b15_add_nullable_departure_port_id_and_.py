"""Add nullable departure_port_id and arrival_port_id to voyage_legs

Revision ID: c5c31d9b5b15
Revises: c51fcc0031b7
Create Date: 2025-07-01 14:10:20.310460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5c31d9b5b15'
down_revision = 'c51fcc0031b7'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('voyage_legs', sa.Column('departure_port_id', sa.Integer(), nullable=True))
    op.add_column('voyage_legs', sa.Column('arrival_port_id', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('voyage_legs', 'departure_port_id')
    op.drop_column('voyage_legs', 'arrival_port_id')

