import requests
import json

BASE_URL = "http://localhost:5000"

endpoints = [
    "/health",
    "/api/routes",
    "/api/cruises",
    "/maritime/weather/overview"
]

print("🌐 Testing API endpoints...")
print("=" * 50)

for endpoint in endpoints:
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ {endpoint} - Status: {response.status_code}")
            
            # For routes endpoint, check data structure
            if endpoint == "/api/routes":
                data = response.json()
                if isinstance(data, list):
                    print(f"   ↳ Found {len(data)} routes")
                    if data:
                        first_route = data[0]
                        print(f"   ↳ Sample: {first_route.get('name', 'No name')}")
        else:
            print(f"⚠️  {endpoint} - Status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {endpoint} - Connection refused (server not running)")
    except Exception as e:
        print(f"❌ {endpoint} - Error: {str(e)[:50]}...")

print("\n" + "=" * 50)
print("API test completed")
