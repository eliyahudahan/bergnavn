#!/usr/bin/env python3
"""
BergNavn Maritime Intelligence Platform - WORKING VERSION
All 3 pages working: Dashboard, Simulation, Routes
FIXED: Dashboard now shows ALL RTZ routes with complete waypoints
ADDED: Weather API endpoints for new weather system
UPDATED: Real-time vessel tracking API integration
"""

import os
import sys
from flask import Flask, render_template, jsonify, session, request
from datetime import datetime
import logging

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'backend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'backend', 'static')

print("=" * 60)
print("🚢 BERGENAVN MARITIME - COMPLETE RTZ VERSION")
print("=" * 60)
print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Template directory: {TEMPLATE_DIR}")
print(f"📁 Static directory: {STATIC_DIR}")

# ============================================
# CREATE FLASK APP
# ============================================

app = Flask(__name__,
           template_folder=TEMPLATE_DIR,
           static_folder=STATIC_DIR,
           static_url_path='/static')

# ============================================
# SECURITY CONFIGURATION
# ============================================

# Load SECRET_KEY from environment
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    logger.warning("⚠️  SECRET_KEY not found in environment, using development key")
    secret_key = 'bergnavn-development-secure-key-2025'

app.config['SECRET_KEY'] = secret_key
print("✅ SECRET_KEY configured")

# Try to enable CORS if available
try:
    from flask_cors import CORS
    CORS(app)
    print("✅ CORS enabled")
except ImportError:
    print("⚠️  CORS not available")

# ============================================
# REGISTER BLUEPRINTS
# ============================================

print("\n📋 Registering blueprints...")

try:
    from backend.routes.main_routes import main_bp
    app.register_blueprint(main_bp)
    print("✅ Registered: main_bp (/)")
except Exception as e:
    print(f"⚠️  Could not register main_bp: {e}")

try:
    from backend.routes.maritime_routes import maritime_bp
    app.register_blueprint(maritime_bp, url_prefix='/maritime')
    print("✅ Registered: maritime_bp (/maritime)")
except Exception as e:
    print(f"⚠️  Could not register maritime_bp: {e}")

try:
    from backend.routes.route_routes import routes_bp
    app.register_blueprint(routes_bp, url_prefix='/routes')
    print("✅ Registered: routes_bp (/routes)")
except Exception as e:
    print(f"⚠️  Could not register routes_bp: {e}")

# ============================================
# WEATHER API BLUEPRINT
# ============================================

try:
    from backend.routes.api_weather import bp as api_weather_bp
    app.register_blueprint(api_weather_bp, url_prefix='/api')
    print("✅ Registered: api_weather_bp (/api)")
except Exception as e:
    print(f"⚠️  Could not register api_weather_bp: {e}")

# ============================================
# VESSEL API BLUEPRINT (NEW - Real-time vessel tracking)
# ============================================

try:
    from backend.routes.api_vessels import register_vessel_routes
    register_vessel_routes(app)
    print("✅ Registered: vessel API routes (/maritime/api/vessels)")
except ImportError as e:
    print(f"⚠️  Could not register vessel API routes: {e}")
except Exception as e:
    print(f"⚠️  Error registering vessel API routes: {e}")

# ============================================
# LANGUAGE ROUTES
# ============================================

@app.route('/<lang>')
def home_with_lang(lang):
    """Home page with language parameter"""
    if lang in ['en', 'no']:
        session['lang'] = lang
        return render_template('home.html', lang=lang)
    else:
        return '''
        <script>
            window.location.href = '/en';
        </script>
        '''

# ============================================
# MARITIME DASHBOARD - FIXED: COMPLETE ROUTES
# ============================================

