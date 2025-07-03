"""Add route_id to voyage_legs

Revision ID: 4fc5d623bb68
Revises: dff0bc311b7c
Create Date: 2025-07-02 14:51:54.539739
"""
from alembic import op
import sqlalchemy as sa

revision = '4fc5d623bb68'
down_revision = 'dff0bc311b7c'
branch_labels = None
depends_on = None


def upgrade():
    # מוסיפים את העמודה route_id (nullable=True כדי לא לשבור קיום נתונים)
    op.add_column('voyage_legs', sa.Column('route_id', sa.Integer(), nullable=True))
    # יוצרים מפתח זר בשם ברור
    op.create_foreign_key(
        'fk_voyage_legs_route_id',
        'voyage_legs',
        'routes',
        ['route_id'],
        ['id']
    )


def downgrade():
    # מסירים את המפתח הזר
    op.drop_constraint('fk_voyage_legs_route_id', 'voyage_legs', type_='foreignkey')
    # מסירים את העמודה
    op.drop_column('voyage_legs', 'route_id')

