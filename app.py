# app.py - BergNavn Maritime Application (Final)
# Main Flask application factory and configuration
# Full integration: AIS Live, Scheduler, Cleanup, ML Routes, Middleware

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


def create_app(config_name=None, testing=False, start_scheduler=True):
    """Factory method to create and configure Flask app."""

    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(
        __name__,
        template_folder=os.path.join('backend', 'templates'),
        static_folder=os.path.join('backend', 'static')
    )

    # Register translation function for templates
    app.jinja_env.globals['translate'] = translate

    # Load configuration
    if testing or config_name == 'testing':
        app.config.from_object('backend.config.config.TestingConfig')
    else:
        app.config.from_object('backend.config.config.Config')

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Initialize AIS Live Service
    if not testing and os.getenv("DISABLE_AIS_SERVICE") != "1":
        try:
            from backend.services.ais_service import ais_service
            ais_service.start_ais_stream()
            logging.info("✅ AIS Live Service initialized successfully")
            app.ais_service = ais_service
        except Exception as e:
            logging.warning(f"⚠️ AIS Service initialization failed: {e}")
            logging.info("🔧 Continuing with simulation data")
    else:
        logging.info("🔧 AIS Service disabled - simulation mode active")

    # Scheduler setup
    if start_scheduler and not testing and os.getenv("FLASK_SKIP_SCHEDULER") != "1":
        scheduler.init_app(app)
        if not scheduler.running:
            scheduler.start()
        logging.info("✅ Background scheduler started")

    # Schedule weekly weather cleanup
    if scheduler.get_job('weekly_cleanup') is None:
        scheduler.add_job(
            id='weekly_cleanup',
            func=lambda: deactivate_old_weather_status(days=30),
            trigger='interval',
            weeks=1
        )
        logging.info("✅ Weekly weather cleanup job scheduled")

    # Import models
    with app.app_context():
        from backend import models
        logging.info("✅ Models imported successfully")

    # Register all blueprints
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
    @app.before_request
    def set_language():
        lang_param = request.args.get('lang')
        if lang_param in ['en', 'no']:
            session['lang'] = lang_param
        session.setdefault('lang', 'en')

    # CLI: List all routes
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

    return app


# Main application instance
app = create_app()

# CLI: Manual weather cleanup
@app.cli.command("run-cleanup")
def run_cleanup():
    deactivate_old_weather_status()
    print("✅ Manual cleanup completed")

# Development server entry point
if __name__ == "__main__":
    app.run(debug=True)
