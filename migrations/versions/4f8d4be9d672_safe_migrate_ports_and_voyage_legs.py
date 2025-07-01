"""safe migrate ports and voyage_legs

Revision ID: 4f8d4be9d672
Revises: 43f4e680661d
Create Date: 2025-06-30 15:21:44.733469

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4f8d4be9d672'
down_revision = '43f4e680661d'
branch_labels = None
depends_on = None


def upgrade():
    # 1. הוסף עמודות חדשות nullable
    op.add_column('voyage_legs', sa.Column('departure_port_id', sa.Integer(), nullable=True))
    op.add_column('voyage_legs', sa.Column('arrival_port_id', sa.Integer(), nullable=True))

    # 2. שנה מפתח ייחודי בports (name בלבד -> name+country)
    op.drop_constraint('ports_name_key', 'ports', type_='unique')
    op.create_unique_constraint('uq_port_name_country', 'ports', ['name', 'country'])

    # 3. עדכן את הערכים בעמודות החדשות לפי העמודות הישנות
    conn = op.get_bind()
    conn.execute("""
        UPDATE voyage_legs vl
        SET departure_port_id = p1.id,
            arrival_port_id = p2.id
        FROM ports p1, ports p2
        WHERE vl.departure_port = p1.name
          AND vl.arrival_port = p2.name
    """)

    # 4. הפוך את העמודות החדשות ל-NOT NULL
    op.alter_column('voyage_legs', 'departure_port_id', nullable=False)
    op.alter_column('voyage_legs', 'arrival_port_id', nullable=False)

    # 5. הוסף מפתחות זרים
    op.create_foreign_key(
        'fk_voyage_legs_departure_port_id_ports',
        'voyage_legs',
        'ports',
        ['departure_port_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_voyage_legs_arrival_port_id_ports',
        'voyage_legs',
        'ports',
        ['arrival_port_id'],
        ['id']
    )

    # 6. מחק את העמודות הישנות (טקסט)
    op.drop_column('voyage_legs', 'departure_port')
    op.drop_column('voyage_legs', 'arrival_port')


def downgrade():
    # הוסף את העמודות הישנות מחדש
    op.add_column('voyage_legs', sa.Column('departure_port', sa.String(length=100), nullable=False))
    op.add_column('voyage_legs', sa.Column('arrival_port', sa.String(length=100), nullable=False))

    # העתק את הנתונים מהעמודות החדשות לעמודות הישנות
    conn = op.get_bind()
    conn.execute("""
        UPDATE voyage_legs vl
        SET departure_port = p1.name,
            arrival_port = p2.name
        FROM ports p1, ports p2
        WHERE vl.departure_port_id = p1.id
          AND vl.arrival_port_id = p2.id
    """)

    # מחק את המפתחות הזרות
    op.drop_constraint('fk_voyage_legs_departure_port_id_ports', 'voyage_legs', type_='foreignkey')
    op.drop_constraint('fk_voyage_legs_arrival_port_id_ports', 'voyage_legs', type_='foreignkey')

    # מחק את העמודות החדשות
    op.drop_column('voyage_legs', 'departure_port_id')
    op.drop_column('voyage_legs', 'arrival_port_id')

    # החזר את המפתח הייחודי לname בלבד בטבלת ports
    op.drop_constraint('uq_port_name_country', 'ports', type_='unique')
    op.create_unique_constraint('ports_name_key', 'ports', ['name'])


