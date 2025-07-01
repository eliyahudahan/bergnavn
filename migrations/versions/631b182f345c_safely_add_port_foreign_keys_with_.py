"""safely add port foreign keys with defaults

Revision ID: 631b182f345c
Revises: c5c31d9b5b15
Create Date: 2025-07-01 14:17:39.544828
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '631b182f345c'
down_revision = 'c5c31d9b5b15'
branch_labels = None
depends_on = None


def upgrade():
    # שלב א': הוספת העמודות כ-nullable
    op.add_column('voyage_legs', sa.Column('departure_port_id', sa.Integer(), nullable=True))
    op.add_column('voyage_legs', sa.Column('arrival_port_id', sa.Integer(), nullable=True))

    # שלב ב': מילוי ערך ברירת מחדל (ID 7 הוא הפורט הזמני שהכנסת)
    op.execute("UPDATE voyage_legs SET departure_port_id = 7 WHERE departure_port_id IS NULL;")
    op.execute("UPDATE voyage_legs SET arrival_port_id = 7 WHERE arrival_port_id IS NULL;")

    # שלב ג': הפיכת השדות ל- NOT NULL
    op.alter_column('voyage_legs', 'departure_port_id', nullable=False)
    op.alter_column('voyage_legs', 'arrival_port_id', nullable=False)

    # שלב ד': הוספת foreign keys
    op.create_foreign_key(
        'fk_departure_port', 'voyage_legs', 'ports',
        ['departure_port_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_arrival_port', 'voyage_legs', 'ports',
        ['arrival_port_id'], ['id'], ondelete='CASCADE'
    )


def downgrade():
    op.drop_constraint('fk_arrival_port', 'voyage_legs', type_='foreignkey')
    op.drop_constraint('fk_departure_port', 'voyage_legs', type_='foreignkey')
    op.drop_column('voyage_legs', 'arrival_port_id')
    op.drop_column('voyage_legs', 'departure_port_id')

