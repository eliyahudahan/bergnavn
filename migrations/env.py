import logging
import os
import sys
from logging.config import fileConfig

from alembic import context
from flask import current_app

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app  # Flask factory method

# Alembic Config object
config = context.config

# Setup logging
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Create Flask app
app = create_app()

def get_engine_url():
    db = current_app.extensions['migrate'].db
    return db.engine.url.render_as_string(hide_password=False).replace('%', '%%')

def get_metadata():
    db = current_app.extensions['migrate'].db
    return db.metadata

with app.app_context():
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
                    logger.info("No schema changes detected.")

        db = current_app.extensions['migrate'].db
        connectable = db.engine

        conf_args = current_app.extensions['migrate'].configure_args
        if conf_args.get("process_revision_directives") is None:
            conf_args["process_revision_directives"] = process_revision_directives

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