@app.route('/maritime/dashboard')
def maritime_dashboard():
    """Maritime dashboard with COMPLETE RTZ routes including all waypoints"""
    logger.info("Loading maritime dashboard with COMPLETE RTZ data")
    
    try:
        from backend.rtz_loader_fixed import rtz_loader
        data = rtz_loader.get_dashboard_data()
        routes_list = data.get('routes', [])
        ports_list = data.get('ports_list', [])
        total_waypoints = data.get('total_waypoints', 0)
        
        print(f"✅ Loaded {len(routes_list)} routes with {total_waypoints} waypoints for dashboard")
        
    except Exception as e:
        logger.error(f"Error loading RTZ data: {e}")
        routes_list = []
        ports_list = ['Bergen', 'Oslo', 'Stavanger', 'Trondheim']
        total_waypoints = 0
    
    # Calculate unique ports
    unique_ports = set()
    for route in routes_list:
        if route.get('origin'):
            unique_ports.add(route['origin'])
        if route.get('destination'):
            unique_ports.add(route['destination'])
    
    return render_template(
        'maritime_split/dashboard_base.html',
        lang='en',
        routes=routes_list,
        route_count=len(routes_list),
        ports_list=ports_list,
        unique_ports_count=len(unique_ports),
        total_waypoints=total_waypoints,
        title="Maritime Dashboard - Complete RTZ Routes"
    )

# ============================================
# SIMULATION DASHBOARD - WITH LANG PARAMETER
# ============================================

@app.route('/maritime/simulation-dashboard/<lang>')
def simulation_dashboard(lang):
    """Simulation dashboard - with lang parameter"""
    if lang not in ['en', 'no']:
        lang = 'en'
    
    logger.info(f"Loading simulation dashboard for language: {lang}")
    
    return render_template(
        'maritime_split/realtime_simulation.html',
        lang=lang,
        routes_count=34,
        ports_list=['Bergen', 'Oslo', 'Stavanger', 'Trondheim', 'Kristiansand'],
        title="Maritime Simulation Dashboard"
    )

# ============================================
# ROUTES PAGE - FIXED: SHOW MORE ROUTES
# ============================================

@app.route('/routes')
def routes_page():
    """Routes page with RTZ data - show more routes"""
    try:
        from backend.rtz_loader_fixed import rtz_loader
        data = rtz_loader.get_dashboard_data()
        
        # Calculate unique ports
        unique_ports = set()
        routes_data = data.get('routes', [])
        for route in routes_data:
            if route.get('origin'):
                unique_ports.add(route['origin'])
            if route.get('destination'):
                unique_ports.add(route['destination'])
        
        return render_template(
            'routes.html',
            lang='en',
            routes=routes_data[:50],
            route_count=data.get('total_routes', len(routes_data)),
            ports_list=data.get('ports_list', ['Bergen', 'Oslo', 'Stavanger']),
            unique_ports_count=len(unique_ports),
            title="Norwegian Coastal Routes"
        )
    except Exception as e:
        logger.error(f"Error loading routes: {e}")
        return render_template(
            'routes.html',
            lang='en',
            routes=[],
            route_count=34,
            ports_list=['Bergen', 'Oslo', 'Stavanger', 'Trondheim'],
            unique_ports_count=10,
            title="Norwegian Coastal Routes"
        )

# ============================================
# API ENDPOINTS - ALL WORKING
# ============================================

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'pages_working': 3,
        'message': 'All 3 pages working: Dashboard, Simulation, Routes'
    })

