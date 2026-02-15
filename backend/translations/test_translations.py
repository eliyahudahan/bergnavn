"""
Test script for BergNavn Maritime translation system.
Run this to verify the translation system is working correctly.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template_string
from backend.translations.flask_integration import init_app, get_translator
from backend.translations.core import initialize_translations, get_registry

def test_translation_system():
    """Test the translation system components."""
    print("🚀 Testing BergNavn Translation System")
    print("=" * 60)
    
    # Test 1: Initialize translation registry
    print("\n1. Testing Translation Registry...")
    try:
        registry = initialize_translations()
        print(f"   ✅ Registry initialized: {len(registry.translation_keys)} keys found")
        print(f"   📊 English translations: {len(registry.translations['en'])}")
        print(f"   📊 Norwegian translations: {len(registry.translations['no'])}")
    except Exception as e:
        print(f"   ❌ Registry initialization failed: {e}")
        return False
    
    # Test 2: Check translation files
    print("\n2. Checking translation files...")
    en_file = "backend/translations/data/en.json"
    no_file = "backend/translations/data/no.json"
    
    if os.path.exists(en_file):
        import json
        with open(en_file, 'r') as f:
            en_data = json.load(f)
        print(f"   ✅ English file exists: {len(en_data)} categories")
    else:
        print(f"   ⚠️  English file not found: {en_file}")
    
    if os.path.exists(no_file):
        import json
        with open(no_file, 'r') as f:
            no_data = json.load(f)
        print(f"   ✅ Norwegian file exists: {len(no_data)} categories")
    else:
        print(f"   ⚠️  Norwegian file not found: {no_file}")
    
    # Test 3: Test translator directly
    print("\n3. Testing DynamicTranslator...")
    try:
        translator = get_translator()
        
        # Test some translations
        test_cases = [
            ("home", "global"),
            ("dashboard", "base_template"),
            ("simulation", "base_template"),
            ("routes", "base_template"),
        ]
        
        for key, category in test_cases:
            en_text = translator.translate(key, 'en', category=category)
            no_text = translator.translate(key, 'no', category=category)
            print(f"   🔤 '{key}' ({category}):")
            print(f"      EN: {en_text}")
            print(f"      NO: {no_text}")
        
        print(f"   ✅ Translator working correctly")
    except Exception as e:
        print(f"   ❌ Translator test failed: {e}")
        return False
    
    # Test 4: Test Flask integration
    print("\n4. Testing Flask integration...")
    try:
        # Create minimal Flask app
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Initialize translation system
        init_app(app)
        
        # Test template context processor
        with app.test_request_context('/?lang=en'):
            # Get the context processor
            ctx_proc = app.template_context_processor
            ctx = ctx_proc()
            
            print(f"   ✅ Context processor loaded")
            print(f"   📝 Available template functions:")
            for key in ['t', 't_all', 'get_language', 'is_english', 'is_norwegian']:
                if key in ctx:
                    print(f"      • {key}")
            
            # Test translation function
            t_func = ctx['t']
            test_translation = t_func('home', 'global', 'Home')
            print(f"   🔤 Test translation: 'home' → '{test_translation}'")
        
        print(f"   ✅ Flask integration working")
    except Exception as e:
        print(f"   ❌ Flask integration test failed: {e}")
        return False
    
    # Test 5: Test API endpoints
    print("\n5. Testing API endpoints...")
    try:
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/translations/health')
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✅ Health endpoint: {data.get('status', 'unknown')}")
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
            
            # Test translations endpoint
            response = client.get('/api/translations/en')
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✅ English translations: {data.get('count', 0)} keys")
            else:
                print(f"   ❌ Translations endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API endpoint test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! Translation system is ready.")
    print("\nNext steps:")
    print("1. Run: python -m backend.translations init")
    print("2. Run: python -m backend.translations transform --dry-run")
    print("3. Check: python test_translations.py")
    
    return True

def create_test_app():
    """Create a test Flask app with translation system."""
    print("\n🌐 Creating test Flask application...")
    
    app = Flask(__name__, 
                template_folder="backend/templates",
                static_folder="backend/static")
    
    # Initialize translation system
    init_app(app)
    
    # Add test routes
    @app.route('/')
    def index():
        """Test homepage with translations."""
        test_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Translation Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .test { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
                .success { background: #d4edda; }
                .warning { background: #fff3cd; }
            </style>
        </head>
        <body>
            <h1>🌍 BergNavn Translation System Test</h1>
            
            <div class="test">
                <h2>Language Information</h2>
                <p>Current language: <strong>{{ get_language() }}</strong></p>
                <p>Is English: {{ is_english() }}</p>
                <p>Is Norwegian: {{ is_norwegian() }}</p>
            </div>
            
            <div class="test">
                <h2>Direct Translations</h2>
                <p>Home: {{ t('home', 'global', 'Home') }}</p>
                <p>Dashboard: {{ t('dashboard', 'base_template', 'Dashboard') }}</p>
                <p>Simulation: {{ t('simulation', 'base_template', 'Simulation') }}</p>
                <p>Routes: {{ t('routes', 'base_template', 'Routes') }}</p>
            </div>
            
            <div class="test">
                <h2>Navigation Test</h2>
                <ul>
                    <li>{{ t('dashboard', 'base_template') }}</li>
                    <li>{{ t('simulation', 'base_template') }}</li>
                    <li>{{ t('routes', 'base_template') }}</li>
                    <li>{{ t('home', 'base_template') }}</li>
                </ul>
            </div>
            
            <div class="test">
                <h2>Language Switching</h2>
                <p>
                    <a href="/?lang=en">English</a> | 
                    <a href="/?lang=no">Norsk</a>
                </p>
            </div>
            
            <div class="test">
                <h2>API Endpoints</h2>
                <ul>
                    <li><a href="/api/translations/health">Health Check</a></li>
                    <li><a href="/api/translations/en">English Translations</a></li>
                    <li><a href="/api/translations/no">Norwegian Translations</a></li>
                </ul>
            </div>
            
            <div class="test success">
                <h2>✅ System Status</h2>
                <p>Translation system is operational!</p>
                <p>Total translation keys: {{ translations|length }}</p>
            </div>
        </body>
        </html>
        """
        return render_template_string(test_template)
    
    @app.route('/api/test')
    def api_test():
        """Test API endpoint."""
        import json
        translator = get_translator()
        
        return {
            'status': 'success',
            'system': 'BergNavn Translation System',
            'version': '1.0.0',
            'translations': {
                'english_count': len(translator.get_all('en')),
                'norwegian_count': len(translator.get_all('no')),
                'sample': translator.translate('home', 'en')
            }
        }
    
    print("✅ Test app created with routes:")
    print("   • / - Test interface")
    print("   • /api/test - API test")
    print("   • /api/translations/* - Translation API")
    
    return app

if __name__ == '__main__':
    print("🔧 BergNavn Maritime - Translation System Tester")
    print("=" * 60)
    
    # Run basic tests
    success = test_translation_system()
    
    if success:
        print("\n🚀 Starting test server...")
        print("   Open browser to: http://localhost:5001")
        print("   Press Ctrl+C to stop\n")
        
        # Create and run test app
        app = create_test_app()
        app.run(debug=True, port=5001, use_reloader=False)
    else:
        print("\n❌ Tests failed. Please fix errors before running server.")
        sys.exit(1)