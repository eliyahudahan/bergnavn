import logging
import os
from flask import Flask
from flask_apscheduler import APScheduler
from dotenv import load_dotenv

# Blueprints
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.main_routes import main_bp
from backend.routes.route_routes import routes_bp
from backend.routes.ml_routes import ml_bp
from backend.controllers.route_leg_controller import route_leg_bp
from backend.routes.system_routes import health_bp
from backend.routes.booking_routes import booking_blueprint
from backend.routes.user_routes import user_blueprint
from backend.routes.cruise_routes import cruise_blueprint
from backend.routes.weather_routes import weather_bp
from backend.routes.dummy_user_routes import dummy_user_bp 

# Extensions
from backend.extensions import db, mail, login_manager, migrate
from backend.models.user import User
from backend.services.cleanup import deactivate_old_weather_status

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)

# Scheduler
scheduler = APScheduler()

def create_app(config_name=None, testing=False, start_scheduler=False):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(
        __name__,
        template_folder=os.path.join('backend', 'templates'),
        static_folder=os.path.join('backend', 'static')
    )

    # Configuration
    if testing or config_name == 'testing':
        app.config.from_object('backend.config.config.TestingConfig')
    else:
        app.config.from_object('backend.config.config.Config')

    # Init extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Scheduler setup
    if start_scheduler and not testing and os.getenv("FLASK_SKIP_SCHEDULER") != "1":
        scheduler.init_app(app)
        if not scheduler.running:
            scheduler.start()

    # Add cleanup job if not exists
    if scheduler.get_job('weekly_cleanup') is None:
        scheduler.add_job(
            id='weekly_cleanup',
            func=lambda: deactivate_old_weather_status(days=30),
            trigger='interval',
            weeks=1
        )

    # Models
    with app.app_context():
        from backend import models
        logging.info("App context initialized. Models imported.")

    # Register Blueprints
    app.register_blueprint(user_blueprint)  # למשל /login, /logout, וכו'
    app.register_blueprint(main_bp)  # כולל route '/' שמחזיר home.html
    app.register_blueprint(cruise_blueprint)       # למשל /cruises/view
    app.register_blueprint(routes_bp, url_prefix="/routes")  # למשל /routes/view
    app.register_blueprint(route_leg_bp, url_prefix='/api/route')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(weather_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(booking_blueprint, url_prefix='/booking')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(dummy_user_bp)

    logging.info("Blueprints registered")

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # CLI: list routes
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

# Create app
app = create_app()

# CLI: manual cleanup
@app.cli.command("run-cleanup")
def run_cleanup():
    """Deactivate old weather statuses manually."""
    deactivate_old_weather_status()

if __name__ == "__main__":
    app.run(debug=True)