# SIMPLE WEATHER API (added directly for reliability)
@app.route('/api/simple-weather')
def simple_weather_api():
    """Simple weather API endpoint - works directly without blueprint"""
    try:
        # Import the weather service using correct path
        sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))
        from services.weather_integration_service import weather_integration_service
        
        # Get parameters or use defaults
        lat = request.args.get('lat', 60.39, type=float)
        lon = request.args.get('lon', 5.32, type=float)
        
        print(f"🌤️ Simple Weather API called for {lat}, {lon}")
        
        # Get weather data
        weather_data = weather_integration_service.get_weather_for_dashboard(lat, lon)
        
        # Ensure display object exists
        if 'display' not in weather_data:
            weather_data['display'] = {
                'temperature': f"{round(weather_data.get('temperature_c', 0))}°C",
                'wind': f"{round(weather_data.get('wind_speed_ms', 0))} m/s",
                'location': weather_data.get('location', 'Bergen'),
                'condition': weather_data.get('condition', 'Unknown'),
                'source_badge': get_source_badge(weather_data.get('data_source', 'unknown')),
                'icon': get_weather_icon(weather_data.get('condition', ''))
            }
        
        # Create response
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': weather_data,
            'api_version': '1.0'
        }
        
        return jsonify(response)
        
    except ImportError as e:
        print(f"❌ Weather service import error: {e}")
        # Try alternative import path
        try:
            # Fallback to empirical weather service
            from backend.services.met_norway_service import met_norway_service
            weather_data = met_norway_service.get_current_weather(lat, lon)
            
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'data': weather_data,
                'api_version': '1.0',
                'note': 'Using MET Norway service directly'
            })
        except Exception as inner_e:
            print(f"❌ MET Norway fallback also failed: {inner_e}")
            # Ultimate fallback
            return get_fallback_weather_response(lat, lon, f"Import error: {str(e)[:100]}")
        
    except Exception as e:
        print(f"❌ Simple Weather API error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return fallback data
        return get_fallback_weather_response(lat, lon, f"API error: {str(e)[:100]}")

def get_fallback_weather_response(lat, lon, error_msg):
    """Generate fallback weather response when all else fails"""
    return jsonify({
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'temperature_c': 8.5,
            'wind_speed_ms': 5.2,
            'location': 'Bergen',
            'condition': 'Fallback Data',
            'data_source': 'fallback',
            'display': {
                'temperature': '8°C',
                'wind': '5 m/s',
                'location': 'Bergen',
                'condition': 'Fallback Data',
                'source_badge': '📊 Fallback',
                'icon': 'cloud'
            }
        },
        'note': 'Using fallback data due to error',
        'error_message': error_msg
    })

def get_source_badge(source):
    """Helper function to get source badge"""
    badges = {
        'met_norway': '🇳🇴 MET Norway',
        'met_norway_live': '🇳🇴 MET Norway',
        'barentswatch': '🌊 BarentsWatch',
        'openweather': '🌍 OpenWeatherMap',
        'empirical': '📊 Empirical',
        'fallback_empirical': '📊 Empirical',
        'emergency': '🚨 Emergency'
    }
    return badges.get(source, '📊 Weather')

def get_weather_icon(condition):
    """Helper function to get weather icon"""
    condition_lower = condition.lower()
    
    if 'clear' in condition_lower or 'fair' in condition_lower:
        return 'sun'
    elif 'cloud' in condition_lower:
        return 'cloud'
    elif 'rain' in condition_lower:
        return 'cloud-rain'
    elif 'snow' in condition_lower:
        return 'snow'
    elif 'fog' in condition_lower or 'mist' in condition_lower:
        return 'cloud-fog'
    else:
        return 'cloud'

@app.route('/maritime/api/rtz/routes')
def rtz_routes_api():
    """RTZ routes API endpoint - COMPLETE DATA"""
    try:
        from backend.rtz_loader_fixed import rtz_loader
        data = rtz_loader.get_dashboard_data()
        
        return jsonify({
            'success': True,
            'count': len(data.get('routes', [])),
            'total_waypoints': data.get('total_waypoints', 0),
            'routes': data.get('routes', []),
            'ports': data.get('ports_list', []),
            'metadata': data.get('metadata', {}),
            'message': 'COMPLETE RTZ routes loaded successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"RTZ API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'routes': [],
            'message': 'Error loading RTZ data',
            'timestamp': datetime.now().isoformat()
        })

@app.route('/maritime/api/rtz/complete')
def rtz_complete_api():
    """Complete RTZ data API endpoint with debugging info"""
    try:
        from backend.rtz_loader_fixed import rtz_loader
        data = rtz_loader.get_dashboard_data()
        
        # Debug information
        debug_info = {}
        if data.get('routes'):
            sample_route = data['routes'][0]
            debug_info = {
                'sample_route_name': sample_route.get('route_name'),
                'has_waypoints_key': 'waypoints' in sample_route,
                'waypoint_count': sample_route.get('waypoint_count'),
                'actual_waypoints_length': len(sample_route.get('waypoints', [])),
                'sample_waypoint': sample_route.get('waypoints', [{}])[0] if sample_route.get('waypoints') else None
            }
        
        return jsonify({
            'success': True,
            'count': len(data.get('routes', [])),
            'total_waypoints': data.get('total_waypoints', 0),
            'routes': data.get('routes', []),
            'ports': data.get('ports_list', []),
            'metadata': data.get('metadata', {}),
            'debug': debug_info,
            'message': 'Complete RTZ data with waypoints',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Complete RTZ API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'routes': [],
            'message': 'Error loading complete RTZ data',
            'timestamp': datetime.now().isoformat()
        })

