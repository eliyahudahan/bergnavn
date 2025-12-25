#!/usr/bin/env python3
"""
Verify the health endpoint fix works correctly
"""

from app import app

print("✅ Verifying health endpoint fix...")
print("=" * 50)

# Test 1: Check the file was created correctly
import os
if os.path.exists('backend/routes/system_routes.py'):
    print("📁 system_routes.py exists")
    
    # Check content
    with open('backend/routes/system_routes.py', 'r') as f:
        content = f.read()
        
    if 'from sqlalchemy import text' in content:
        print("✅ 'text' import found")
    else:
        print("❌ 'text' import missing")
        
    if "text('SELECT 1')" in content:
        print("✅ SQL query uses text() wrapper")
    else:
        print("❌ SQL query not using text() wrapper")
else:
    print("❌ system_routes.py not found")

print("\n" + "=" * 50)
print("🧪 Testing endpoint...")

# Test 2: Actually test the endpoint
with app.test_client() as client:
    response = client.get('/health')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.get_json()
        print(f"✅ SUCCESS! Response: {data}")
        print("\n🎉 Health endpoint is FIXED!")
    else:
        print(f"❌ FAILED! Response: {response.data[:200]}...")
        print("\n⚠️  Health endpoint still broken")

print("\n" + "=" * 50)
