from app import app
import json

print("🌐 Correct API Test - Matching actual routes")
print("=" * 60)

with app.test_client() as client:
    # רשימת endpoints אמיתיים לפי flask routes
    endpoints = [
        ("/health", "Health check"),
        ("/routes/api/routes", "Routes API"),  # התיקון כאן!
        ("/cruises/", "Cruises API"),  # התיקון כאן!
        ("/maritime/api/weather", "Weather API"),  # התיקון כאן!
        ("/api/check-api-keys", "API Keys check"),
        ("/maritime/api/rtz/routes", "RTZ Routes"),
        ("/maritime/api/system-status", "System status"),
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
                        if data and endpoint == "/routes/api/routes":
                            # Show sample route
                            first = data[0]
                            print(f"   ↳ Sample: {first.get('name', 'No name')}")
                            print(f"   ↳ Source: {first.get('source', 'No source')}")
                    elif isinstance(data, dict):
                        keys = list(data.keys())[:3]
                        print(f"   ↳ JSON keys: {keys}...")
                except:
                    if response.data:
                        print(f"   ↳ Response: {response.data[:100]}...")
                    else:
                        print(f"   ↳ Empty response")
                        
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Not found (404)")
            elif response.status_code == 500:
                print(f"❌ {endpoint} - Server error (500)")
                # ננסה לראות את השגיאה
                try:
                    print(f"   ↳ Error: {response.data[:200]}...")
                except:
                    pass
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)[:50]}")

print("\n" + "=" * 60)
print("📋 Testing additional critical endpoints...")

# בדיקות נוספות
additional_endpoints = [
    ("/maritime/api/ais-status", "AIS Status"),
    ("/maritime/api/risk-assessment", "Risk Assessment"),
    ("/api/ml/available-routes", "ML Routes"),
]

for endpoint, description in additional_endpoints:
    try:
        response = client.get(endpoint, timeout=2)
        status = "✅" if response.status_code == 200 else "⚠️ "
        print(f"{status} {endpoint} - {description} ({response.status_code})")
    except Exception as e:
        print(f"❌ {endpoint} - Error: {str(e)[:30]}")

print("\n" + "=" * 60)
