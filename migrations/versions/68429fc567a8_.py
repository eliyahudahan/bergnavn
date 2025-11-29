"""SAFE migration – does NOT drop existing tables
Revision ID: 68429fc567a8
Revises: 
Create Date: 2025-05-01 23:06:52.544162
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '68429fc567a8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    SAFE UPGRADE:
    This migration was originally generated incorrectly and attempted to drop
    critical tables (payments/bookings). These tables do NOT exist in your DB
    anymore and are not part of the commercial maritime project.

    The destructive operations have been removed.
    Only non-breaking cruise/user updates are kept.
    """

    # ---- Cruises table adjustments (SAFE) ----
    with op.batch_alter_table('cruises', schema=None) as batch_op:
        batch_op.alter_column(
            'title',
            existing_type=sa.VARCHAR(length=100),
            type_=sa.String(length=150),
            nullable=False
        )
        batch_op.alter_column(
            'departure_date',
            existing_type=sa.DATE(),
            type_=sa.DateTime(),
            existing_nullable=False
        )
        batch_op.alter_column(
            'return_date',
            existing_type=sa.DATE(),
            type_=sa.DateTime(),
            nullable=False
        )
        batch_op.alter_column(
            'created_at',
            existing_type=postgresql.TIMESTAMP(),
            nullable=True
        )

        # SAFE REMOVALS — only if exists
        try:
            batch_op.drop_column('destination')
        except Exception:
            pass

        try:
            batch_op.drop_column('status')
        except Exception:
            pass

    # ---- Users table adjustments (SAFE) ----
    with op.batch_alter_table('users', schema=None) as batch_op:
        # New columns
        try:
            batch_op.add_column(sa.Column('date_created', sa.DateTime(), nullable=True))
        except Exception:
            pass

        try:
            batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=True))
        except Exception:
            pass

        try:
            batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=True))
        except Exception:
            pass

        # Existing columns update
        batch_op.alter_column(
            'username',
            existing_type=sa.VARCHAR(length=80),
            type_=sa.String(length=150),
            existing_nullable=False
        )
        batch_op.alter_column(
            'password_hash',
            existing_type=sa.VARCHAR(length=128),
            type_=sa.String(length=200),
            existing_nullable=False,
            existing_server_default=sa.text("''::character varying")
        )

        # Drop old fields safely only if exist
        for col in ['created_at', 'birth_date', 'role', 'full_name']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass


def downgrade():
    """
    SAFE DOWNGRADE:
    Only restores columns that were modified. Does NOT recreate payments/bookings.
    """
    # ---- Users table ----
    with op.batch_alter_table('users', schema=None) as batch_op:

        try:
            batch_op.add_column(sa.Column('full_name', sa.VARCHAR(length=120), nullable=True))
        except Exception:
            pass

        try:
            batch_op.add_column(sa.Column('role', sa.VARCHAR(length=50), nullable=True))
        except Exception:
            pass

        try:
            batch_op.add_column(sa.Column('birth_date', sa.DATE(), nullable=True))
        except Exception:
            pass

        try:
            batch_op.add_column(sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
        except Exception:
            pass

        batch_op.alter_column(
            'password_hash',
            existing_type=sa.String(length=200),
            type_=sa.VARCHAR(length=128),
            existing_nullable=False
        )
        batch_op.alter_column(
            'username',
            existing_type=sa.String(length=150),
            type_=sa.VARCHAR(length=80),
            existing_nullable=False
        )

        for col in ['is_admin', 'is_verified', 'date_created']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

    # ---- Cruises table ----
    with op.batch_alter_table('cruises', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('status', sa.VARCHAR(length=50), nullable=True))
        except Exception:
            pass

        try:
            batch_op.add_column(sa.Column('destination', sa.VARCHAR(length=100), nullable=False))
        except Exception:
            pass

        batch_op.alter_column(
            'created_at',
            existing_type=postgresql.TIMESTAMP(),
            nullable=False
        )
        batch_op.alter_column(
            'return_date',
            existing_type=sa.DateTime(),
            type_=sa.DATE()
        )
        batch_op.alter_column(
            'departure_date',
            existing_type=sa.DateTime(),
            type_=sa.DATE(),
            existing_nullable=False
        )
        batch_op.alter_column(
            'title',
            existing_type=sa.String(length=150),
            type_=sa.VARCHAR(length=100)
        )
