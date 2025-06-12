"""עדכון מיגרציה - שמירת טבלת payments ושינויים ב-voyage_legs

Revision ID: 0b4f4042af4f
Revises: 6a6bc2167b89
Create Date: 2025-06-08 15:25:31.590919

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0b4f4042af4f'
down_revision = '6a6bc2167b89'
branch_labels = None
depends_on = None


def upgrade():
    # שינויים קיימים, בלי למחוק את טבלת payments
    op.drop_table('cruises_backup')
    op.drop_constraint('cruises_location_id_fkey', 'cruises', type_='foreignkey')
    op.drop_column('cruises', 'cleaned_title')
    op.drop_column('cruises', 'location_id')
    op.alter_column('locations', 'name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               nullable=False)
    op.alter_column('locations', 'country',
               existing_type=sa.TEXT(),
               type_=sa.String(length=50),
               existing_nullable=True)
    op.drop_constraint('locations_name_key', 'locations', type_='unique')
    op.drop_column('locations', 'lon')
    op.drop_column('locations', 'lat')
    op.add_column('route_legs', sa.Column('leg_order', sa.Integer(), nullable=True))
    op.drop_column('route_legs', 'order')
    # אין שינויים לטבלת payments - נשארת כפי שהיא


def downgrade():
    # החזרת שינויים עם שמירת payments כפי שהיא
    op.add_column('route_legs', sa.Column('order', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('route_legs', 'leg_order')
    op.add_column('locations', sa.Column('lat', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('locations', sa.Column('lon', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.create_unique_constraint('locations_name_key', 'locations', ['name'])
    op.alter_column('locations', 'country',
               existing_type=sa.String(length=50),
               type_=sa.TEXT(),
               existing_nullable=True)
    op.alter_column('locations', 'name',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               nullable=True)
    op.add_column('cruises', sa.Column('location_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('cruises', sa.Column('cleaned_title', sa.TEXT(), autoincrement=False, nullable=True))
    op.create_foreign_key('cruises_location_id_fkey', 'cruises', 'locations', ['location_id'], ['id'])
    op.create_table('cruises_backup',
        sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('departure_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('title', sa.VARCHAR(length=150), autoincrement=False, nullable=True),
        sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column('return_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('origin', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column('destination', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column('origin_lat', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column('origin_lon', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column('capacity', sa.INTEGER(), autoincrement=False, nullable=True)
    )
    # טבלת payments לא מוחזרת ולא נוצרת מחדש - נשארת בשלמותה

