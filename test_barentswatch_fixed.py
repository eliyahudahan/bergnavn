import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote

# Load .env file
env_path = Path('/home/framg/dev/bergnavn') / '.env'
load_dotenv(dotenv_path=env_path)

# Get credentials
client_id = os.getenv('BARENTSWATCH_CLIENT_ID').strip('"\'')
client_secret = os.getenv('BARENTSWATCH_CLIENT_SECRET').strip('"\'')

print(f"Client ID: {client_id}")
print(f"Client Secret length: {len(client_secret)}")

# Try different scopes that BarentsWatch might accept
scopes_to_try = [
    'ais',           # Most likely for AIS data
    'barentswatch',  # General API access
    'offline_access', # Sometimes needed
    'openid',        # OpenID scope
    'profile',       # Profile scope
    '',              # No scope (sometimes works)
]

url = "https://id.barentswatch.no/connect/token"

for scope in scopes_to_try:
    print(f"\n{'='*60}")
    print(f"Testing with scope: '{scope if scope else '(empty)'}'")
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    
    if scope:  # Add scope only if not empty
        data['scope'] = scope
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ SUCCESS!")
            print(f"Token type: {token_data.get('token_type')}")
            print(f"Scope returned: {token_data.get('scope', 'not specified')}")
            print(f"Expires in: {token_data.get('expires_in')} seconds")
            print(f"Access token (first 50 chars): {token_data.get('access_token', '')[:50]}...")
            
            # Save to .env
            with open(env_path, 'a') as f:
                f.write(f'\nBARENTSWATCH_ACCESS_TOKEN="{token_data.get("access_token")}"')
                f.write(f'\nBARENTSWATCH_TOKEN_EXPIRES={token_data.get("expires_in")}')
            
            print(f"\n✅ Token saved to .env file!")
            break
            
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

print(f"\n{'='*60}")
print("Testing completed.")

# If all fail, check BarentsWatch documentation
if response.status_code != 200:
    print("\n💡 TIPS:")
    print("1. Check BarentsWatch documentation for correct scope")
    print("2. Make sure your app is activated at: https://www.barentswatch.no/developer/")
    print("3. Try registering a new app")
