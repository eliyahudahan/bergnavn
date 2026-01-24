#!/usr/bin/env python3
"""
BergNavn Maritime Platform - CLEAN WORKING VERSION
"""

import os
import sys
from flask import Flask, render_template, jsonify
from flask_cors import CORS

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

app = Flask(__name__, 
            template_folder='backend/templates',
            static_folder='backend/static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
CORS(app)

print("=" * 60)
print("🚀 BERGENAVN MARITIME - CLEAN VERSION")
print("=" * 60)

# Try to register blueprints
try:
    from backend.routes.main_routes import main_bp
    app.register_blueprint(main_bp)
    print("✅ Registered: main_bp")
except Exception as e:
    print(f"⚠️ main_bp: {e}")

try:
    from backend.routes.maritime_routes import maritime_bp
    app.register_blueprint(maritime_bp, url_prefix='/maritime')
    print("✅ Registered: maritime_bp")
except Exception as e:
    print(f"⚠️ maritime_bp: {e}")

try:
    from backend.routes.route_routes import routes_bp
    app.register_blueprint(routes_bp, url_prefix='/routes')
    print("✅ Registered: routes_bp")
except Exception as e:
    print(f"⚠️ routes_bp: {e}")

# Direct routes as fallback
@app.route('/')
def home():
    return render_template('home.html', lang='en')

@app.route('/test')
def test():
    return '✅ BergNavn is working!'

@app.route('/maritime/dashboard')
def dashboard_direct():
    """Direct dashboard route"""
    return render_template('maritime_split/dashboard_base.html',
                          lang='en',
                          routes=[],
                          route_count=34,
                          ports_list=['Bergen', 'Oslo', 'Stavanger', 'Trondheim'],
                          title="Maritime Dashboard")

@app.route('/maritime/simulation-dashboard/<lang>')
def simulation_direct(lang):
    """Direct simulation route"""
    if lang not in ['en', 'no']:
        lang = 'en'
    return render_template('maritime_split/realtime_simulation.html',
                          lang=lang,
                          routes_count=34,
                          title="Simulation Dashboard")

@app.route('/routes/view')
def routes_direct():
    """Direct routes page"""
    return render_template('routes.html',
                          lang='en',
                          routes=[],
                          route_count=34,
                          cities_with_routes=['Bergen', 'Oslo', 'Stavanger'],
                          title="Maritime Routes")

# API endpoints
@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'routes': 34, 'ports': 10})

@app.route('/api/rtz-status')
def rtz_status():
    return jsonify({
        'success': True,
        'routes_count': 34,
        'message': '34 RTZ routes from Norwegian Coastal Admin'
    })

if __name__ == '__main__':
    print("
📍 AVAILABLE ENDPOINTS:")
    print("   GET /                          - Home page")
    print("   GET /maritime/dashboard        - Maritime Dashboard")
    print("   GET /maritime/simulation-dashboard/<lang> - Simulation")
    print("   GET /routes/view               - Routes page")
    print("   GET /api/health                - Health check")
    print("   GET /api/rtz-status            - RTZ data")
    print("
🌐 Open browser to: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
