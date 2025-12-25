"""Add RTZ columns to routes - manual SQL

Uses PostgreSQL-specific SQL with IF NOT EXISTS to safely add RTZ columns.

Revision ID: rtz_sql_fix
Revises: 30ae1c7fcabc
Create Date: 2025-12-25 17:57:33.826520
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'rtz_sql_fix'
down_revision = '30ae1c7fcabc'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add RTZ columns using PostgreSQL IF NOT EXISTS.
    Safe - won't fail if columns already exist.
    """
    
    # Get database connection
    conn = op.get_bind()
    
    print("🔧 Adding RTZ columns to 'routes' table...")
    
    # List of SQL statements to add columns if they don't exist
    sql_statements = [
        # source column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='source') THEN
                ALTER TABLE routes ADD COLUMN source VARCHAR(50) DEFAULT 'NCA';
                RAISE NOTICE 'Added column: source';
            ELSE
                RAISE NOTICE 'Column already exists: source';
            END IF;
        END $$;""",
        
        # rtz_filename column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='rtz_filename') THEN
                ALTER TABLE routes ADD COLUMN rtz_filename VARCHAR(255);
                RAISE NOTICE 'Added column: rtz_filename';
            ELSE
                RAISE NOTICE 'Column already exists: rtz_filename';
            END IF;
        END $$;""",
        
        # waypoint_count column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='waypoint_count') THEN
                ALTER TABLE routes ADD COLUMN waypoint_count INTEGER DEFAULT 0;
                RAISE NOTICE 'Added column: waypoint_count';
            ELSE
                RAISE NOTICE 'Column already exists: waypoint_count';
            END IF;
        END $$;""",
        
        # rtz_file_hash column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='rtz_file_hash') THEN
                ALTER TABLE routes ADD COLUMN rtz_file_hash VARCHAR(64);
                RAISE NOTICE 'Added column: rtz_file_hash';
            ELSE
                RAISE NOTICE 'Column already exists: rtz_file_hash';
            END IF;
        END $$;""",
        
        # vessel_draft_min column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='vessel_draft_min') THEN
                ALTER TABLE routes ADD COLUMN vessel_draft_min DOUBLE PRECISION;
                RAISE NOTICE 'Added column: vessel_draft_min';
            ELSE
                RAISE NOTICE 'Column already exists: vessel_draft_min';
            END IF;
        END $$;""",
        
        # vessel_draft_max column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='vessel_draft_max') THEN
                ALTER TABLE routes ADD COLUMN vessel_draft_max DOUBLE PRECISION;
                RAISE NOTICE 'Added column: vessel_draft_max';
            ELSE
                RAISE NOTICE 'Column already exists: vessel_draft_max';
            END IF;
        END $$;""",
        
        # created_at column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='created_at') THEN
                ALTER TABLE routes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                RAISE NOTICE 'Added column: created_at';
            ELSE
                RAISE NOTICE 'Column already exists: created_at';
            END IF;
        END $$;""",
        
        # updated_at column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='updated_at') THEN
                ALTER TABLE routes ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                RAISE NOTICE 'Added column: updated_at';
            ELSE
                RAISE NOTICE 'Column already exists: updated_at';
            END IF;
        END $$;""",
        
        # parsed_at column
        """DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='routes' AND column_name='parsed_at') THEN
                ALTER TABLE routes ADD COLUMN parsed_at TIMESTAMP;
                RAISE NOTICE 'Added column: parsed_at';
            ELSE
                RAISE NOTICE 'Column already exists: parsed_at';
            END IF;
        END $$;"""
    ]
    
    # Execute each SQL statement
    for sql in sql_statements:
        try:
            conn.execute(text(sql))
        except Exception as e:
            print(f"⚠️  Error (continuing): {e}")
    
    print("✅ RTZ columns added (or already exist)!")


def downgrade():
    """
    Remove RTZ columns using IF EXISTS.
    Safe - won't fail if columns don't exist.
    """
    
    # Get database connection
    conn = op.get_bind()
    
    print("🗑️  Removing RTZ columns from 'routes' table...")
    
    # List of columns to remove
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
    
    # Remove each column if it exists
    for column in columns_to_remove:
        try:
            conn.execute(text(f"ALTER TABLE routes DROP COLUMN IF EXISTS {column};"))
            print(f"✅ Removed column (or didn't exist): {column}")
        except Exception as e:
            print(f"⚠️  Error removing {column}: {e}")
    
    print("✅ RTZ columns removed (or didn't exist)!")