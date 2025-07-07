import logging
import os
from flask import Flask
from flask_apscheduler import APScheduler
from dotenv import load_dotenv

from backend.extensions import db, mail, login_manager, migrate
from backend.models.user import User
from backend.services.cleanup import deactivate_old_weather_status

from backend.routes.route_routes import routes_bp 
from backend.routes.ml_routes import ml_bp
from backend.controllers.route_leg_controller import route_leg_bp
from backend.routes.system_routes import health_bp
from backend.routes.booking_routes import booking_blueprint
from backend.routes.user_routes import user_blueprint
from backend.routes.cruise_routes import cruise_blueprint
from backend.routes.weather_routes import weather_bp

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

scheduler = APScheduler()  # מוגדר מחוץ ל־create_app

def create_app(config_name=None):
    """Create and configure the Flask application."""
    from backend.config.config import Config, TestingConfig

    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)

    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Init models
    with app.app_context():
        from backend import models
        logging.info("App context initialized. Models imported.")

    # Blueprints
    app.register_blueprint(user_blueprint)
    app.register_blueprint(cruise_blueprint, url_prefix='/api')
    app.register_blueprint(health_bp)
    app.register_blueprint(booking_blueprint, url_prefix='/booking')
    app.register_blueprint(routes_bp, url_prefix='/api/routes')
    app.register_blueprint(route_leg_bp, url_prefix='/api/route')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(weather_bp)

    logging.info("Blueprints registered")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # CLI command to list routes
    @app.cli.command("list-routes")
    def list_routes():
        import urllib
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            line = urllib.parse.unquote(f"{rule.endpoint:30s} {methods:20s} {rule}")
            output.append(line)
        for line in sorted(output):
            print(line)

    # Init scheduler
    scheduler.init_app(app)
    scheduler.start()

    # Add weekly cleanup job
    scheduler.add_job(
        id='weekly_cleanup',
        func=lambda: deactivate_old_weather_status(days=30),
        trigger='interval',
        weeks=1
    )

    return app

# Create app outside for CLI access
app = create_app()

# CLI cleanup command (✅ מוגדר מחוץ ל־create_app)
@app.cli.command("run-cleanup")
def run_cleanup():
    """Deactivate old weather statuses manually."""
    deactivate_old_weather_status()

if __name__ == "__main__":
    app.run(debug=True)




