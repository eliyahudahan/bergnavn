# migrations/versions/b4b712744049_add_rtz_fields_to_route_model.py - SAFE VERSION
"""Add RTZ fields to Route model

Revision ID: b4b712744049
Revises: 722cef555736
Create Date: 2025-12-25 15:05:42.975647

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'b4b712744049'
down_revision = '722cef555736'
branch_labels = None
depends_on = None


def upgrade():
    # Check if 'routes' table exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'routes' not in tables:
        # Create the 'routes' table since it doesn't exist
        op.create_table('routes',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('duration_days', sa.Float()),
            sa.Column('total_distance_nm', sa.Float()),
            sa.Column('is_active', sa.Boolean(), server_default='true'),
            sa.Column('origin', sa.String(100)),
            sa.Column('destination', sa.String(100)),
            sa.Column('source', sa.String(50)),
            sa.Column('rtz_filename', sa.String(255)),
            sa.Column('waypoint_count', sa.Integer()),
            sa.Column('rtz_file_hash', sa.String(64)),
            sa.Column('vessel_draft_min', sa.Float()),
            sa.Column('vessel_draft_max', sa.Float()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
            sa.Column('parsed_at', sa.DateTime())
        )
        print("✅ Created 'routes' table")
    else:
        # Table exists, just add the missing columns
        # First check which columns already exist
        existing_columns = [col['name'] for col in inspector.get_columns('routes')]
        
        columns_to_add = {
            'source': sa.Column('source', sa.String(50)),
            'rtz_filename': sa.Column('rtz_filename', sa.String(255)),
            'waypoint_count': sa.Column('waypoint_count', sa.Integer()),
            'rtz_file_hash': sa.Column('rtz_file_hash', sa.String(64)),
            'vessel_draft_min': sa.Column('vessel_draft_min', sa.Float()),
            'vessel_draft_max': sa.Column('vessel_draft_max', sa.Float()),
            'created_at': sa.Column('created_at', sa.DateTime()),
            'updated_at': sa.Column('updated_at', sa.DateTime()),
            'parsed_at': sa.Column('parsed_at', sa.DateTime())
        }
        
        for col_name, column_def in columns_to_add.items():
            if col_name not in existing_columns:
                op.add_column('routes', column_def)
                print(f"✅ Added column '{col_name}' to 'routes' table")
    
    print("🎉 Migration completed successfully")


def downgrade():
    # Check if table exists before trying to drop columns
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'routes' in tables:
        # Only drop the columns we added (not the original ones)
        existing_columns = [col['name'] for col in inspector.get_columns('routes')]
        
        columns_to_drop = ['parsed_at', 'updated_at', 'created_at', 
                          'vessel_draft_max', 'vessel_draft_min', 
                          'rtz_file_hash', 'waypoint_count', 
                          'rtz_filename', 'source']
        
        for col_name in columns_to_drop:
            if col_name in existing_columns:
                op.drop_column('routes', col_name)
                print(f"❌ Dropped column '{col_name}' from 'routes' table")
    
    # Don't drop the entire table in downgrade - keep original structure