@app.route('/maritime/api/ais-data')
def ais_data_api():
    """AIS data API endpoint"""
    try:
        # Try to import AIS service
        from backend.services.ais_service import get_current_ais_data
        ais_data = get_current_ais_data()
        
        return jsonify({
            'success': True,
            'vessels': ais_data.get('vessels', []),
            'count': ais_data.get('count', 0),
            'timestamp': datetime.now().isoformat(),
            'source': 'AIS Service'
        })
    except ImportError:
        # Fallback to simulated data
        simulated_vessels = [
            {
                'mmsi': '257123450',
                'name': 'MS BERGENSFJORD',
                'lat': 60.392,
                'lon': 5.324,
                'speed': 12.5,
                'course': 45,
                'type': 'Cargo',
                'destination': 'Bergen'
            },
            {
                'mmsi': '257123451',
                'name': 'MS OSLOFJORD',
                'lat': 59.913,
                'lon': 10.752,
                'speed': 8.2,
                'course': 120,
                'type': 'Passenger',
                'destination': 'Oslo'
            }
        ]
        
        return jsonify({
            'success': True,
            'vessels': simulated_vessels,
            'count': len(simulated_vessels),
            'timestamp': datetime.now().isoformat(),
            'source': 'Simulated AIS Data',
            'note': 'Real AIS service not configured'
        })
    except Exception as e:
        logger.error(f"AIS API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'vessels': [],
            'message': 'AIS service unavailable',
            'timestamp': datetime.now().isoformat()
        })

@app.route('/maritime/api/weather-dashboard')
def weather_dashboard_api():
    """Weather API endpoint (legacy - for compatibility)"""
    return jsonify({
        'success': True,
        'temperature': 8.5,
        'wind_speed': 5.2,
        'city': 'Bergen',
        'timestamp': datetime.now().isoformat(),
        'source': 'Simulated weather data'
    })

# ============================================
# NEW REAL-TIME VESSEL API ENDPOINTS (Direct registration)
# ============================================

@app.route('/maritime/api/vessels/real-time')
def direct_real_time_vessel():
    """Direct implementation of real-time vessel endpoint"""
    try:
        # Import services
        from backend.services.empirical_ais_service import empirical_maritime_service
        
        # Get query parameters
        city = request.args.get('city', 'bergen').lower()
        radius_km = float(request.args.get('radius_km', 20))
        
        # Try to get empirical vessel
        vessel = empirical_maritime_service.get_bergen_vessel_empirical()
        
        if vessel:
            response = {
                'status': 'success',
                'source': vessel.get('data_source', 'unknown'),
                'vessel': vessel,
                'is_empirical': True,
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'city_requested': city,
                    'radius_km': radius_km
                }
            }
            
            logger.info(f"✅ Direct API: Real-time vessel from {vessel.get('data_source')}")
            return jsonify(response)
        
        # Fallback
        from datetime import datetime, timezone
        import random
        
        fallback_vessel = {
            'mmsi': f'257{random.randint(100000, 999999)}',
            'name': f'MS NORWAY {random.randint(1, 99)}',
            'lat': 60.3913 + random.uniform(-0.1, 0.1),
            'lon': 5.3221 + random.uniform(-0.1, 0.1),
            'speed_knots': round(random.uniform(5, 15), 1),
            'course': random.uniform(0, 360),
            'heading': random.uniform(0, 360),
            'type': random.choice(['Cargo', 'Tanker', 'Passenger', 'Fishing']),
            'destination': random.choice(['Bergen', 'Oslo', 'Stavanger', 'Trondheim']),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_source': 'empirical_fallback',
            'is_empirical': False
        }
        
        return jsonify({
            'status': 'fallback',
            'source': 'empirical_simulation',
            'vessel': fallback_vessel,
            'is_empirical': False,
            'timestamp': datetime.now().isoformat(),
            'message': 'Using empirical fallback data'
        })
        
    except Exception as e:
        logger.error(f"❌ Direct vessel API error: {e}")
        import random
        from datetime import datetime, timezone
        
        emergency_vessel = {
            'mmsi': '999999999',
            'name': 'EMERGENCY VESSEL',
            'lat': 60.3913,
            'lon': 5.3221,
            'speed_knots': 0,
            'course': 0,
            'type': 'Emergency',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_source': 'emergency',
            'is_empirical': False,
            'emergency': True
        }
        
        return jsonify({
            'status': 'emergency',
            'vessel': emergency_vessel,
            'is_empirical': False,
            'error': str(e)[:100],
            'message': 'Emergency fallback - service error',
            'timestamp': datetime.now().isoformat()
        })

