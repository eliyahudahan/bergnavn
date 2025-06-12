"""  
Remove user_id and cruise_id columns from payments  
Add booking_id foreign key to payments for linking to bookings  

Revision ID: 8a9851ba6148  
Revises: aa24f01c8ce5  
Create Date: 2025-06-11 14:17:57.580359  

---

Upgrade:  
- Add booking_id column (foreign key to bookings.id)  
- Drop foreign key constraints for user_id and cruise_id  
- Remove user_id and cruise_id columns  

Downgrade:  
- Add back user_id and cruise_id columns with foreign keys  
- Remove booking_id column and its foreign key constraint  
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8a9851ba6148'
down_revision = 'aa24f01c8ce5'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add booking_id column (not nullable)
    op.add_column('payments', sa.Column('booking_id', sa.Integer(), nullable=False))

    # 2. Create foreign key constraint payments.booking_id -> bookings.id
    op.create_foreign_key(
        constraint_name=None,  # Alembic יווצר שם אוטומטי, אפשר לשנות אם רוצים
        source_table='payments',
        referent_table='bookings',
        local_cols=['booking_id'],
        remote_cols=['id']
    )

    # 3. Drop old foreign keys (user_id, cruise_id)
    op.drop_constraint('fk_payments_cruise', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_user', 'payments', type_='foreignkey')

    # 4. Drop old columns user_id, cruise_id
    op.drop_column('payments', 'user_id')
    op.drop_column('payments', 'cruise_id')


def downgrade():
    # 1. Add back user_id and cruise_id columns
    op.add_column('payments', sa.Column('user_id', sa.INTEGER(), nullable=False))
    op.add_column('payments', sa.Column('cruise_id', sa.INTEGER(), nullable=True))

    # 2. Re-create foreign key constraints for user_id and cruise_id
    op.create_foreign_key(
        'fk_payments_user',
        'payments',
        'users',
        ['user_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_payments_cruise',
        'payments',
        'cruises',
        ['cruise_id'],
        ['id']
    )

    # 3. Drop foreign key for booking_id and remove the column
    op.drop_constraint(None, 'payments', type_='foreignkey')  # drop FK for booking_id
    op.drop_column('payments', 'booking_id')

