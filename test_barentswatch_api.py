import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path('/home/framg/dev/bergnavn') / '.env'
load_dotenv(dotenv_path=env_path)

token = os.getenv('BARENTSWATCH_ACCESS_TOKEN').strip('"\'')

print(f"Token length: {len(token)}")
print(f"Token (first 50 chars): {token[:50]}...")

# Test different BarentsWatch API endpoints
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json'
}

# Test 1: Get AIS data for Norwegian waters
print("\n" + "="*60)
print("Test 1: Getting AIS data for Norwegian waters...")

# Try different endpoints based on BarentsWatch documentation
endpoints = [
    "https://www.barentswatch.no/bwapi/v2/geodata/ais/openpositions",
    "https://www.barentswatch.no/bwapi/v2/geodata/ais/vesselpositions",
    "https://www.barentswatch.no/bwapi/v1/ais/openpositions",
    "https://www.barentswatch.no/bwapi/v1/ais/vesselpositions",
]

for endpoint in endpoints:
    print(f"\nTrying: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got {len(data) if isinstance(data, list) else 'data'} records")
            if data and isinstance(data, list):
                print(f"First vessel: {data[0].get('name', 'Unknown')} - MMSI: {data[0].get('mmsi', 'N/A')}")
            break
        else:
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {str(e)}")

# Test 2: Get hazard data (aquaculture, cables, etc.)
print("\n" + "="*60)
print("Test 2: Getting hazard data...")

hazard_endpoints = [
    "https://www.barentswatch.no/bwapi/v2/geodata/facilities",
    "https://www.barentswatch.no/bwapi/v2/geodata/aquaculture",
    "https://www.barentswatch.no/bwapi/v1/geodata/facilities",
]

for endpoint in hazard_endpoints:
    print(f"\nTrying: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got hazard data")
            if data and isinstance(data, list):
                print(f"First item type: {data[0].get('type', 'Unknown')}")
                print(f"Total items: {len(data)}")
            break
        else:
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {str(e)}")

print("\n" + "="*60)
print("API testing completed!")