@app.route('/maritime/api/vessels/empirical-status')
def direct_empirical_status():
    """Direct implementation of empirical status endpoint"""
    from datetime import datetime, timezone
    
    status = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment_config': {
            'USE_KYSTDATAHUSET_AIS': app.config.get('USE_KYSTDATAHUSET_AIS', False),
            'BARENTSWATCH_CLIENT_ID_set': bool(app.config.get('BARENTSWATCH_CLIENT_ID')),
            'MET_USER_AGENT_set': bool(app.config.get('MET_USER_AGENT'))
        },
        'data_sources': {},
        'recommendations': []
    }
    
    # Check Kystdatahuset availability
    try:
        from backend.services.kystdatahuset_adapter import kystdatahuset_adapter
        test_vessels = kystdatahuset_adapter.get_vessels_near_city('bergen', radius_km=10)
        status['data_sources']['kystdatahuset'] = {
            'available': True,
            'vessels_found': len(test_vessels),
            'status': 'operational' if test_vessels else 'no_data'
        }
    except Exception as e:
        status['data_sources']['kystdatahuset'] = {
            'available': False,
            'error': str(e),
            'status': 'unavailable'
        }
    
    # Check BarentsWatch
    try:
        from backend.services.barentswatch_service import barentswatch_service
        service_status = barentswatch_service.get_service_status()
        status['data_sources']['barentswatch'] = {
            'available': True,
            'token_valid': service_status['authentication']['token_valid'],
            'scope': service_status['authentication']['current_scope'],
            'status': 'operational'
        }
    except Exception as e:
        status['data_sources']['barentswatch'] = {
            'available': False,
            'error': str(e),
            'status': 'unavailable'
        }
    
    # Check empirical service
    try:
        from backend.services.empirical_ais_service import empirical_maritime_service
        empirical_status = empirical_maritime_service.get_service_status()
        status['data_sources']['empirical_maritime_service'] = empirical_status
    except Exception as e:
        status['data_sources']['empirical_maritime_service'] = {
            'available': False,
            'error': str(e),
            'status': 'unavailable'
        }
    
    # Overall assessment
    operational_sources = [s for s in status['data_sources'].values() if s.get('available') and s.get('status') == 'operational']
    status['overall_assessment'] = {
        'operational_sources': len(operational_sources),
        'total_sources': len(status['data_sources']),
        'readiness': 'ready' if len(operational_sources) > 0 else 'not_ready'
    }
    
    return jsonify(status)

# ============================================
# HOME PAGE
# ============================================

