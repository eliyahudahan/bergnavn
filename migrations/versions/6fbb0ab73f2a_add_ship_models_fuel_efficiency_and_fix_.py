"""add_ship_models_fuel_efficiency_and_fix_imports

Revision ID: 6fbb0ab73f2a
Revises: 56456e05a868
Create Date: 2025-10-27 14:13:51.332459
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '6fbb0ab73f2a'
down_revision = '56456e05a868'
branch_labels = None
depends_on = None


def upgrade():
    # ✅ SAFE: Remove unused dummy_users table (only if exists)
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'dummy_users' in inspector.get_table_names():
        op.drop_table('dummy_users')
    
    # ✅ SKIP: ship_type_coefficients already exists - don't create again
    # op.create_table('ship_type_coefficients')  # ❌ COMMENTED OUT - already exists
    
    # ✅ Add missing columns to ships table
    op.add_column('ships', sa.Column('home_port', sa.String(50), nullable=True))
    op.add_column('ships', sa.Column('fuel_efficiency_profile', sa.JSON(), nullable=True))
    op.add_column('ships', sa.Column('operational_constraints', sa.JSON(), nullable=True))
    op.add_column('ships', sa.Column('alternative_fuel_capability', sa.Boolean(), server_default='false'))
    
    # ✅ Add missing columns to fuel_efficiency_calculations table
    op.add_column('fuel_efficiency_calculations', sa.Column('weather_wind_speed', sa.Float(), nullable=True))
    op.add_column('fuel_efficiency_calculations', sa.Column('weather_wind_direction', sa.Float(), nullable=True))
    op.add_column('fuel_efficiency_calculations', sa.Column('efficiency_class', sa.String(10), nullable=True))
    op.add_column('fuel_efficiency_calculations', sa.Column('confidence_score', sa.Float(), nullable=True))
    op.add_column('fuel_efficiency_calculations', sa.Column('algorithm_version', sa.String(20), server_default='v2.0_sandbox'))
    op.add_column('fuel_efficiency_calculations', sa.Column('alternative_fuel_type', sa.String(20), nullable=True))
    op.add_column('fuel_efficiency_calculations', sa.Column('alternative_fuel_savings', sa.Float(), nullable=True))
    
    # ✅ Create spatial indexes for better performance
    op.create_index('idx_base_routes_geometry', 'base_routes', ['geometry'], unique=False, postgresql_using='gist')
    op.create_index('idx_hazard_zones_geometry', 'hazard_zones', ['geometry'], unique=False, postgresql_using='gist')
    op.create_index('idx_route_legs_geometry', 'route_legs', ['geometry'], unique=False, postgresql_using='gist')
    op.create_index('idx_waypoints_position', 'waypoints', ['position'], unique=False, postgresql_using='gist')


def downgrade():
    # Remove indexes
    op.drop_index('idx_waypoints_position', table_name='waypoints', postgresql_using='gist')
    op.drop_index('idx_route_legs_geometry', table_name='route_legs', postgresql_using='gist')
    op.drop_index('idx_hazard_zones_geometry', table_name='hazard_zones', postgresql_using='gist')
    op.drop_index('idx_base_routes_geometry', table_name='base_routes', postgresql_using='gist')
    
    # Remove new columns
    op.drop_column('fuel_efficiency_calculations', 'alternative_fuel_savings')
    op.drop_column('fuel_efficiency_calculations', 'alternative_fuel_type')
    op.drop_column('fuel_efficiency_calculations', 'algorithm_version')
    op.drop_column('fuel_efficiency_calculations', 'confidence_score')
    op.drop_column('fuel_efficiency_calculations', 'efficiency_class')
    op.drop_column('fuel_efficiency_calculations', 'weather_wind_direction')
    op.drop_column('fuel_efficiency_calculations', 'weather_wind_speed')
    
    op.drop_column('ships', 'alternative_fuel_capability')
    op.drop_column('ships', 'operational_constraints')
    op.drop_column('ships', 'fuel_efficiency_profile')
    op.drop_column('ships', 'home_port')
    
    # Restore dummy_users (optional)
    op.create_table('dummy_users',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('username', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
        sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=True),
        sa.Column('scenario', sa.VARCHAR(length=120), autoincrement=False, nullable=True),
        sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('flags', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.Column('gender', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
        sa.Column('nationality', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
        sa.Column('language', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
        sa.Column('preferred_sailing_areas', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='dummy_users_pkey'),
        sa.UniqueConstraint('email', name='dummy_users_email_key'),
        sa.UniqueConstraint('username', name='dummy_users_username_key')
    )