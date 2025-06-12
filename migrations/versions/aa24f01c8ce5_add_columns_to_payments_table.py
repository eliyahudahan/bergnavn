"""Add columns to existing payments table

Revision ID: aa24f01c8ce5
Revises: 0b4f4042af4f
Create Date: 2025-06-10 15:31:14.646396
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa24f01c8ce5'
down_revision = '0b4f4042af4f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('payments', sa.Column('amount', sa.Float(), nullable=False))
    op.add_column('payments', sa.Column('user_id', sa.Integer(), nullable=False))
    op.add_column('payments', sa.Column('cruise_id', sa.Integer(), nullable=True))
    op.add_column('payments', sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()))

    op.create_foreign_key('fk_payments_user', 'payments', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_payments_cruise', 'payments', 'cruises', ['cruise_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_payments_user', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_cruise', 'payments', type_='foreignkey')

    op.drop_column('payments', 'timestamp')
    op.drop_column('payments', 'cruise_id')
    op.drop_column('payments', 'user_id')
    op.drop_column('payments', 'amount')

