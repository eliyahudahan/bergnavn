"""safe add ports and voyage_legs foreign keys

Revision ID: a2668fb2c079
Revises: 5c1c13b2b6b7
Create Date: 2025-06-30 15:17:58.062147

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import Integer, String

# revision identifiers, used by Alembic.
revision = 'a2668fb2c079'
down_revision = '5c1c13b2b6b7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. הוסף עמודות חדשות nullable=True
    op.add_column('voyage_legs', sa.Column('departure_port_id', sa.Integer(), nullable=True))
    op.add_column('voyage_legs', sa.Column('arrival_port_id', sa.Integer(), nullable=True))

    # 2. טבלאות זמניות לעבודה עם נתונים
    voyage_legs = table('voyage_legs',
                        column('id', Integer),
                        column('departure_port', String),
                        column('arrival_port', String),
                        column('departure_port_id', Integer),
                        column('arrival_port_id', Integer))

    ports = table('ports',
                  column('id', Integer),
                  column('name', String),
                  column('country', String))

    connection = op.get_bind()

    # 3. טען את כל השורות מ-voyage_legs
    results = connection.execute(sa.select([
        voyage_legs.c.id,
        voyage_legs.c.departure_port,
        voyage_legs.c.arrival_port
    ])).fetchall()

    # 4. עבור כל שורה, חפש את המזהים של הנמלים בטבלה ports והכנס אותם לעמודות החדשות
    for row in results:
        dep_port_id = connection.execute(
            sa.select([ports.c.id]).where(ports.c.name == row.departure_port)
        ).scalar()

        arr_port_id = connection.execute(
            sa.select([ports.c.id]).where(ports.c.name == row.arrival_port)
        ).scalar()

        connection.execute(
            voyage_legs.update().where(voyage_legs.c.id == row.id).values(
                departure_port_id=dep_port_id,
                arrival_port_id=arr_port_id
            )
        )

    # 5. אחרי מילוי הערכים - הורד את העמודות הישנות
    op.drop_column('voyage_legs', 'departure_port')
    op.drop_column('voyage_legs', 'arrival_port')

    # 6. שנה את העמודות החדשות ל-not nullable
    op.alter_column('voyage_legs', 'departure_port_id', nullable=False)
    op.alter_column('voyage_legs', 'arrival_port_id', nullable=False)

    # 7. צור מפתחות זרים בטוחים בין voyage_legs ל-ports
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['departure_port_id'], ['id'])
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['arrival_port_id'], ['id'])

    # 8. עדכן את המגבלה הייחודית בטבלה ports לשם + מדינה
    op.drop_constraint('ports_name_key', 'ports', type_='unique')
    op.create_unique_constraint('uq_port_name_country', 'ports', ['name', 'country'])


def downgrade():
    # היפוך של השינויים

    # 1. הורד את המגבלה הייחודית החדשה, החזר למגבלה הישנה
    op.drop_constraint('uq_port_name_country', 'ports', type_='unique')
    op.create_unique_constraint('ports_name_key', 'ports', ['name'])

    # 2. הורד את מפתחות הזרות
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')

    # 3. הפוך את העמודות ל-nullable
    op.alter_column('voyage_legs', 'arrival_port_id', nullable=True)
    op.alter_column('voyage_legs', 'departure_port_id', nullable=True)

    # 4. הוסף בחזרה את העמודות departure_port ו-arrival_port
    op.add_column('voyage_legs', sa.Column('arrival_port', sa.VARCHAR(length=100), nullable=False))
    op.add_column('voyage_legs', sa.Column('departure_port', sa.VARCHAR(length=100), nullable=False))

    # 5. הסר את העמודות החדשות
    op.drop_column('voyage_legs', 'arrival_port_id')
    op.drop_column('voyage_legs', 'departure_port_id')

