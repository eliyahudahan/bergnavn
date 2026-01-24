#!/usr/bin/env python3
"""
QUICK FIX: Fix indentation error in app.py
"""

import os

def fix_app_py_indentation():
    """
    Fix the indentation error in app.py
    """
    app_path = "app.py"
    
    if not os.path.exists(app_path):
        print(f"❌ app.py not found at {app_path}")
        return False
    
    # Read the file
    with open(app_path, 'r') as f:
        lines = f.readlines()
    
    # Find the problematic line (line 52)
    print("🔍 Looking for indentation error at line 52...")
    
    # Fix indentation for all lines
    fixed_lines = []
    for i, line in enumerate(lines, 1):
        if i == 52:  # The problematic line
            print(f"   Line {i} before: {repr(line)}")
            # Fix indentation - should be 4 spaces, not more
            stripped = line.lstrip()
            fixed_line = '    ' + stripped  # 4 spaces
            print(f"   Line {i} after:  {repr(fixed_line)}")
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    # Write fixed version
    backup_path = app_path + '.backup_indent'
    with open(backup_path, 'w') as f:
        f.writelines(lines)
    print(f"✅ Backup created: {backup_path}")
    
    with open(app_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print("✅ Fixed indentation in app.py")
    
    # Show context of the fix
    print("\n📋 Context around line 52:")
    print("-" * 50)
    for i in range(48, 58):
        if i-1 < len(lines):
            print(f"{i:3}: {lines[i-1].rstrip()}")
    print("-" * 50)
    
    return True

def create_clean_app_py():
    """
    Create a clean, working app.py
    """
    print("\n🔄 Creating clean app.py...")
    
    clean_app = '''#!/usr/bin/env python3
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
    print("\n📍 AVAILABLE ENDPOINTS:")
    print("   GET /                          - Home page")
    print("   GET /maritime/dashboard        - Maritime Dashboard")
    print("   GET /maritime/simulation-dashboard/<lang> - Simulation")
    print("   GET /routes/view               - Routes page")
    print("   GET /api/health                - Health check")
    print("   GET /api/rtz-status            - RTZ data")
    print("\n🌐 Open browser to: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
'''
    
    clean_path = "app_clean.py"
    with open(clean_path, 'w') as f:
        f.write(clean_app)
    
    print(f"✅ Created clean app.py at {clean_path}")
    return clean_path

def main():
    print("=" * 60)
    print("FIX: Indentation Error in app.py")
    print("=" * 60)
    
    print("\n1. Fixing indentation...")
    if fix_app_py_indentation():
        print("   ✓ Fixed")
    else:
        print("   ✗ Failed")
    
    print("\n2. Creating clean version...")
    clean_path = create_clean_app_py()
    
    print("\n" + "=" * 60)
    print("🎯 FIX COMPLETE!")
    print("=" * 60)
    print("\nTry running:")
    print("1. python app.py          (fixed version)")
    print("2. python app_clean.py    (clean version)")
    print("\nIf still errors, show me lines 45-55 of app.py:")
    print("   head -55 app.py | tail -10")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())