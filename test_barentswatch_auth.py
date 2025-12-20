import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote

# Load .env file
env_path = Path('/home/framg/dev/bergnavn') / '.env'
load_dotenv(dotenv_path=env_path)

# Get credentials
client_id = os.getenv('BARENTSWATCH_CLIENT_ID')
client_secret = os.getenv('BARENTSWATCH_CLIENT_SECRET')

if not client_id or not client_secret:
    print("❌ ERROR: Could not find credentials in .env file")
    print(f"Client ID found: {bool(client_id)}")
    print(f"Client Secret found: {bool(client_secret)}")
    exit(1)

print(f"✓ Found Client ID: {client_id}")
print(f"✓ Found Client Secret: {'*' * len(client_secret)} (length: {len(client_secret)})")

# Remove quotes if they exist
client_id = client_id.strip('"\'')
client_secret = client_secret.strip('"\'')

print(f"\nCleaned Client ID: {client_id}")
print(f"Cleaned Client Secret length: {len(client_secret)}")

# Test authentication
url = "https://id.barentswatch.no/connect/token"

data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'api',
    'grant_type': 'client_credentials'
}

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

print(f"\nTesting authentication with BarentsWatch...")
print(f"URL: {url}")

try:
    response = requests.post(url, data=data, headers=headers, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print("✅ SUCCESS! Authentication successful!")
        print(f"Token type: {token_data.get('token_type')}")
        print(f"Expires in: {token_data.get('expires_in')} seconds")
        print(f"Access token (first 50 chars): {token_data.get('access_token', '')[:50]}...")
        
        # Save to .env
        with open(env_path, 'a') as f:
            f.write(f'\nBARENTSWATCH_ACCESS_TOKEN="{token_data.get("access_token")}"')
            f.write(f'\nBARENTSWATCH_TOKEN_EXPIRES={token_data.get("expires_in")}')
        
        print(f"\n✅ Token saved to .env file!")
        
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Try with URL encoded client_id
        print("\nTrying with URL encoded client_id...")
        encoded_client_id = quote(client_id, safe='')
        data['client_id'] = encoded_client_id
        
        response2 = requests.post(url, data=data, headers=headers, timeout=10)
        print(f"Status Code (encoded): {response2.status_code}")
        print(f"Response: {response2.text}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
