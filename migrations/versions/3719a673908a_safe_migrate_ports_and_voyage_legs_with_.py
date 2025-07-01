"""safe migrate ports and voyage_legs with defaults

Revision ID: <הערך שמופיע בראש הקובץ>
Revises: af55ca751c7c  # או המזהה שקיבלת בשלב 1
Create Date: 2025-06-30  # התאריך הנוכחי

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import Integer, String

# revision identifiers, used by Alembic.
revision = '3719a673908a'
down_revision = 'af55ca751c7c'  # עדכן לפי HEAD שלך
branch_labels = None
depends_on = None


def upgrade():
    # 1. הוסף עמודות חדשות כ- nullable זמנית
    op.add_column('voyage_legs', sa.Column('departure_port_id', sa.Integer(), nullable=True))
    op.add_column('voyage_legs', sa.Column('arrival_port_id', sa.Integer(), nullable=True))

    # 2. טען טבלה זמנית לגישה לנתונים
    voyage_legs = table('voyage_legs',
                       column('id', Integer),
                       column('departure_port', String),
                       column('arrival_port', String),
                       column('departure_port_id', Integer),
                       column('arrival_port_id', Integer),
    )

    # 3. מלא את הערכים החדשים בעזרת SQL - כאן תכתוב SQL שממפה את departure_port ו-arrival_port ל-IDs של הטבלה ports
    op.execute("""
        UPDATE voyage_legs vl
        SET departure_port_id = p1.id
        FROM ports p1
        WHERE vl.departure_port = p1.name
    """)
    op.execute("""
        UPDATE voyage_legs vl
        SET arrival_port_id = p2.id
        FROM ports p2
        WHERE vl.arrival_port = p2.name
    """)

    # 4. אחרי שמילאת את הערכים - הפוך את העמודות ל NOT NULL
    op.alter_column('voyage_legs', 'departure_port_id', nullable=False)
    op.alter_column('voyage_legs', 'arrival_port_id', nullable=False)

    # 5. צור foreign keys
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['departure_port_id'], ['id'])
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['arrival_port_id'], ['id'])

    # 6. מחק את העמודות הישנות של שמות הנמלים
    op.drop_column('voyage_legs', 'departure_port')
    op.drop_column('voyage_legs', 'arrival_port')


def downgrade():
    # מחזיר עמודות שמות הנמלים
    op.add_column('voyage_legs', sa.Column('departure_port', sa.String(length=100), nullable=False))
    op.add_column('voyage_legs', sa.Column('arrival_port', sa.String(length=100), nullable=False))

    # מחיקת foreign keys ועמודות id החדשות
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_column('voyage_legs', 'departure_port_id')
    op.drop_column('voyage_legs', 'arrival_port_id')


    # כאן אפשר להוסיף לוגיקה להחזיר את הערכים של departure_port ו-arrival_port אם רוצים



