"""Add RTZ columns to routes - FIXED version

Adds all RTZ columns to routes table using simple SQL.
Designed to work with the 'framg' database.

Revision ID: rtz_final_fix
Revises: rtz_sql_fix
Create Date: 2025-12-25 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic
revision = 'rtz_final_fix'
down_revision = 'rtz_sql_fix'
branch_labels = None
depends_on = None


def upgrade():
    """Add all RTZ columns to routes table."""
    
    print("🚀 Starting RTZ columns addition to 'routes' table...")
    
    # Get database connection
    conn = op.get_bind()
    
    # Check current columns
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'routes'
    """))
    
    existing_columns = {row[0] for row in result}
    print(f"📊 Found {len(existing_columns)} existing columns: {sorted(existing_columns)}")
    
    # Define all RTZ columns to add
    columns_to_add = [
        {
            'name': 'source',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'NCA'",
            'type': 'VARCHAR(50)',
            'default': "'NCA'"
        },
        {
            'name': 'rtz_filename',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS rtz_filename VARCHAR(255)",
            'type': 'VARCHAR(255)'
        },
        {
            'name': 'waypoint_count',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS waypoint_count INTEGER DEFAULT 0",
            'type': 'INTEGER',
            'default': '0'
        },
        {
            'name': 'rtz_file_hash',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS rtz_file_hash VARCHAR(64)",
            'type': 'VARCHAR(64)'
        },
        {
            'name': 'vessel_draft_min',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS vessel_draft_min DOUBLE PRECISION",
            'type': 'DOUBLE PRECISION'
        },
        {
            'name': 'vessel_draft_max',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS vessel_draft_max DOUBLE PRECISION",
            'type': 'DOUBLE PRECISION'
        },
        {
            'name': 'created_at',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            'type': 'TIMESTAMP',
            'default': 'CURRENT_TIMESTAMP'
        },
        {
            'name': 'updated_at',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            'type': 'TIMESTAMP',
            'default': 'CURRENT_TIMESTAMP'
        },
        {
            'name': 'parsed_at',
            'sql': "ALTER TABLE routes ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP",
            'type': 'TIMESTAMP'
        }
    ]
    
    # Add each column
    added_count = 0
    for col in columns_to_add:
        col_name = col['name']
        
        if col_name in existing_columns:
            print(f"✅ Column '{col_name}' already exists")
        else:
            try:
                conn.execute(text(col['sql']))
                print(f"➕ Added column '{col_name}' ({col['type']})")
                added_count += 1
            except Exception as e:
                print(f"❌ Failed to add '{col_name}': {e}")
    
    print(f"\n🎯 Added {added_count} new columns")
    
    # Verify final state
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'routes'
        ORDER BY ordinal_position
    """))
    
    final_columns = [row[0] for row in result]
    print(f"📊 Final columns ({len(final_columns)} total): {final_columns}")


def downgrade():
    """Remove RTZ columns."""
    
    print("🗑️ Removing RTZ columns from 'routes' table...")
    
    # Get database connection
    conn = op.get_bind()
    
    # Columns to remove
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
    
    # Remove each column
    removed_count = 0
    for col_name in columns_to_remove:
        try:
            conn.execute(text(f"ALTER TABLE routes DROP COLUMN IF EXISTS {col_name}"))
            print(f"➖ Removed column '{col_name}'")
            removed_count += 1
        except Exception as e:
            print(f"⚠️ Failed to remove '{col_name}': {e}")
    
    print(f"\n🗑️ Removed {removed_count} columns")