from app import app
import json

print("🌐 Proper API Test (using test client)")
print("=" * 50)

with app.test_client() as client:
    endpoints = [
        ("/health", "Health check"),
        ("/api/routes", "Routes API"),
        ("/api/cruises", "Cruises API"),
        ("/api/weather/overview", "Weather overview"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = client.get(endpoint)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - {description}")
                
                # Try to parse JSON
                try:
                    data = response.get_json()
                    if isinstance(data, list):
                        print(f"   ↳ Found {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"   ↳ JSON response with keys: {list(data.keys())[:3]}...")
                except:
                    print(f"   ↳ Response: {response.data[:100]}...")
                    
            elif response.status_code == 404:
                print(f"⚠️  {endpoint} - Not found (404)")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)[:50]}")

print("\n" + "=" * 50)
