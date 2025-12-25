from app import app

print("🔧 Debugging Flask server...")
print(f"Debug mode: {app.debug}")

# בדוק את routes
print("\n📋 Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.endpoint}: {rule.rule}")

# בדוק את health endpoint
print("\n🧪 Testing health endpoint...")
with app.test_client() as client:
    response = client.get('/health')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data[:200]}...")
