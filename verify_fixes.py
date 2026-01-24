#!/usr/bin/env python3
"""
Verification Script - Test all fixed endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, method='GET', data=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=5)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"🔍 Testing: {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Success: {data.get('success', 'N/A')}")
                print(f"   Message: {data.get('message', 'No message')}")
                if 'count' in data:
                    print(f"   Count: {data['count']}")
                return True
            except:
                print(f"   ✓ HTML response (not JSON)")
                return True
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 VERIFYING ALL FIXES")
    print("=" * 60)
    
    endpoints = [
        # Core pages
        ("/en", "Home page (English)"),
        ("/no", "Home page (Norwegian)"),
        ("/maritime/dashboard", "Dashboard page"),
        ("/maritime/simulation-dashboard/en", "Simulation dashboard"),
        
        # API endpoints
        ("/api/health", "Health check"),
        ("/maritime/api/health", "Maritime health"),
        ("/maritime/api/weather-dashboard", "Weather API"),
        ("/maritime/api/rtz/routes", "RTZ routes API - FIXED"),
        ("/maritime/api/ais-data", "AIS data API - FIXED"),
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        print(f"
📡 {description}")
        success = test_endpoint(endpoint)
        results.append((endpoint, description, success))
    
    print("
" + "=" * 60)
    print("📊 VERIFICATION RESULTS")
    print("=" * 60)
    
    successful = 0
    for endpoint, description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
        if success:
            successful += 1
    
    print(f"
🎯 Success rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    
    if successful == len(results):
        print("
🎉 ALL TESTS PASSED! All issues have been fixed.")
    else:
        print(f"
⚠️  {len(results) - successful} tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