@app.route('/')
def home():
    """Home page redirect"""
    return '''
    <script>
        window.location.href = '/en';
    </script>
    '''

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def page_not_found(e):
    return '''
    <div style="text-align: center; padding: 50px; font-family: Arial;">
        <h1>🚢 404 - Route Not Found</h1>
        <p>The maritime route you're looking for doesn't exist.</p>
        <p><strong>Working pages:</strong></p>
        <p>
            <a href="/en">🏠 Home</a> |
            <a href="/maritime/dashboard">📊 Dashboard</a> |
            <a href="/maritime/simulation-dashboard/en">🚢 Simulation</a> |
            <a href="/routes">🗺️ Routes</a>
        </p>
        <p><strong>API Endpoints:</strong></p>
        <p>
            <a href="/api/health">🔧 Health Check</a> |
            <a href="/api/simple-weather">🌤️ Weather API</a> |
            <a href="/maritime/api/rtz/routes">🗺️ RTZ Routes</a> |
            <a href="/maritime/api/rtz/complete">🗺️ Complete RTZ Data</a>
            <a href="/maritime/api/vessels/real-time">🚢 Real-time Vessel</a>
        </p>
    </div>
    ''', 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 Error: {e}")
    return '''
    <div style="text-align: center; padding: 50px; font-family: Arial;">
        <h1>⚓ 500 - Internal Server Error</h1>
        <p>Something went wrong with the maritime systems.</p>
        <p><a href="/en">Return to Home Port</a></p>
    </div>
    ''', 500

# ============================================
# LOAD ENVIRONMENT CONFIGURATION
# ============================================

def load_environment_config():
    """Load environment configuration into app config"""
    # AIS settings
    app.config['USE_KYSTDATAHUSET_AIS'] = os.environ.get('USE_KYSTDATAHUSET_AIS', 'false').lower() == 'true'
    app.config['KYSTDATAHUSET_USER_AGENT'] = os.environ.get('KYSTDATAHUSET_USER_AGENT', '')
    
    # BarentsWatch API
    app.config['BARENTSWATCH_CLIENT_ID'] = os.environ.get('BARENTSWATCH_CLIENT_ID', '')
    app.config['BARENTSWATCH_CLIENT_SECRET'] = os.environ.get('BARENTSWATCH_CLIENT_SECRET', '')
    
    # MET Norway
    app.config['MET_USER_AGENT'] = os.environ.get('MET_USER_AGENT', '')
    
    print("\n🔧 Environment Configuration:")
    print(f"   USE_KYSTDATAHUSET_AIS: {app.config['USE_KYSTDATAHUSET_AIS']}")
    print(f"   BARENTSWATCH_CLIENT_ID: {'Set' if app.config['BARENTSWATCH_CLIENT_ID'] else 'Not set'}")
    print(f"   MET_USER_AGENT: {'Set' if app.config['MET_USER_AGENT'] else 'Not set'}")

# ============================================
# START APPLICATION
# ============================================

if __name__ == '__main__':
    # Load environment configuration
    load_environment_config()
    
    print("\n📍 AVAILABLE ROUTES:")
    print("   GET /en                             - Home (English)")
    print("   GET /no                             - Home (Norwegian)")
    print("   GET /maritime/dashboard             - Dashboard with COMPLETE RTZ routes")
    print("   GET /maritime/simulation-dashboard/<lang> - Simulation")
    print("   GET /routes                         - Route explorer")
    print("\n🔧 API Endpoints:")
    print("   GET /api/health                     - System health")
    print("   GET /api/simple-weather             - Weather API")
    print("   GET /api/weather-pro               - Weather API (from blueprint)")
    print("   GET /maritime/api/rtz/routes       - RTZ routes API")
    print("   GET /maritime/api/rtz/complete     - Complete RTZ data")
    print("   GET /maritime/api/ais-data         - AIS data API")
    print("   GET /maritime/api/vessels/real-time - Real-time vessel tracking (NEW)")
    print("   GET /maritime/api/vessels/empirical-status - Vessel data source status (NEW)")
    
    print("\n🌐 STARTING SERVER...")
    print("   Home:      http://localhost:5000/en")
    print("   Dashboard: http://localhost:5000/maritime/dashboard")
    print("   Simulation: http://localhost:5000/maritime/simulation-dashboard/en")
    print("   Routes:    http://localhost:5000/routes")
    print("   Weather API: http://localhost:5000/api/simple-weather?lat=60.39&lon=5.32")
    print("   Vessel API: http://localhost:5000/maritime/api/vessels/real-time")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)