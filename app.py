# app.py - BergNavn Maritime Application
# Main Flask application factory with full feature integration
# ENHANCED: Prioritizes Kystdatahuset API for reliable Norwegian AIS data
# FIXED: AIS service initialization with proper fallback handling
# UPDATED: Removed dashboard_routes.py import (deleted file)

import logging
import os
import sys
from flask import Flask, session, request, jsonify
from flask_apscheduler import APScheduler
from dotenv import load_dotenv

# Import all blueprints - REMOVED: dashboard_routes.py (deleted)
from backend.routes.main_routes import main_bp
from backend.routes.route_routes import routes_bp
from backend.routes.ml_routes import ml_bp
from backend.controllers.route_leg_controller import route_leg_bp
from backend.routes.cruise_routes import cruise_blueprint
from backend.routes.weather_routes import weather_bp
from backend.routes.maritime_routes import maritime_bp
from backend.routes.recommendation_routes import recommendation_bp
from backend.routes.system_dashboard import system_bp  # System monitoring dashboard
from backend.routes.analytics_routes import analytics_bp
from backend.routes.simulation_routes import simulation_bp

# Import extensions
from backend.extensions import db, mail, migrate
from backend.services.cleanup import deactivate_old_weather_status

# Import translation utilities
from backend.utils.translations import translate

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize scheduler
scheduler = APScheduler()


def _detect_migration_mode():
    """
    Detect when Alembic is loading the app (env.py).
    Prevents scheduler and AIS services from running during database migrations.
    
    Returns:
        bool: True if in migration mode, False otherwise
    """
    return "alembic" in sys.argv[0] or ("flask" in sys.argv[0] and len(sys.argv) > 1 and "db" in sys.argv[1])


