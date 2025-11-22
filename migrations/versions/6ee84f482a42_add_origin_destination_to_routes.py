"""add_origin_destination_to_routes

Revision ID: 6ee84f482a42
Revises: 9e1084ea028f
Create Date: 2025-11-22 23:39:58.768375

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ee84f482a42'
down_revision = '9e1084ea028f'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add origin and destination columns to routes table.
    These columns will store the start and end points of maritime routes.
    """
    # Add origin column to store route starting point
    op.add_column('routes', sa.Column('origin', sa.String(length=100), nullable=True))
    
    # Add destination column to store route ending point  
    op.add_column('routes', sa.Column('destination', sa.String(length=100), nullable=True))
    
    # Optional: Add spatial indexes for better performance (not primary purpose)
    op.create_index('idx_hazard_zones_geometry', 'hazard_zones', ['geometry'], 
                   unique=False, postgresql_using='gist')
    op.create_index('idx_route_legs_geometry', 'route_legs', ['geometry'], 
                   unique=False, postgresql_using='gist')


def downgrade():
    """
    Remove origin and destination columns from routes table.
    """
    # Remove destination column first
    op.drop_column('routes', 'destination')
    
    # Remove origin column
    op.drop_column('routes', 'origin')
    
    # Remove optional indexes
    op.drop_index('idx_route_legs_geometry', table_name='route_legs', postgresql_using='gist')
    op.drop_index('idx_hazard_zones_geometry', table_name='hazard_zones', postgresql_using='gist')