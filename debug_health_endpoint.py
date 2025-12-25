from app import app
import traceback

print("🔧 Debugging /health endpoint")
print("=" * 50)

# בדוק מה יש ב-blueprint health
print("Looking for health blueprint...")
for name, blueprint in app.blueprints.items():
    if name == 'health_bp' or 'health' in name:
        print(f"Found blueprint: {name}")
        print(f"  Has {len(blueprint.deferred_functions)} functions")

# נסה לגשת ישירות לפונקציה
try:
    from backend.routes.system_routes import health_check
    print("\n✅ health_check function imported successfully")
except Exception as e:
    print(f"\n❌ Cannot import health_check: {e}")
    traceback.print_exc()

# נסה לראות את השגיאה
print("\n🧪 Testing health endpoint with error handling...")
with app.test_client() as client:
    try:
        response = client.get('/health')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 500:
            print("Trying to get error details...")
            # Flask בדרך כלל לא מראה את השגיאה ב-response.data
            # צריך לראות את הלוגים
            print("Check the Flask logs for error details")
            
    except Exception as e:
        print(f"Request failed: {e}")

print("\n" + "=" * 50)
