"""Add RTZ columns to routes table - EXACT update (with safety checks)

Adds ONLY the missing RTZ columns from the Route model.
Checks if columns exist before adding them.

Revision ID: 1ee0ff605ab8
Revises: 3652ea3139e5
Create Date: 2025-12-25 17:03:46.104515
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1ee0ff605ab8'
down_revision = '3652ea3139e5'
branch_labels = None
depends_on = None


def upgrade():
    """Add ONLY the missing RTZ columns to the existing routes table."""
    
    # Get the current table structure
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('routes')]
    
    print(f"Existing columns in routes: {existing_columns}")
    
    # Add only columns that don't exist
    if 'source' not in existing_columns:
        print("Adding column: source")
        op.add_column('routes', sa.Column('source', sa.String(length=50), 
                                          nullable=True, 
                                          server_default='NCA'))
    
    if 'rtz_filename' not in existing_columns:
        print("Adding column: rtz_filename")
        op.add_column('routes', sa.Column('rtz_filename', sa.String(length=255), 
                                          nullable=True))
    
    if 'waypoint_count' not in existing_columns:
        print("Adding column: waypoint_count")
        op.add_column('routes', sa.Column('waypoint_count', sa.Integer(), 
                                          nullable=True, 
                                          server_default='0'))
    
    if 'rtz_file_hash' not in existing_columns:
        print("Adding column: rtz_file_hash")
        op.add_column('routes', sa.Column('rtz_file_hash', sa.String(length=64), 
                                          nullable=True))
    
    if 'vessel_draft_min' not in existing_columns:
        print("Adding column: vessel_draft_min")
        op.add_column('routes', sa.Column('vessel_draft_min', sa.Float(), 
                                          nullable=True))
    
    if 'vessel_draft_max' not in existing_columns:
        print("Adding column: vessel_draft_max")
        op.add_column('routes', sa.Column('vessel_draft_max', sa.Float(), 
                                          nullable=True))
    
    if 'created_at' not in existing_columns:
        print("Adding column: created_at")
        op.add_column('routes', sa.Column('created_at', sa.DateTime(), 
                                          nullable=True,
                                          server_default=sa.text('CURRENT_TIMESTAMP')))
    
    if 'updated_at' not in existing_columns:
        print("Adding column: updated_at")
        op.add_column('routes', sa.Column('updated_at', sa.DateTime(), 
                                          nullable=True,
                                          server_default=sa.text('CURRENT_TIMESTAMP')))
    
    if 'parsed_at' not in existing_columns:
        print("Adding column: parsed_at")
        op.add_column('routes', sa.Column('parsed_at', sa.DateTime(), 
                                          nullable=True))


def downgrade():
    """Remove ONLY the RTZ columns we added (if they exist)."""
    
    # Get the current table structure
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('routes')]
    
    # Remove only columns that exist
    if 'parsed_at' in existing_columns:
        op.drop_column('routes', 'parsed_at')
    
    if 'updated_at' in existing_columns:
        op.drop_column('routes', 'updated_at')
    
    if 'created_at' in existing_columns:
        op.drop_column('routes', 'created_at')
    
    if 'vessel_draft_max' in existing_columns:
        op.drop_column('routes', 'vessel_draft_max')
    
    if 'vessel_draft_min' in existing_columns:
        op.drop_column('routes', 'vessel_draft_min')
    
    if 'rtz_file_hash' in existing_columns:
        op.drop_column('routes', 'rtz_file_hash')
    
    if 'waypoint_count' in existing_columns:
        op.drop_column('routes', 'waypoint_count')
    
    if 'rtz_filename' in existing_columns:
        op.drop_column('routes', 'rtz_filename')
    
    if 'source' in existing_columns:
        op.drop_column('routes', 'source')