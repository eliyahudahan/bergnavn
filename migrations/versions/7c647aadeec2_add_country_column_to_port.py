"""Add country column to ports with default value

Revision ID: 7c647aadeec2
Revises: 7dcdbb4940dc
Create Date: 2025-05-27 14:24:42.754881
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c647aadeec2'
down_revision = '7dcdbb4940dc'
branch_labels = None
depends_on = None


def upgrade():
    # מוסיפים עמודה עם ערך ברירת מחדל 'Unknown' כדי לאפשר הוספה בטוחה
    op.add_column('ports', sa.Column('country', sa.String(length=100), nullable=False, server_default='Unknown'))
    
    # לאחר הוספת העמודה עם ברירת מחדל, ניתן להסיר את ברירת המחדל כדי למנוע הכנסת ערך אוטומטי בעתיד (רצוי)
    op.alter_column('ports', 'country', server_default=None)


def downgrade():
    # במקרה של downgrade מסירים את העמודה שהוספנו
    op.drop_column('ports', 'country')


