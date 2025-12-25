from app import app

print("🧪 Verifying health endpoint fix...")

with app.test_client() as client:
    # Test the fixed health endpoint
    response = client.get('/health')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.get_json()
        print(f"✅ Health endpoint works!")
        print(f"Data: {data}")
    else:
        print(f"❌ Health endpoint still broken")
        print(f"Error: {response.data[:200]}...")

print("\n" + "=" * 50)
