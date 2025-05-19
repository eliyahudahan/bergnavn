import logging
import sys
import os
from logging.config import fileConfig

from alembic import context
from flask import current_app

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app  # Flask factory method

# Alembic Config Object
config = context.config

# Setup logging from alembic.ini path
alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'alembic.ini')
fileConfig(alembic_ini_path)
logger = logging.getLogger('alembic.env')

def get_engine():
    """Create SQLAlchemy engine from config or Flask app context."""
    from backend.config.config import Config
    from sqlalchemy import create_engine
    try:
        return create_engine(Config.SQLALCHEMY_DATABASE_URI)
    except Exception:
        return current_app.extensions['migrate'].db.engine

def get_engine_url():
    """Return DB URL string, escaping percent signs."""
    try:
        return get_engine().url.render_as_string(hide_password=False).replace('%', '%%')
    except Exception:
        return str(get_engine().url).replace('%', '%%')

def get_metadata():
    """Get metadata from Flask-Migrate extension."""
    db = current_app.extensions['migrate'].db
    return getattr(db, 'metadatas', {None: db.metadata}).get(None)

app = create_app()

with app.app_context():
    # Override sqlalchemy.url dynamically
    config.set_main_option('sqlalchemy.url', get_engine_url())

    def run_migrations_offline():
        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=get_metadata(),
            literal_binds=True
        )
        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online():

        def process_revision_directives(context, revision, directives):
            if getattr(config.cmd_opts, 'autogenerate', False):
                script = directives[0]
                if script.upgrade_ops.is_empty():
                    directives[:] = []
                    logger.info("No changes in schema detected.")

        conf_args = current_app.extensions['migrate'].configure_args
        if conf_args.get("process_revision_directives") is None:
            conf_args["process_revision_directives"] = process_revision_directives

        connectable = get_engine()
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=get_metadata(),
                **conf_args
            )
            with context.begin_transaction():
                context.run_migrations()

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()

