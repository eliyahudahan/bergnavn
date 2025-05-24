
"""Add cleaned_title to cruises

Revision ID: dbc244ec5744
Revises: 453d5441d5c5
Create Date: 2025-05-22 08:50:43.389170
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'dbc244ec5744'
down_revision = '453d5441d5c5'
branch_labels = None
depends_on = None

def upgrade():
    # Add new column
    op.add_column('cruises', sa.Column('cleaned_title', sa.Text(), nullable=True))

    # Clean titles using SQL
    conn = op.get_bind()

    # Step 1: Basic capitalization
    conn.execute(text("""
        UPDATE cruises
        SET cleaned_title = INITCAP(title);
    """))

    # Step 2: Number duplicates
    conn.execute(text("""
        WITH ranked AS (
            SELECT id, cleaned_title,
                ROW_NUMBER() OVER (PARTITION BY cleaned_title ORDER BY id) AS rn
            FROM cruises
        )
        UPDATE cruises
        SET cleaned_title = ranked.cleaned_title || ' #' || ranked.rn
        FROM ranked
        WHERE cruises.id = ranked.id AND ranked.rn > 1;
    """))


def downgrade():
    # Remove the cleaned_title column
    op.drop_column('cruises', 'cleaned_title')
