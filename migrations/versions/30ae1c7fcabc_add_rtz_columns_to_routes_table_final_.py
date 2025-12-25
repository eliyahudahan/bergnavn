"""Add RTZ columns to routes table - final fix (with safety checks)

ONLY adds RTZ columns to existing routes table.
Checks if columns exist before adding them.

Revision ID: 30ae1c7fcabc
Revises: 1ee0ff605ab8
Create Date: 2025-12-25 17:31:03.157527
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision = '30ae1c7fcabc'
down_revision = '1ee0ff605ab8'
branch_labels = None
depends_on = None


def upgrade():
    """Add ONLY missing RTZ columns with safety checks."""
    
    # Get database connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('routes')]
    print(f"📊 Existing columns in 'routes': {existing_columns}")
    
    # Define all RTZ columns to add
    columns_to_add = [
        {
            'name': 'source',
            'type': sa.String(50),
            'kwargs': {'nullable': True, 'server_default': 'NCA'}
        },
        {
            'name': 'rtz_filename', 
            'type': sa.String(255),
            'kwargs': {'nullable': True}
        },
        {
            'name': 'waypoint_count',
            'type': sa.Integer(),
            'kwargs': {'nullable': True, 'server_default': '0'}
        },
        {
            'name': 'rtz_file_hash',
            'type': sa.String(64),
            'kwargs': {'nullable': True}
        },
        {
            'name': 'vessel_draft_min',
            'type': sa.Float(),
            'kwargs': {'nullable': True}
        },
        {
            'name': 'vessel_draft_max',
            'type': sa.Float(),
            'kwargs': {'nullable': True}
        },
        {
            'name': 'created_at',
            'type': sa.DateTime(),
            'kwargs': {'nullable': True, 'server_default': text('CURRENT_TIMESTAMP')}
        },
        {
            'name': 'updated_at',
            'type': sa.DateTime(),
            'kwargs': {'nullable': True, 'server_default': text('CURRENT_TIMESTAMP')}
        },
        {
            'name': 'parsed_at',
            'type': sa.DateTime(),
            'kwargs': {'nullable': True}
        }
    ]
    
    # Add only columns that don't exist
    columns_added = 0
    for col_def in columns_to_add:
        col_name = col_def['name']
        
        if col_name not in existing_columns:
            print(f"➕ Adding column: {col_name}")
            op.add_column('routes', sa.Column(col_name, col_def['type'], **col_def['kwargs']))
            columns_added += 1
        else:
            print(f"✓ Column already exists: {col_name}")
    
    print(f"✅ Added {columns_added} new columns to 'routes' table")
    
    # Verify final state
    final_columns = [col['name'] for col in inspector.get_columns('routes')]
    print(f"📊 Final columns in 'routes': {sorted(final_columns)}")


def downgrade():
    """Remove RTZ columns (only if they exist)."""
    
    # Get database connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('routes')]
    
    # Define RTZ columns to remove (in reverse order)
    columns_to_remove = [
        'parsed_at',
        'updated_at',
        'created_at',
        'vessel_draft_max',
        'vessel_draft_min',
        'rtz_file_hash',
        'waypoint_count',
        'rtz_filename',
        'source'
    ]
    
    # Remove only columns that exist
    columns_removed = 0
    for col_name in columns_to_remove:
        if col_name in existing_columns:
            print(f"➖ Removing column: {col_name}")
            op.drop_column('routes', col_name)
            columns_removed += 1
        else:
            print(f"✗ Column doesn't exist: {col_name}")
    
    print(f"🗑️  Removed {columns_removed} columns from 'routes' table")