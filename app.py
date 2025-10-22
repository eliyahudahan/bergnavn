# app.py - BergNavn Maritime Application
# Main Flask application factory and configuration
# Enhanced with AIS Live Service and maritime data processing

import logging
import os
from flask import Flask, session, request
from flask_apscheduler import APScheduler
from dotenv import load_dotenv

# Blueprints
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.main_routes import main_bp
from backend.routes.route_routes import routes_bp
from backend.routes.ml_routes import ml_bp
from backend.controllers.route_leg_controller import route_leg_bp
from backend.routes.system_routes import health_bp
from backend.routes.cruise_routes import cruise_blueprint
from backend.routes.weather_routes import weather_bp
from backend.routes.maritime_routes import maritime_bp

# Extensions
from backend.extensions import db, mail, migrate
from backend.services.cleanup import deactivate_old_weather_status

# Translation utility
from backend.utils.translations import translate

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Scheduler for background tasks
scheduler = APScheduler()


def create_app(config_name=None, testing=False, start_scheduler=False):
    """
    Factory method to create and configure the Flask app.
    Enhanced with AIS service initialization for real-time maritime data.
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(
        __name__,
        template_folder=os.path.join('backend', 'templates'),
        static_folder=os.path.join('backend', 'static')
    )

    # Register translation function for templates
    app.jinja_env.globals['translate'] = translate

    # Load configuration based on environment
    if testing or config_name == 'testing':
        app.config.from_object('backend.config.config.TestingConfig')
    else:
        app.config.from_object('backend.config.config.Config')

    # Initialize database and other extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Initialize AIS Live Service for real-time maritime data
    # This service connects to Kystverket AIS and provides live ship tracking
    if not testing and os.getenv("DISABLE_AIS_SERVICE") != "1":
        try:
            from backend.services.ais_service import ais_service
            ais_service.start_ais_stream()
            logging.info("✅ AIS Live Service initialized successfully")
            
            # Store AIS service in app context for easy access
            app.ais_service = ais_service
            
        except Exception as e:
            logging.warning(f"⚠️ AIS Service initialization failed: {e}")
            logging.info("🔧 Continuing without AIS service - using enhanced simulation data")
    else:
        logging.info("🔧 AIS Service disabled - using simulation mode")

    # Scheduler setup for periodic tasks
    if start_scheduler and not testing and os.getenv("FLASK_SKIP_SCHEDULER") != "1":
        scheduler.init_app(app)
        if not scheduler.running:
            scheduler.start()
        logging.info("✅ Background scheduler started")

    # Add periodic cleanup job for weather data if missing
    if scheduler.get_job('weekly_cleanup') is None:
        scheduler.add_job(
            id='weekly_cleanup',
            func=lambda: deactivate_old_weather_status(days=30),
            trigger='interval',
            weeks=1
        )
        logging.info("✅ Weekly cleanup job scheduled")

    # Import models to ensure they are registered with SQLAlchemy
    with app.app_context():
        from backend import models
        logging.info("✅ App context initialized - Models imported successfully")

    # Register all application blueprints
    # Each blueprint represents a modular component of the application
    app.register_blueprint(main_bp)
    app.register_blueprint(cruise_blueprint)
    app.register_blueprint(routes_bp, url_prefix="/routes")
    app.register_blueprint(route_leg_bp, url_prefix='/api/route')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(weather_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(maritime_bp, url_prefix='/maritime')

    logging.info("✅ All blueprints registered successfully")

    # Language selection middleware
    # Sets the language for each request based on URL parameter or session
    @app.before_request
    def set_language():
        lang_param = request.args.get('lang')
        if lang_param in ['en', 'no']:
            session['lang'] = lang_param
        session.setdefault('lang', 'en')

    # CLI command: List all available routes in the application
    # Useful for debugging and understanding the API structure
    @app.cli.command("list-routes")
    def list_routes():
        """CLI command to display all registered routes and their methods"""
        import urllib
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            line = urllib.parse.unquote(f"{rule.endpoint:30s} {methods:20s} {rule}")
            output.append(line)
        for line in sorted(output):
            print(line)

    return app


# Create the main application instance
# This instance is used by the WSGI server and development server
app = create_app()


# CLI command: Manual cleanup of old weather data
# Can be run independently of the scheduled job
@app.cli.command("run-cleanup")
def run_cleanup():
    """CLI command to manually run weather data cleanup"""
    deactivate_old_weather_status()
    print("✅ Manual cleanup completed")


# Development server entry point
# Only runs when script is executed directly (not imported)
if __name__ == "__main__":
    app.run(debug=True)