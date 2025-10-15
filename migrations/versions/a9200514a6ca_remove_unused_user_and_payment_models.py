"""Remove unused user and payment models

Revision ID: a9200514a6ca
Revises: 968f83e64475
Create Date: 2025-10-09 13:46:52.036561
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a9200514a6ca'
down_revision = '968f83e64475'
branch_labels = None
depends_on = None


def upgrade():
    # Drop dependent tables in the correct order
    op.drop_table('payments')
    op.drop_table('bookings')
    op.drop_table('users')


def downgrade():
    # Recreate the dropped tables if rollback is needed
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(150), nullable=False, unique=True),
        sa.Column('email', sa.String(120), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(200), nullable=False, default=''),
        sa.Column('date_created', sa.DateTime(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
    )

    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('cruise_id', sa.Integer(), nullable=False),
        sa.Column('num_of_people', sa.Integer(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('booking_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['cruise_id'], ['cruises.id']),
    )

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id']),
    )
