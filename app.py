#!/usr/bin/env python3
"""
BergNavn Maritime Intelligence Platform - PRODUCTION READY
FIXED: Single blueprint registration, no duplicates, clean architecture
All maritime logic in blueprint only - app.py only registers blueprints
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
print("🚢 BERGENAVN MARITIME - PRODUCTION READY")
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
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    logger.warning("⚠️ SECRET_KEY not found in environment, using development key")
    secret_key = 'bergnavn-development-secure-key-2025'
app.config['SECRET_KEY'] = secret_key
print("✅ SECRET_KEY configured")

# ============================================
# LOAD ENVIRONMENT CONFIGURATION
# ============================================
app.config['BARENTSWATCH_CLIENT_ID'] = os.environ.get('BARENTSWATCH_CLIENT_ID', '')
app.config['BARENTSWATCH_CLIENT_SECRET'] = os.environ.get('BARENTSWATCH_CLIENT_SECRET', '')
app.config['MET_USER_AGENT'] = os.environ.get('MET_USER_AGENT', 'BergNavn/1.0 (contact@bergnavn.no)')
app.config['MET_LAT'] = os.environ.get('MET_LAT', '60.39')
app.config['MET_LON'] = os.environ.get('MET_LON', '5.32')

print("\n🔧 Environment Configuration:")
print(f"   BARENTSWATCH_CLIENT_ID: {'Set' if app.config['BARENTSWATCH_CLIENT_ID'] else 'Not set'}")
print(f"   MET_USER_AGENT: {'Set' if app.config['MET_USER_AGENT'] else 'Not set'}")

# ============================================
# REGISTER BLUEPRINTS - SINGLE REGISTRATION ONLY!
# ============================================
print("\n📋 Registering blueprints...")

# ----- Main Blueprint (Home, About, Legal) -----
try:
    from backend.routes.main_routes import main_bp
    app.register_blueprint(main_bp)
    print("✅ Registered: main_bp (/)")
except Exception as e:
    print(f"⚠️ Could not register main_bp: {e}")

# ----- Maritime Blueprint (ALL maritime routes - CRITICAL!) -----
try:
    from backend.routes.maritime_routes import maritime_bp
    app.register_blueprint(maritime_bp, url_prefix='/maritime')
    print("✅ Registered: maritime_bp (/maritime)")
    print(f"   Blueprint name: {maritime_bp.name}")
    print(f"   URL prefix: /maritime")
except ImportError as e:
    print(f"❌ CRITICAL: Could not import maritime_bp: {e}")
    print(f"   Check that backend/routes/maritime_routes.py exists")
except Exception as e:
    print(f"❌ CRITICAL: Could not register maritime_bp: {e}")

# ----- Routes Blueprint (Optional - can be removed) -----
try:
    from backend.routes.route_routes import routes_bp
    app.register_blueprint(routes_bp, url_prefix='/routes')
    print("✅ Registered: routes_bp (/routes)")
except Exception as e:
    print(f"⚠️ Could not register routes_bp: {e}")

# ----- Weather API Blueprint -----
try:
    from backend.routes.api_weather import bp as api_weather_bp
    app.register_blueprint(api_weather_bp, url_prefix='/api')
    print("✅ Registered: api_weather_bp (/api)")
except Exception as e:
    print(f"⚠️ Could not register api_weather_bp: {e}")

# ============================================
# LANGUAGE ROUTES - ONLY THESE IN APP.PY!
# ============================================

@app.route('/<lang>')
def home_with_lang(lang):
    """
    Home page with language parameter.
    Supports English (en) and Norwegian (no).
    """
    if lang in ['en', 'no']:
        session['lang'] = lang
        return render_template('home.html', lang=lang)
    # Default to English
    return '<script>window.location.href="/en";</script>'

@app.route('/')
def home():
    """Home page redirect to English version."""
    return '<script>window.location.href="/en";</script>'

# ============================================
# HEALTH CHECK - SIMPLE ENDPOINT FOR DEBUGGING
# ============================================

@app.route('/api/health')
def health_check():
    """Simple health check endpoint - verifies app is running."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'blueprints': list(app.blueprints.keys()),
        'maritime_blueprint_registered': 'maritime' in app.blueprints,
        'message': 'All systems operational'
    })

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page."""
    return '''
    <div style="text-align: center; padding: 50px; font-family: Arial;">
        <h1>🚢 404 - Route Not Found</h1>
        <p>The maritime route you're looking for doesn't exist.</p>
        <p><strong>Working pages:</strong></p>
        <p>
            <a href="/en">🏠 Home</a> |
            <a href="/maritime/dashboard">📊 Dashboard</a> |
            <a href="/maritime/simulation-dashboard/en">🚢 Simulation</a>
        </p>
        <p><small>BergNavn Maritime Intelligence Platform</small></p>
    </div>
    ''', 404

@app.errorhandler(500)
def internal_error(e):
    """Custom 500 error page."""
    logger.error(f"500 Error: {e}")
    return '''
    <div style="text-align: center; padding: 50px; font-family: Arial;">
        <h1>⚓ 500 - Internal Server Error</h1>
        <p>Something went wrong with the maritime systems.</p>
        <p>The technical team has been notified.</p>
        <p><a href="/en">Return to Home Port</a></p>
    </div>
    ''', 500

# ============================================
# START APPLICATION
# ============================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("📍 AVAILABLE ROUTES")
    print("=" * 60)
    print("\n📌 Web Pages:")
    print("   GET /                             - Redirect to /en")
    print("   GET /en                          - Home (English)")
    print("   GET /no                          - Home (Norwegian)")
    print("   GET /maritime/dashboard          - Maritime Dashboard")
    print("   GET /maritime/simulation-dashboard/<lang> - Simulation")
    
    print("\n🔌 API Endpoints (via blueprints):")
    print("   GET /api/health                  - System health")
    print("   GET /maritime/api/health         - Maritime health")
    print("   GET /maritime/api/ais-data       - AIS vessel data")
    print("   GET /maritime/api/weather-dashboard - Weather data")
    print("   GET /maritime/api/rtz/routes     - RTZ routes")
    print("   GET /maritime/api/rtz-status     - RTZ status")
    
    print("\n🌐 SERVER STARTING...")
    print("   Home:      http://localhost:5000/en")
    print("   Dashboard: http://localhost:5000/maritime/dashboard")
    print("   Simulation: http://localhost:5000/maritime/simulation-dashboard/en")
    print("   Health:    http://localhost:5000/api/health")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)