from app import app
import json

print("🚀 FINAL SYSTEM TEST - All endpoints with correct URLs")
print("=" * 60)

with app.test_client() as client:
    # Group endpoints by functionality
    endpoints_by_category = {
        "Health & System": [
            ("/health", "Health check"),
            ("/api/check-api-keys", "API Keys status"),
            ("/maritime/api/system-status", "System status"),
        ],
        "Routes & RTZ": [
            ("/routes/api/routes", "All routes"),
            ("/maritime/api/rtz/routes", "RTZ routes"),
            ("/api/ml/available-routes", "ML available routes"),
        ],
        "Maritime Data": [
            ("/maritime/api/weather", "Weather data"),
            ("/maritime/api/barentswatch/hazards", "Hazards data"),
            ("/maritime/api/risk-assessment", "Risk assessment"),
        ],
        "Cruises & Voyages": [
            ("/cruises/", "All cruises"),
            ("/maritime/dashboard", "Maritime dashboard"),
        ],
        "Other Services": [
            ("/weather/api/maritime-weather", "Maritime weather API"),
            ("/dashboard/api/metrics", "Dashboard metrics"),
        ]
    }
    
    results = {}
    
    for category, endpoint_list in endpoints_by_category.items():
        print(f"\n📊 {category}:")
        print("-" * 40)
        
        category_results = []
        
        for endpoint, description in endpoint_list:
            try:
                response = client.get(endpoint, timeout=5)
                
                if response.status_code == 200:
                    try:
                        data = response.get_json()
                        if isinstance(data, list):
                            item_count = len(data)
                            status = f"✅ {item_count} items"
                        elif isinstance(data, dict):
                            status = "✅ JSON object"
                        else:
                            status = "✅ Working"
                    except:
                        status = "✅ Working (non-JSON)"
                    
                    print(f"  {status}: {description}")
                    category_results.append((endpoint, True, status))
                    
                elif response.status_code == 404:
                    print(f"  ⚠️  Not found: {description}")
                    category_results.append((endpoint, False, "404"))
                elif response.status_code == 500:
                    print(f"  ❌ Server error: {description}")
                    category_results.append((endpoint, False, "500"))
                else:
                    print(f"  ⚠️  Status {response.status_code}: {description}")
                    category_results.append((endpoint, False, f"{response.status_code}"))
                    
            except Exception as e:
                print(f"  ❌ Error: {description} - {str(e)[:30]}")
                category_results.append((endpoint, False, f"Error: {str(e)[:15]}"))
        
        results[category] = category_results
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY:")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, category_results in results.items():
        category_total = len(category_results)
        category_passed = sum(1 for _, passed, _ in category_results if passed)
        
        total_tests += category_total
        passed_tests += category_passed
        
        status = "✅" if category_passed == category_total else "⚠️" if category_passed > 0 else "❌"
        print(f"{status} {category}: {category_passed}/{category_total}")
    
    print("-" * 60)
    overall_status = "✅ EXCELLENT" if passed_tests == total_tests else "⚠️  GOOD" if passed_tests >= total_tests * 0.7 else "❌ NEEDS WORK"
    print(f"Overall: {passed_tests}/{total_tests} endpoints working ({overall_status})")
    
    # Show critical endpoints status
    print("\n🔑 CRITICAL ENDPOINTS STATUS:")
    critical_endpoints = [
        ("/health", "Health check"),
        ("/routes/api/routes", "Routes API"),
        ("/maritime/api/weather", "Weather API"),
        ("/api/check-api-keys", "API Keys"),
    ]
    
    for endpoint, description in critical_endpoints:
        try:
            response = client.get(endpoint, timeout=3)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {description}: HTTP {response.status_code}")
        except:
            print(f"❌ {description}: Failed to connect")

print("\n" + "=" * 60)
