# app.py - BergNavn Maritime Application (Safe + Migration-Proof Version)
# Main Flask application factory and configuration

import logging
import os
import sys
from flask import Flask, session, request, jsonify
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
from backend.routes.recommendation_routes import recommendation_bp


# Extensions
from backend.extensions import db, mail, migrate
from backend.services.cleanup import deactivate_old_weather_status

# Translation
from backend.utils.translations import translate

load_dotenv()

logging.basicConfig(level=logging.INFO)

scheduler = APScheduler()


def _detect_migration_mode():
    """
    Detect when Alembic is loading the app (env.py).
    This ensures the scheduler / AIS won't run during migrations.
    """
    return "alembic" in sys.argv[0] or ("flask" in sys.argv[0] and len(sys.argv) > 1 and "db" in sys.argv[1])


def create_app(config_name=None, testing=False, start_scheduler=True):
    """Factory method to create and configure Flask app."""

    # Detect migration context (Alembic env.py)
    migration_mode = _detect_migration_mode()

    if migration_mode:
        testing = True
        start_scheduler = False

    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(
        __name__,
        template_folder=os.path.join('backend', 'templates'),
        static_folder=os.path.join('backend', 'static')
    )

    app.jinja_env.globals['translate'] = translate

    if testing or config_name == 'testing':
        app.config.from_object('backend.config.config.TestingConfig')
    else:
        app.config.from_object('backend.config.config.Config')

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # AIS Service disabled during migrations & testing
    if not (testing or migration_mode) and os.getenv("DISABLE_AIS_SERVICE") != "1":
        try:
            from backend.services.ais_service import ais_service
            ais_service.start_ais_stream()
            app.ais_service = ais_service
            logging.info("✅ AIS Live Service initialized successfully")
        except Exception as e:
            logging.warning(f"⚠️ AIS Service initialization failed: {e}")
    else:
        logging.info("🔧 AIS Service disabled (testing/migration mode)")

    # Scheduler
    if start_scheduler and not testing and not migration_mode and os.getenv("FLASK_SKIP_SCHEDULER") != "1":
        scheduler.init_app(app)
        if not scheduler.running:
            scheduler.start()
        logging.info("✅ Background scheduler started")
    else:
        logging.info("🔧 Scheduler disabled (testing/migration mode)")

    # Weekly cleanup job
    if not migration_mode and scheduler.running:
        if scheduler.get_job('weekly_cleanup') is None:
            scheduler.add_job(
                id='weekly_cleanup',
                func=lambda: deactivate_old_weather_status(days=30),
                trigger='interval',
                weeks=1
            )
            logging.info("✅ Weekly cleanup job scheduled")

    # Import models
    with app.app_context():
        from backend import models
        logging.info("✅ Models imported successfully")

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(cruise_blueprint)
    app.register_blueprint(routes_bp, url_prefix="/routes")
    app.register_blueprint(route_leg_bp, url_prefix='/api/route')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(weather_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(maritime_bp, url_prefix='/maritime')
    app.register_blueprint(recommendation_bp)


    logging.info("✅ All blueprints registered successfully")

    # Language middleware
    @app.before_request
    def set_language():
        lang_param = request.args.get('lang')
        if lang_param in ['en', 'no']:
            session['lang'] = lang_param
        session.setdefault('lang', 'en')

    # API key validation endpoint
    @app.route('/api/check-api-keys')
    def check_api_keys():
        """Check if API keys are configured"""
        keys_status = {
            'OPENWEATHER_API_KEY': bool(os.getenv('OPENWEATHER_API_KEY')),
            'MET_USER_AGENT': bool(os.getenv('MET_USER_AGENT')),
            'USE_KYSTVERKET_AIS': os.getenv('USE_KYSTVERKET_AIS') == 'true',
            'USE_FREE_AIS': os.getenv('USE_FREE_AIS') == 'true',
            'AIS_ENABLED': os.getenv('DISABLE_AIS_SERVICE') != '1'
        }
        return jsonify(keys_status)

    # CLI command
    @app.cli.command("list-routes")
    def list_routes():
        import urllib.parse
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            line = urllib.parse.unquote(f"{rule.endpoint:30s} {methods:20s} {rule}")
            output.append(line)
        for line in sorted(output):
            print(line)

    return app


# Main app instance
app = create_app()


# Manual cleanup CLI command
@app.cli.command("run-cleanup")
def run_cleanup():
    deactivate_old_weather_status(days=30)
    print("✅ Manual cleanup completed")


if __name__ == "__main__":
    app.run(debug=True)