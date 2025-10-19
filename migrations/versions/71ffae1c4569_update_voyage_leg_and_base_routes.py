"""update voyage_leg and base_routes safely

Revision ID: 71ffae1c4569
Revises: a9200514a6ca
Create Date: 2025-10-19 14:00:35.460993
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '71ffae1c4569'
down_revision = 'a9200514a6ca'
branch_labels = None
depends_on = None

# ---------- Utility helper ----------
def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return column_name in [col['name'] for col in inspector.get_columns(table_name)]

def fk_exists(table_name: str, fk_name: str) -> bool:
    """Check if a foreign key constraint exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return fk_name in [fk['name'] for fk in inspector.get_foreign_keys(table_name)]


# ---------- Upgrade ----------
def upgrade():
    conn = op.get_bind()

    # --- VoyageLeg table ---
    with op.batch_alter_table('voyage_legs') as batch_op:
        # Add columns only if missing
        if not column_exists('voyage_legs', 'departure_port_id'):
            batch_op.add_column(sa.Column('departure_port_id', sa.Integer(), nullable=True))
        if not column_exists('voyage_legs', 'arrival_port_id'):
            batch_op.add_column(sa.Column('arrival_port_id', sa.Integer(), nullable=True))
        if not column_exists('voyage_legs', 'leg_order'):
            batch_op.add_column(sa.Column('leg_order', sa.Integer(), nullable=False, server_default='1'))
        if not column_exists('voyage_legs', 'is_active'):
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))

        # Add foreign keys safely
        if not fk_exists('voyage_legs', 'voyage_legs_departure_port_id_fkey'):
            batch_op.create_foreign_key('voyage_legs_departure_port_id_fkey', 'ports', ['departure_port_id'], ['id'], ondelete='SET NULL')
        if not fk_exists('voyage_legs', 'voyage_legs_arrival_port_id_fkey'):
            batch_op.create_foreign_key('voyage_legs_arrival_port_id_fkey', 'ports', ['arrival_port_id'], ['id'], ondelete='SET NULL')

    # --- BaseRoutes table ---
    with op.batch_alter_table('base_routes') as batch_op:
        if not column_exists('base_routes', 'is_multi_stop'):
            batch_op.add_column(sa.Column('is_multi_stop', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        if not column_exists('base_routes', 'last_updated'):
            batch_op.add_column(sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))

    # --- RouteFiles table ---
    with op.batch_alter_table('route_files') as batch_op:
        if not column_exists('route_files', 'file_type'):
            batch_op.add_column(sa.Column('file_type', sa.String(length=50), nullable=True))


# ---------- Downgrade ----------
def downgrade():
    with op.batch_alter_table('voyage_legs') as batch_op:
        for col in ['is_active', 'leg_order', 'arrival_port_id', 'departure_port_id']:
            if column_exists('voyage_legs', col):
                batch_op.drop_column(col)

    with op.batch_alter_table('base_routes') as batch_op:
        for col in ['last_updated', 'is_multi_stop']:
            if column_exists('base_routes', col):
                batch_op.drop_column(col)

    with op.batch_alter_table('route_files') as batch_op:
        if column_exists('route_files', 'file_type'):
            batch_op.drop_column('file_type')
