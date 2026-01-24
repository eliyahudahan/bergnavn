#!/usr/bin/env python3
"""
ACTIVATE RTZ NOW - Simple activation script
"""

import os
import sys
from pathlib import Path

print("🚢 ACTIVATING RTZ DASHBOARD")
print("=" * 50)

# Step 1: Check what we have
print("\n📊 Checking current status...")

backend_dir = Path("backend")
routes_file = backend_dir / "routes" / "maritime_routes.py"

if not routes_file.exists():
    print(f"❌ {routes_file} not found!")
    sys.exit(1)

print(f"✅ Found: {routes_file}")

# Step 2: Check if route already exists
with open(routes_file, 'r') as f:
    content = f.read()

if 'dashboard-fixed' in content:
    print("✅ Route '/dashboard-fixed' already exists")
else:
    print("❌ Route '/dashboard-fixed' not found in maritime_routes.py")
    print("💡 Need to add the route from dashboard_route_final.py")

# Step 3: Test the loader
print("\n🔍 Testing RTZ loader...")
try:
    sys.path.insert(0, str(backend_dir))
    from rtz_loader_fixed import rtz_loader
    
    print("✅ RTZ loader imported")
    
    data = rtz_loader.get_dashboard_data()
    print(f"📊 Found: {data['total_routes']} routes")
    print(f"📍 From: {data['cities_with_routes']} cities")
    print(f"🏙️ Ports: {len(data['ports_list'])}")
    
    print("\n📋 Norwegian ports loaded:")
    for port in data['ports_list']:
        print(f"  • {port}")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Step 4: Simple instructions
print("\n" + "=" * 50)
print("🎯 SIMPLE INSTRUCTIONS:")
print("\n1. Make sure Flask is running:")
print("   export FLASK_APP=app.py")
print("   flask run --port=5000 --host=0.0.0.0")
print("\n2. Visit these URLs:")
print("   📊 Dashboard: http://localhost:5000/maritime/dashboard-fixed")
print("   🔍 Status:    http://localhost:5000/maritime/api/rtz-status")
print("\n3. If '/dashboard-fixed' doesn't work:")
print("   Add the route from backend/dashboard_route_final.py")
print("   to backend/routes/maritime_routes.py")

# Quick check: is Flask running?
print("\n🔍 Checking if Flask is running...")
try:
    import requests
    response = requests.get('http://localhost:5000', timeout=2)
    if response.status_code == 200:
        print("✅ Flask is running on port 5000")
        print("🚀 Go to: http://localhost:5000/maritime/dashboard-fixed")
    else:
        print(f"⚠️  Flask responded with status: {response.status_code}")
except:
    print("❌ Flask not running on port 5000")
    print("💡 Start it with: flask run --port=5000")