import logging
import os
from flask import Flask
from dotenv import load_dotenv

from backend.routes.system_routes import health_bp
from backend.routes.booking_routes import booking_blueprint
from backend.routes.user_routes import user_blueprint
from backend.routes.cruise_routes import cruise_blueprint

from backend import db, mail, login_manager, migrate
from backend.models.user import User

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)


def create_app(config_name=None):
    """Create and configure the Flask application."""
    from backend.config.config import Config, TestingConfig

    # If no config_name is passed, fallback to FLASK_ENV or 'default'
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    # Create the Flask app instance
    app = Flask(__name__)

    # Load configuration based on environment
    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Create database tables if they do not exist
    try:
        with app.app_context():
            from backend import models  # Ensures all models are loaded and registered
            db.create_all()
            logging.info("Database connected and tables created.")
    except Exception as e:
        logging.error(f"Could not connect to database: {e}")

    # Register blueprints
    app.register_blueprint(user_blueprint)
    app.register_blueprint(cruise_blueprint)
    app.register_blueprint(health_bp)
    app.register_blueprint(booking_blueprint, url_prefix='/booking')

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
