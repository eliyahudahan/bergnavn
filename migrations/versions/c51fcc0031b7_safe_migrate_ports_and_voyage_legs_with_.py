"""safe migrate ports and voyage_legs with defaults

Revision ID: c51fcc0031b7
Revises: aebb30329dab
Create Date: 2025-07-01 13:49:01.435433

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import Integer, String


# revision identifiers, used by Alembic.
revision = 'c51fcc0031b7'
down_revision = 'aebb30329dab'
branch_labels = None
depends_on = None


def upgrade():
    # 1. הוסף עמודות חדשות כ- nullable זמנית
    op.add_column('voyage_legs', sa.Column('departure_port_id', sa.Integer(), nullable=True))
    op.add_column('voyage_legs', sa.Column('arrival_port_id', sa.Integer(), nullable=True))

    # 2. טבלה זמנית לגישה לשדות
    voyage_legs = table('voyage_legs',
                       column('id', Integer),
                       column('departure_port', String),
                       column('arrival_port', String),
                       column('departure_port_id', Integer),
                       column('arrival_port_id', Integer),
    )

    # 3. עדכון הערכים החדשים עם מיפוי לשמות נמלים שקיימים בטבלת ports
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

    # 4. הפוך את העמודות ל-NOT NULL לאחר מילוי הערכים
    op.alter_column('voyage_legs', 'departure_port_id', nullable=False)
    op.alter_column('voyage_legs', 'arrival_port_id', nullable=False)

    # 5. יצירת foreign keys בין voyage_legs ל ports
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['departure_port_id'], ['id'])
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['arrival_port_id'], ['id'])

    # 6. מחיקת העמודות הישנות של שמות הנמלים
    op.drop_column('voyage_legs', 'departure_port')
    op.drop_column('voyage_legs', 'arrival_port')


def downgrade():
    # הוספת עמודות שמות הנמלים מחדש
    op.add_column('voyage_legs', sa.Column('departure_port', sa.String(length=100), nullable=False))
    op.add_column('voyage_legs', sa.Column('arrival_port', sa.String(length=100), nullable=False))

    # מחיקת מפתחות זרים ועמודות ה-id החדשות
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_column('voyage_legs', 'departure_port_id')
    op.drop_column('voyage_legs', 'arrival_port_id')

    # במידת הצורך, אפשר להוסיף לוגיקה להחזרת ערכי שמות נמלים מהמזהים - כרגע לא חובה

