from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select
from sqlalchemy.orm.session import Session
from sqlalchemy import Integer, String

revision = '3355c0cd0f82'
down_revision = 'af55ca751c7c'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('voyage_legs', sa.Column('departure_port_id', sa.Integer(), nullable=True))
    op.add_column('voyage_legs', sa.Column('arrival_port_id', sa.Integer(), nullable=True))

    voyage_legs = table('voyage_legs',
        column('id', Integer),
        column('departure_port', String),
        column('arrival_port', String),
        column('departure_port_id', Integer),
        column('arrival_port_id', Integer),
    )
    ports = table('ports',
        column('id', Integer),
        column('name', String),
    )

    bind = op.get_bind()
    session = Session(bind=bind)

    legs = session.execute(select([
        voyage_legs.c.id,
        voyage_legs.c.departure_port,
        voyage_legs.c.arrival_port,
    ])).fetchall()

    for leg in legs:
        departure_port_id = session.execute(
            select([ports.c.id])
            .where(ports.c.name == leg.departure_port)
            .limit(1)
        ).scalar()

        arrival_port_id = session.execute(
            select([ports.c.id])
            .where(ports.c.name == leg.arrival_port)
            .limit(1)
        ).scalar()

        session.execute(
            voyage_legs.update()
            .where(voyage_legs.c.id == leg.id)
            .values(departure_port_id=departure_port_id, arrival_port_id=arrival_port_id)
        )
    session.commit()

    op.drop_column('voyage_legs', 'departure_port')
    op.drop_column('voyage_legs', 'arrival_port')

    op.alter_column('voyage_legs', 'departure_port_id', nullable=False)
    op.alter_column('voyage_legs', 'arrival_port_id', nullable=False)

    op.create_foreign_key(None, 'voyage_legs', 'ports', ['departure_port_id'], ['id'])
    op.create_foreign_key(None, 'voyage_legs', 'ports', ['arrival_port_id'], ['id'])

def downgrade():
    op.add_column('voyage_legs', sa.Column('departure_port', sa.String(length=100), nullable=False))
    op.add_column('voyage_legs', sa.Column('arrival_port', sa.String(length=100), nullable=False))

    voyage_legs = table('voyage_legs',
        column('id', Integer),
        column('departure_port', String),
        column('arrival_port', String),
        column('departure_port_id', Integer),
        column('arrival_port_id', Integer),
    )
    ports = table('ports',
        column('id', Integer),
        column('name', String),
    )

    bind = op.get_bind()
    session = Session(bind=bind)

    legs = session.execute(select([
        voyage_legs.c.id,
        voyage_legs.c.departure_port_id,
        voyage_legs.c.arrival_port_id,
    ])).fetchall()

    for leg in legs:
        departure_name = session.execute(
            select([ports.c.name])
            .where(ports.c.id == leg.departure_port_id)
            .limit(1)
        ).scalar()

        arrival_name = session.execute(
            select([ports.c.name])
            .where(ports.c.id == leg.arrival_port_id)
            .limit(1)
        ).scalar()

        session.execute(
            voyage_legs.update()
            .where(voyage_legs.c.id == leg.id)
            .values(departure_port=departure_name, arrival_port=arrival_name)
        )
    session.commit()

    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_constraint(None, 'voyage_legs', type_='foreignkey')
    op.drop_column('voyage_legs', 'departure_port_id')
    op.drop_column('voyage_legs', 'arrival_port_id')