def _initialize_ais_service(app, testing=False, migration_mode=False):
    """
    Initialize the appropriate AIS service based on configuration.
    ENHANCED: Prioritizes Kystdatahuset API for reliable Norwegian AIS data.
    FIXED: Proper fallback handling with real-time simulation.
    
    Priority: 
    1. Kystdatahuset API (most reliable for Norwegian waters)
    2. Kystverket Socket (if Kystdatahuset fails)
    3. Empirical service with real-time simulation
    """
    # Check if AIS is disabled
    if os.getenv("DISABLE_AIS_SERVICE") == "1":
        logging.info("🔧 AIS Service disabled by configuration")
        return
    
    logging.info("🔄 Initializing AIS service...")
    
    # 1. Try Kystdatahuset API first (most reliable for Norwegian data)
    use_kystdatahuset = os.getenv("USE_KYSTDATAHUSET_AIS", "false").strip().lower() == "true"
    if use_kystdatahuset:
        try:
            from backend.services.kystdatahuset_adapter import kystdatahuset_adapter
            app.ais_service = kystdatahuset_adapter
            logging.info("✅ Kystdatahuset AIS Adapter initialized - REAL-TIME Norwegian AIS")
            logging.info(f"📡 Serving {len(kystdatahuset_adapter.NORWEGIAN_CITIES)} Norwegian cities")
            
            # Test the connection
            try:
                status = kystdatahuset_adapter.get_service_status()
                logging.info(f"📊 Kystdatahuset status: {status.get('request_statistics', {}).get('success_rate', 'Unknown')}")
            except Exception as e:
                logging.warning(f"Kystdatahuset status check failed: {e}")
            
            return
        except ImportError as e:
            logging.error(f"❌ Kystdatahuset Adapter import failed: {e}")
        except Exception as e:
            logging.error(f"❌ Kystdatahuset Adapter initialization failed: {e}")
    
    # 2. Try Kystverket as fallback (often has connectivity issues)
    use_kystverket = os.getenv("USE_KYSTVERKET_AIS", "false").strip().lower() == "true"
    kystverket_host = os.getenv("KYSTVERKET_AIS_HOST", "").strip()
    
    if use_kystverket and kystverket_host:
        try:
            from backend.services.ais_service import ais_service
            # Force real-time mode
            ais_service.use_real_ais = True
            ais_service.ais_host = kystverket_host
            ais_service.ais_port = int(os.getenv("KYSTVERKET_AIS_PORT", "5631").strip())
            
            ais_service.start_ais_stream()
            app.ais_service = ais_service
            logging.info("✅ Kystverket Real-Time AIS Service initialized")
            logging.info(f"📡 Connected to: {kystverket_host}:{ais_service.ais_port}")
            
            # Start background monitoring for connection issues
            import threading
            def monitor_ais_connection():
                import time
                while True:
                    time.sleep(60)  # Check every minute
                    if not ais_service.running or not ais_service.ais_socket:
                        logging.warning("🔌 AIS connection lost, attempting to restart...")
                        try:
                            ais_service.start_ais_stream()
                            logging.info("✅ AIS connection restored")
                        except Exception as e:
                            logging.error(f"Failed to restore AIS connection: {e}")
            
            monitor_thread = threading.Thread(target=monitor_ais_connection, daemon=True)
            monitor_thread.start()
            
            return
        except ImportError as e:
            logging.error(f"❌ AIS Service import failed: {e}")
        except Exception as e:
            logging.error(f"❌ Kystverket AIS initialization failed: {e}")
    
    # 3. Fallback to empirical service with real-time simulation
    try:
        from backend.services.ais_service import ais_service
        # Configure for empirical mode but with real-time updates
        ais_service.use_real_ais = False
        ais_service.running = True
        
        # Start real-time simulation thread
        import threading
        def real_time_simulation():
            import time
            update_count = 0
            while ais_service.running:
                try:
                    ais_service.manual_refresh()
                    update_count += 1
                    if update_count % 10 == 0:  # Log every 10 updates
                        logging.info(f"🔄 Empirical AIS simulation update #{update_count}")
                except Exception as e:
                    logging.error(f"Empirical AIS simulation error: {e}")
                time.sleep(30)  # Update every 30 seconds
        
        thread = threading.Thread(target=real_time_simulation, daemon=True)
        thread.start()
        
        app.ais_service = ais_service
        logging.info("✅ Empirical AIS Service with real-time simulation initialized")
        logging.info("📊 Generating realistic Norwegian vessel data")
        
    except Exception as e:
        logging.warning(f"⚠️ All AIS service initialization attempts failed: {e}")
        app.ais_service = None


def _initialize_weather_service(app):
    """
    Initialize weather service for Norwegian maritime conditions.
    """
    try:
        from backend.services.weather_service import weather_service
        app.weather_service = weather_service
        logging.info("✅ Weather Service initialized for Norwegian coastal areas")
        
        # Test the weather service
        try:
            weather_data = weather_service.get_current_weather()
            if weather_data:
                logging.info(f"🌤️ Weather data available: {weather_data.get('location', 'Norwegian Coast')}")
        except Exception as e:
            logging.warning(f"Weather service test failed: {e}")
            
    except ImportError as e:
        logging.warning(f"Weather service import failed: {e}")
    except Exception as e:
        logging.warning(f"Weather service initialization failed: {e}")


