import logging
import os
import sys
from logging.config import fileConfig

from alembic import context
from flask import current_app

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app  # Flask factory method

# Alembic Config object
config = context.config

# Setup logging - load config from root alembic.ini
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ini_path = os.path.join(root_dir, 'alembic.ini')
fileConfig(ini_path)
logger = logging.getLogger('alembic.env')

# Create Flask app and load models
app = create_app()


def get_engine_url():
    """
    Retrieve the database URL from Flask-Migrate's extension.
    """
    db_ext = current_app.extensions['migrate']
    return db_ext.db.engine.url.render_as_string(hide_password=False).replace('%', '%%')


def get_metadata():
    """
    Retrieve SQLAlchemy metadata for autogenerate.
    """
    db_ext = current_app.extensions['migrate']
    return db_ext.db.metadata


# List of PostGIS system tables we want Alembic to ignore
EXCLUDE_TABLES = {"spatial_ref_sys", "geometry_columns", "geography_columns", "raster_columns", "raster_overviews"}


def include_object(object, name, type_, reflected, compare_to):
    """
    Hook for Alembic's autogenerate to decide which objects to include.
    We skip PostGIS internal tables.
    """
    if type_ == "table" and name in EXCLUDE_TABLES:
        return False
    return True


with app.app_context():
    # Override URL from alembic.ini
    config.set_main_option('sqlalchemy.url', get_engine_url())

    def run_migrations_offline():
        """
        Run migrations in 'offline' mode.
        """
        url = config.get_main_option('sqlalchemy.url')
        context.configure(
            url=url,
            target_metadata=get_metadata(),
            literal_binds=True,
            include_object=include_object,  # prevent PostGIS deletion
        )
        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online():
        """
        Run migrations in 'online' mode.
        """
        def process_revision_directives(context, revision, directives):
            if getattr(config.cmd_opts, 'autogenerate', False):
                script = directives[0]
                if script.upgrade_ops.is_empty():
                    directives[:] = []
                    logger.info('No schema changes detected.')

        db_ext = current_app.extensions['migrate']
        connectable = db_ext.db.engine
        conf_args = db_ext.configure_args
        if conf_args.get('process_revision_directives') is None:
            conf_args['process_revision_directives'] = process_revision_directives

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=get_metadata(),
                include_object=include_object,  # prevent PostGIS deletion
                **conf_args
            )
            with context.begin_transaction():
                context.run_migrations()

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
