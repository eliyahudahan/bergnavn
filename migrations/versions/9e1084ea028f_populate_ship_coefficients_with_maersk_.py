"""Populate ship coefficients with Maersk methanol data

Revision ID: 9e1084ea028f
Revises: 446506ff1f1c
Create Date: 2025-10-28 14:05:21.900536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e1084ea028f'
down_revision = '446506ff1f1c'
branch_labels = None
depends_on = None


def upgrade():
    # ### REMOVE the index creation lines ###
    # op.create_index('idx_hazard_zones_geometry', 'hazard_zones', ['geometry'], unique=False, postgresql_using='gist')
    # op.create_index('idx_route_legs_geometry', 'route_legs', ['geometry'], unique=False, postgresql_using='gist')
    
    # ### ADD data population with direct SQL ###
    op.execute("""
        INSERT INTO ship_type_coefficients 
        (ship_type, base_consumption_coef, optimal_speed_knots, fuel_cost_usd_tonne, maintenance_impact, methanol_consumption_ratio, methanol_cost_usd_tonne, validation_status, created_at)
        VALUES
        ('tanker', 0.0060, 11.0, 800.0, 0.15, 1.8, 1200.0, 'maersk_validated', NOW()),
        ('container', 0.0040, 14.0, 750.0, 0.08, 1.8, 1150.0, 'maersk_validated', NOW()),
        ('bulk_carrier', 0.0055, 13.0, 740.0, 0.11, 1.8, 1100.0, 'sandbox_validated', NOW()),
        ('roro', 0.0042, 15.0, 770.0, 0.09, 1.8, 1180.0, 'sandbox_validated', NOW()),
        ('passenger', 0.0045, 16.0, 780.0, 0.12, 1.8, 1250.0, 'theoretical', NOW()),
        ('cargo', 0.0050, 12.0, 760.0, 0.10, 1.8, 1120.0, 'theoretical', NOW())
        ON CONFLICT (ship_type) DO NOTHING;
    """)


def downgrade():
    # ### REMOVE the index dropping lines ###
    # op.drop_index('idx_route_legs_geometry', table_name='route_legs', postgresql_using='gist')
    # op.drop_index('idx_hazard_zones_geometry', table_name='hazard_zones', postgresql_using='gist')
    
    # ### ADD data removal instead ###
    op.execute("DELETE FROM ship_type_coefficients")