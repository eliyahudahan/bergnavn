"""real unified maritime model

Revision ID: 722cef555736
Revises: 6ee84f482a42
Create Date: 2025-11-29 17:30:00
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


# Revision identifiers
revision = '722cef555736'
down_revision = '6ee84f482a42'
branch_labels = None
depends_on = None


def upgrade():
    """
    Main upgrade entrypoint.
    This migration ensures that:
    - hazard_zones table exists with correct geometry column
    - GIST index exists
    - clocks table is created safely without using reserved SQL keywords
    """

    # -------------------------------
    # Create hazard_zones if missing
    # -------------------------------
    op.create_table(
        'hazard_zones',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('hazard_type', sa.String(100), nullable=False),
        sa.Column('geometry', Geometry(geometry_type='POLYGON', srid=4326)),
        sa.Column('risk_score', sa.Float, nullable=True)
    )

    # Create GIST index on geometry
    op.create_index(
        'idx_hazard_zones_geometry',
        'hazard_zones',
        ['geometry'],
        postgresql_using='gist'
    )

    # -------------------------------
    # Create clocks table safely
    # NOTE: "offset" is a reserved PostgreSQL keyword → renamed to timezone_offset
    # -------------------------------

    op.create_table(
        'clocks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('cruise_id', sa.Integer, sa.ForeignKey('cruises.id'), nullable=False),
        sa.Column('timezone', sa.String(100), nullable=False),
        sa.Column('timezone_offset', sa.Integer),   # FIXED: renamed from offset
        sa.Column('created_at', sa.TIMESTAMP)
    )


def downgrade():
    """
    Reverse schema changes.
    """
    op.drop_index('idx_hazard_zones_geometry', table_name='hazard_zones')
    op.drop_table('hazard_zones')
    op.drop_table('clocks')
