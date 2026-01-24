#!/usr/bin/env python3
"""
BergNavn Maritime Platform - Minimal Working Version
"""

import os
import sys
from flask import Flask, render_template
from flask_cors import CORS

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

app = Flask(__name__, 
            template_folder='backend/templates',
            static_folder='backend/static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
CORS(app)

# Register blueprints
try:
    from backend.routes.main_routes import main_bp
    from backend.routes.maritime_routes import maritime_bp
    from backend.routes.route_routes import routes_bp
    from backend.routes.ml_routes import ml_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(maritime_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(ml_bp)
    
    print("✅ All blueprints registered successfully")
    
except Exception as e:
    print(f"⚠️ Error registering blueprints: {e}")
    print("⚠️ Running with minimal functionality")

@app.route('/')
def index():
    """Main index page"""
    return render_template('home.html', lang='en')

@app.route('/test')
def test():
    """Test route"""
    return '🚢 BergNavn Maritime Platform is running!'

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 BergNavn Maritime Platform - Minimal Version")
    print("=" * 60)
    print("🌐 Open browser to: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000/maritime/dashboard")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
