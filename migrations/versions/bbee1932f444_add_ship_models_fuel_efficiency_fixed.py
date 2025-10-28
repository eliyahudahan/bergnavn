"""add_ship_models_fuel_efficiency_fixed

Revision ID: bbee1932f444
Revises: 6fbb0ab73f2a
Create Date: 2025-10-27 14:36:23.685921

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'bbee1932f444'
down_revision = '6fbb0ab73f2a'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name):
    """Check if a table exists"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def index_exists(table_name, index_name):
    """Check if an index exists"""
    conn = op.get_bind()
    inspector = inspect(conn)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # ✅ SAFE: Remove unused dummy_users table (only if exists)
    if 'dummy_users' in inspector.get_table_names():
        op.drop_table('dummy_users')
        print("✅ Dropped dummy_users table")
    
    # ✅ Add missing columns to ships table (only if they don't exist)
    if not column_exists('ships', 'home_port'):
        op.add_column('ships', sa.Column('home_port', sa.String(50), nullable=True))
        print("✅ Added home_port to ships")
    else:
        print("⚠️  home_port already exists in ships")
    
    if not column_exists('ships', 'fuel_efficiency_profile'):
        op.add_column('ships', sa.Column('fuel_efficiency_profile', sa.JSON(), nullable=True))
        print("✅ Added fuel_efficiency_profile to ships")
    else:
        print("⚠️  fuel_efficiency_profile already exists in ships")
    
    if not column_exists('ships', 'operational_constraints'):
        op.add_column('ships', sa.Column('operational_constraints', sa.JSON(), nullable=True))
        print("✅ Added operational_constraints to ships")
    else:
        print("⚠️  operational_constraints already exists in ships")
    
    if not column_exists('ships', 'alternative_fuel_capability'):
        op.add_column('ships', sa.Column('alternative_fuel_capability', sa.Boolean(), server_default='false'))
        print("✅ Added alternative_fuel_capability to ships")
    else:
        print("⚠️  alternative_fuel_capability already exists in ships")
    
    # ✅ Add missing columns to fuel_efficiency_calculations table (only if they don't exist)
    fuel_calc_columns = [
        ('weather_wind_speed', sa.Column('weather_wind_speed', sa.Float(), nullable=True)),
        ('weather_wind_direction', sa.Column('weather_wind_direction', sa.Float(), nullable=True)),
        ('efficiency_class', sa.Column('efficiency_class', sa.String(10), nullable=True)),
        ('confidence_score', sa.Column('confidence_score', sa.Float(), nullable=True)),
        ('algorithm_version', sa.Column('algorithm_version', sa.String(20), server_default='v2.0_sandbox')),
        ('alternative_fuel_type', sa.Column('alternative_fuel_type', sa.String(20), nullable=True)),
        ('alternative_fuel_savings', sa.Column('alternative_fuel_savings', sa.Float(), nullable=True))
    ]
    
    for col_name, column in fuel_calc_columns:
        if not column_exists('fuel_efficiency_calculations', col_name):
            op.add_column('fuel_efficiency_calculations', column)
            print(f"✅ Added {col_name} to fuel_efficiency_calculations")
        else:
            print(f"⚠️  {col_name} already exists in fuel_efficiency_calculations")
    
    # ✅ Create spatial indexes for better performance (only if they don't exist)
    spatial_indexes = [
        ('base_routes', 'idx_base_routes_geometry', 'geometry'),
        ('hazard_zones', 'idx_hazard_zones_geometry', 'geometry'),
        ('route_legs', 'idx_route_legs_geometry', 'geometry'),
        ('waypoints', 'idx_waypoints_position', 'position')
    ]
    
    for table, index_name, column in spatial_indexes:
        if table_exists(table) and not index_exists(table, index_name):
            op.create_index(index_name, table, [column], unique=False, postgresql_using='gist')
            print(f"✅ Created spatial index {index_name} on {table}")
        else:
            print(f"⚠️  Index {index_name} already exists or table {table} doesn't exist")


def downgrade():
    # Remove indexes (only if they exist)
    if index_exists('waypoints', 'idx_waypoints_position'):
        op.drop_index('idx_waypoints_position', table_name='waypoints', postgresql_using='gist')
        print("✅ Dropped idx_waypoints_position index")
    
    if index_exists('route_legs', 'idx_route_legs_geometry'):
        op.drop_index('idx_route_legs_geometry', table_name='route_legs', postgresql_using='gist')
        print("✅ Dropped idx_route_legs_geometry index")
    
    if index_exists('hazard_zones', 'idx_hazard_zones_geometry'):
        op.drop_index('idx_hazard_zones_geometry', table_name='hazard_zones', postgresql_using='gist')
        print("✅ Dropped idx_hazard_zones_geometry index")
    
    if index_exists('base_routes', 'idx_base_routes_geometry'):
        op.drop_index('idx_base_routes_geometry', table_name='base_routes', postgresql_using='gist')
        print("✅ Dropped idx_base_routes_geometry index")
    
    # Remove new columns from fuel_efficiency_calculations (only if they exist)
    fuel_calc_columns = [
        'alternative_fuel_savings',
        'alternative_fuel_type',
        'algorithm_version',
        'confidence_score',
        'efficiency_class',
        'weather_wind_direction',
        'weather_wind_speed'
    ]
    
    for col_name in fuel_calc_columns:
        if column_exists('fuel_efficiency_calculations', col_name):
            op.drop_column('fuel_efficiency_calculations', col_name)
            print(f"✅ Dropped {col_name} from fuel_efficiency_calculations")
    
    # Remove new columns from ships (only if they exist)
    ships_columns = [
        'alternative_fuel_capability',
        'operational_constraints',
        'fuel_efficiency_profile',
        'home_port'
    ]
    
    for col_name in ships_columns:
        if column_exists('ships', col_name):
            op.drop_column('ships', col_name)
            print(f"✅ Dropped {col_name} from ships")
    
    # Restore dummy_users (optional - only if it doesn't exist)
    if not table_exists('dummy_users'):
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
        print("✅ Restored dummy_users table")