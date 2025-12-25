#!/usr/bin/env python3
"""
Simple test to discover which BarentsWatch endpoints are available with your credentials.
Run from project root: python test_barentswatch.py
"""

import requests
import json
import time
from datetime import datetime

def get_token():
    """Get fresh token"""
    token_url = "https://id.barentswatch.no/connect/token"
    
    # Your credentials - update these
    client_id = "framgangsrik747@gmail.com:Bergnavn App"
    client_secret = "Stavanger-1125-API"
    
    # Try different scopes
    scopes = ['ais', 'api', 'barentswatch.api', 'openid', '']
    
    for scope in scopes:
        print(f"\n🔍 Testing scope: '{scope}'")
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        }
        
        if scope:
            data['scope'] = scope
        
        try:
            response = requests.post(token_url, data=data, timeout=10)
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                token_data = response.json()
                print(f"   ✅ SUCCESS! Token received")
                print(f"   Token type: {token_data.get('token_type')}")
                print(f"   Expires in: {token_data.get('expires_in')}s")
                print(f"   Actual scope in token: {token_data.get('scope', 'N/A')}")
                return token_data['access_token']
            else:
                print(f"   ❌ Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    return None

def test_endpoints(access_token):
    """Test various BarentsWatch endpoints"""
    api_base = "https://www.barentswatch.no/bwapi/"
    
    # Common endpoints to test
    endpoints = [
        # AIS related (most likely to work)
        'v1/ais/openpositions',  # AIS positions
        'v1/ais/latest',         # Latest AIS data
        'v1/ais/history',        # AIS history
        
        # Geodata endpoints (might not be accessible)
        'v1/geodata/download/aquaculture',
        'v1/geodata/download/cables',
        'v1/geodata/download/installations',
        
        # Other possible endpoints
        'v1/metoc/weather',      # Weather data
        'v1/metoc/forecast',     # Weather forecast
        'v1/vesseltraffic/portcalls',  # Port calls
    ]
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    results = {}
    
    for endpoint in endpoints:
        print(f"\n🌐 Testing: {endpoint}")
        url = f"{api_base}{endpoint}?format=json"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            results[endpoint] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'size': len(response.text) if response.text else 0
            }
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Works! Response size: {len(response.text)} bytes")
                # Show first 100 chars if JSON
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   Items: {len(data)}")
                        if data:
                            print(f"   First item: {json.dumps(data[0])[:100]}...")
                    elif isinstance(data, dict):
                        print(f"   Data keys: {list(data.keys())}")
                except:
                    print(f"   Content: {response.text[:100]}...")
            elif response.status_code == 401:
                print(f"   ❌ Unauthorized - token invalid for this endpoint")
            elif response.status_code == 403:
                print(f"   ❌ Forbidden - no permissions for this endpoint")
            elif response.status_code == 404:
                print(f"   ❌ Not Found - endpoint doesn't exist")
            else:
                print(f"   Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results[endpoint] = {'error': str(e), 'success': False}
        
        time.sleep(0.5)  # Be nice to the API
    
    return results

def main():
    print("=" * 60)
    print("BarentsWatch API Access Tester")
    print("=" * 60)
    
    # Step 1: Get token
    token = get_token()
    
    if not token:
        print("\n❌ Failed to get access token")
        return
    
    print("\n" + "=" * 60)
    print("Testing Endpoints")
    print("=" * 60)
    
    # Step 2: Test endpoints
    results = test_endpoints(token)
    
    # Step 3: Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    working = [k for k, v in results.items() if v.get('success')]
    failing = [k for k, v in results.items() if not v.get('success')]
    
    print(f"\n✅ Working endpoints ({len(working)}):")
    for endpoint in working:
        print(f"  • {endpoint}")
    
    print(f"\n❌ Failing endpoints ({len(failing)}):")
    for endpoint in failing:
        status = results[endpoint].get('status', 'Error')
        print(f"  • {endpoint} (Status: {status})")
    
    print(f"\n📊 Success rate: {len(working)}/{len(results)} ({len(working)/len(results)*100:.1f}%)")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'barentswatch_test_{timestamp}.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'working_endpoints': working,
            'all_results': results
        }, f, indent=2)
    
    print(f"\n📁 Results saved to: barentswatch_test_{timestamp}.json")

if __name__ == "__main__":
    main()