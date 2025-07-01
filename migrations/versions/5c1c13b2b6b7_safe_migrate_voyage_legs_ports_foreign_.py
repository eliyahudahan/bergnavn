"""safe migrate voyage_legs ports foreign keys

Revision ID: 5c1c13b2b6b7
Revises: 43f4e680661d
Create Date: 2025-06-30 15:13:44.428518

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c1c13b2b6b7'
down_revision = '43f4e680661d'
branch_labels = None
depends_on = None


def upgrade():
    # הוספת עמודות חדשות nullable
    op.add_column('voyage_legs', sa.Column('departure_port_id', sa.Integer(), nullable=True))
    op.add_column('voyage_legs', sa.Column('arrival_port_id', sa.Integer(), nullable=True))

    # יצירת מפתחות זרים
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['departure_port_id'], ['id'])
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['arrival_port_id'], ['id'])

    # עדכון הערכים החדשים לפי הטקסט הקיים
    conn = op.get_bind()
    conn.execute("""
    UPDATE voyage_legs vl
    SET departure_port_id = p1.id,
        arrival_port_id = p2.id
    FROM ports p1, ports p2
    WHERE vl.departure_port = p1.name AND vl.arrival_port = p2.name;
    """)

    # שינוי עמודות ל-NOT NULL
    op.alter_column('voyage_legs', 'departure_port_id', nullable=False)
    op.alter_column('voyage_legs', 'arrival_port_id', nullable=False)

    # מחיקת העמודות הישנות
    op.drop_column('voyage_legs', 'departure_port')
    op.drop_column('voyage_legs', 'arrival_port')


def downgrade():
    # הוספת העמודות הישנות בחזרה
    op.add_column('voyage_legs', sa.Column('departure_port', sa.String(length=100), nullable=False))
    op.add_column('voyage_legs', sa.Column('arrival_port', sa.String(length=100), nullable=False))

    # הסרת מפתחות זרים והעמודות החדשות
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_column('voyage_legs', 'departure_port_id')
    op.drop_column('voyage_legs', 'arrival_port_id')