def create_app(config_name=None, testing=False, start_scheduler=True):
    """
    Factory method to create and configure Flask application.
    
    Args:
        config_name: Configuration name (default, testing, production)
        testing: Boolean flag for testing mode
        start_scheduler: Boolean flag to start scheduler
        
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Detect migration context to disable services during migrations
    migration_mode = _detect_migration_mode()
    
    if migration_mode:
        testing = True
        start_scheduler = False
        logging.info("🔧 Migration mode detected - disabling services")

    # Determine configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    # Create Flask application
    app = Flask(
        __name__,
        template_folder=os.path.join('backend', 'templates'),
        static_folder=os.path.join('backend', 'static')
    )

    # Add translation function to Jinja globals
    app.jinja_env.globals['translate'] = translate

    # Load configuration
    if testing or config_name == 'testing':
        app.config.from_object('backend.config.config.TestingConfig')
        logging.info("🔧 Testing configuration loaded")
    else:
        app.config.from_object('backend.config.config.Config')
        logging.info("✅ Production configuration loaded")

    # Initialize database and extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    logging.info("✅ Database and extensions initialized")

    # Initialize AIS Service - SINGLE SOURCE OF TRUTH with priority handling
    if not (testing or migration_mode):
        _initialize_ais_service(app, testing, migration_mode)
    else:
        logging.info("🔧 AIS Service disabled (testing/migration mode)")

    # Initialize Weather Service
    if not (testing or migration_mode):
        _initialize_weather_service(app)
    else:
        logging.info("🔧 Weather Service disabled (testing/migration mode)")

    # Initialize scheduler for background tasks
    if start_scheduler and not testing and not migration_mode and os.getenv("FLASK_SKIP_SCHEDULER") != "1":
        scheduler.init_app(app)
        if not scheduler.running:
            scheduler.start()
        logging.info("✅ Background scheduler started")
    else:
        logging.info("🔧 Scheduler disabled (testing/migration mode)")

    # Add weekly cleanup job for old data
    if not migration_mode and scheduler.running:
        if scheduler.get_job('weekly_cleanup') is None:
            scheduler.add_job(
                id='weekly_cleanup',
                func=lambda: deactivate_old_weather_status(days=30),
                trigger='interval',
                weeks=1,
                name='Weekly data cleanup'
            )
            logging.info("✅ Weekly cleanup job scheduled")

    # Import models within application context
    with app.app_context():
        from backend import models
        logging.info("✅ Database models imported successfully")

    # Register all blueprints
    app.register_blueprint(main_bp)  # Main pages (home, about, contact)
    app.register_blueprint(cruise_blueprint)  # Cruise routes
    app.register_blueprint(routes_bp, url_prefix="/routes")  # Route management
    app.register_blueprint(route_leg_bp, url_prefix='/api/route')  # Route legs API
    app.register_blueprint(ml_bp, url_prefix='/api/ml')  # Machine learning API
    app.register_blueprint(weather_bp)  # Weather API - NOTE: blueprint name is 'weather'
    app.register_blueprint(maritime_bp, url_prefix='/maritime')  # Maritime dashboard
    app.register_blueprint(recommendation_bp)  # Recommendation engine
    app.register_blueprint(system_bp, url_prefix='/api/system')  # System monitoring API
    app.register_blueprint(analytics_bp)
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')

    logging.info("✅ All blueprints registered successfully")

    # Language middleware - set language based on URL parameter or session
    @app.before_request
    def set_language():
        """
        Set language for the current request.
        Language can be specified via 'lang' URL parameter or stored in session.
        """
        lang_param = request.args.get('lang')
        if lang_param in ['en', 'no']:
            session['lang'] = lang_param
        session.setdefault('lang', 'en')

    # API key validation endpoint for debugging
    @app.route('/api/check-api-keys')
    def check_api_keys():
        """
        Check if required API keys are configured.
        
        Returns:
            JSON object with API key status
        """
        keys_status = {
            'OPENWEATHER_API_KEY': bool(os.getenv('OPENWEATHER_API_KEY')),
            'MET_USER_AGENT': bool(os.getenv('MET_USER_AGENT')),
            'USE_KYSTVERKET_AIS': os.getenv('USE_KYSTVERKET_AIS') == 'true',
            'USE_FREE_AIS': os.getenv('USE_FREE_AIS') == 'true',
            'USE_KYSTDATAHUSET_AIS': os.getenv('USE_KYSTDATAHUSET_AIS') == 'true',
            'AIS_ENABLED': os.getenv('DISABLE_AIS_SERVICE') != '1',
            'BARENTSWATCH_CLIENT_ID': bool(os.getenv('BARENTSWATCH_CLIENT_ID')),
            'FLASK_ENV': os.getenv('FLASK_ENV', 'development'),
            'ACTIVE_AIS_SERVICE': getattr(app, 'ais_service', None).__class__.__name__ if hasattr(app, 'ais_service') else 'None',
            'ACTIVE_WEATHER_SERVICE': getattr(app, 'weather_service', None).__class__.__name__ if hasattr(app, 'weather_service') else 'None'
        }
        return jsonify(keys_status)

    # CLI command to list all available routes
    @app.cli.command("list-routes")
    def list_routes():
        """
        CLI command to list all registered routes.
        Usage: flask list-routes
        """
        import urllib.parse
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            line = urllib.parse.unquote(f"{rule.endpoint:40s} {methods:20s} {rule}")
            output.append(line)
        
        print("\n" + "="*80)
        print("REGISTERED ROUTES")
        print("="*80)
        for line in sorted(output):
            print(line)
        print("="*80)
        print(f"Total routes: {len(output)}")

    # System initialization logging
    logging.info("="*60)
    logging.info("🚀 BergNavn Maritime System Initialized")
    logging.info(f"🌍 Environment: {os.getenv('FLASK_ENV', 'development')}")
    logging.info(f"🌐 Supported ports: 10 Norwegian cities")
    logging.info(f"📊 Available dashboards: /maritime (Maritime Dashboard)")
    logging.info(f"🚢 Available simulations: /maritime/simulation (Bergen Simulator)")
    logging.info(f"🗺️ Available routes: /routes (RTZ Routes)")
    logging.info(f"🔍 System monitoring: /api/system/health, /api/system/metrics")
    
    # Log active services
    if hasattr(app, 'ais_service'):
        service_name = app.ais_service.__class__.__name__
        logging.info(f"📡 AIS Service: {service_name}")
    if hasattr(app, 'weather_service'):
        logging.info(f"🌤️ Weather Service: Active")
    
    logging.info("="*60)

    return app


# Create main application instance
app = create_app()


# CLI command for manual cleanup
@app.cli.command("run-cleanup")
def run_cleanup():
    """
    CLI command to manually run cleanup of old weather data.
    Usage: flask run-cleanup
    """
    print("🔧 Starting manual cleanup...")
    deactivate_old_weather_status(days=30)
    print("✅ Manual cleanup completed")


# Test endpoint for Kystdatahuset integration
@app.route('/api/kystdatahuset-test')
def kystdatahuset_test():
    """
    Test endpoint to verify Kystdatahuset adapter functionality.
    
    Returns:
        JSON response with service status or error
    """
    try:
        from backend.services.kystdatahuset_adapter import kystdatahuset_adapter
        status = kystdatahuset_adapter.get_service_status()
        return jsonify({
            'status': 'success',
            'service': 'KystdatahusetAdapter',
            'timestamp': status.get('timestamp'),
            'configuration': status.get('configuration', {}),
            'request_statistics': status.get('request_statistics', {}),
            'data_quality': status.get('data_quality', {}),
            'connectivity_test': status.get('connectivity_test', {})
        })
    except ImportError:
        return jsonify({
            'status': 'error',
            'error': 'KystdatahusetAdapter not found. Check installation.'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# Test endpoint for RTZ route discovery
@app.route('/api/rtz-discovery-test')
def rtz_discovery_test():
    """
    Test endpoint to verify RTZ route discovery functionality.
    
    Returns:
        JSON response with discovered routes
    """
    try:
        from backend.services.rtz_parser import discover_rtz_files, get_processing_statistics
        
        stats = get_processing_statistics()
        routes = discover_rtz_files()
        
        return jsonify({
            'status': 'success',
            'routes_discovered': len(routes),
            'statistics': stats,
            'routes_sample': routes[:5] if routes else [],  # First 5 routes as sample
            'cities_with_routes': list(set(route.get('source_city', 'unknown') for route in routes))
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'error': f'RTZ parser import failed: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# Application entry point
if __name__ == "__main__":
    """
    Main entry point when running the application directly.
    Runs the Flask development server with debug mode enabled.
    """
    app.run(
        debug=True,
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        threaded=True
    )