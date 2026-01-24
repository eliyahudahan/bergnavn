#!/bin/bash
echo "🔍 TESTING BLUEPRINT REGISTRATION..."
echo "========================================"

echo "1. Testing app.py startup..."
python3 -c "
import os, sys
sys.path.insert(0, '.')
try:
    # Test imports
    from backend.routes.route_routes import routes_bp
    from backend.routes.main_routes import main_bp
    print('✅ Blueprints can be imported')
    
    # Test Flask app creation
    from flask import Flask
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'backend', 'templates'))
    
    # Try to register blueprints
    try:
        app.register_blueprint(routes_bp, url_prefix='/routes')
        print('✅ routes_bp can be registered')
    except Exception as e:
        print(f'⚠️  routes_bp registration: {e}')
    
    try:
        app.register_blueprint(main_bp)
        print('✅ main_bp can be registered')
    except Exception as e:
        print(f'⚠️  main_bp registration: {e}')
        
except ImportError as e:
    print(f'❌ Import error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "2. Checking route files..."
if [ -f "backend/routes/route_routes.py" ]; then
    echo "   ✅ route_routes.py exists"
    echo "   📊 Blueprint name: $(grep -o "routes_bp = Blueprint" backend/routes/route_routes.py | head -1)"
    echo "   📊 Route endpoints:"
    grep -n "@routes_bp.route" backend/routes/route_routes.py | head -5
else
    echo "   ❌ route_routes.py not found"
fi

echo ""
echo "3. Quick Flask test..."
python3 -c "
from flask import Flask
app = Flask(__name__)

# Define a test route
@app.route('/test-blueprint')
def test():
    return 'Blueprint test OK'

# Check URL map
app.config['SERVER_NAME'] = 'localhost:5000'
with app.test_request_context():
    for rule in app.url_map.iter_rules():
        if 'test' in rule.rule:
            print(f'   ✅ Test route registered: {rule.rule}')
"

echo ""
echo "========================================"
echo "🚀 TO START WITH BLUEPRINTS:"
echo "   python app.py"
echo ""
echo "📊 EXPECTED OUTPUT:"
echo "   ✅ Registered: main_bp (/)"
echo "   ✅ Registered: maritime_bp (/maritime)"
echo "   ✅ Registered: routes_bp (/routes)"
echo "   ✅ Registered: ml_bp (/ml)"
echo ""
echo "🌐 TEST THESE URLS:"
echo "   • http://localhost:5000/"
echo "   • http://localhost:5000/maritime/simulation"
echo "   • http://localhost:5000/routes"
echo "   • http://localhost:5000/routes/api/routes"
echo ""
echo "🔧 If routes don't work, check:"
echo "   1. Blueprint registration in app.py"
echo "   2. Template file exists: backend/templates/routes.html"
echo "   3. No syntax errors in route_routes.py"
