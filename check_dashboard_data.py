#!/usr/bin/env python3
"""
Check what data the dashboard is actually getting
"""

import os
import sys
from pathlib import Path

# Add backend to path
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
sys.path.insert(0, str(backend_dir))

print("🔍 CHECKING DASHBOARD DATA SOURCES")
print("=" * 50)

# Option 1: Check Database
print("\n1️⃣ Checking Database Routes...")
try:
    from app import create_app
    from backend.models.route import Route
    from backend.extensions import db
    
    app = create_app()
    with app.app_context():
        route_count = Route.query.count()
        print(f"✅ Routes in database 'routes' table: {route_count}")
        
        if route_count > 0:
            routes = Route.query.limit(5).all()
            print("📋 First 5 routes in database:")
            for i, route in enumerate(routes):
                print(f"  {i+1}. {route.name}")
                print(f"     From: {route.origin} → To: {route.destination}")
                print(f"     Distance: {route.total_distance_nm} nm")
                print()
        else:
            print("❌ Database 'routes' table is EMPTY!")
            
except Exception as e:
    print(f"❌ Database error: {e}")

# Option 2: Check RTZ Files Directly
print("\n2️⃣ Checking RTZ Files Directly...")
try:
    from backend.services.rtz_parser import discover_rtz_files
    
    print("🔍 Discovering RTZ files...")
    routes = discover_rtz_files(enhanced=False)
    print(f"✅ Found {len(routes)} routes from RTZ files")
    
    if routes:
        print("\n📋 First 5 routes from RTZ files:")
        for i, route in enumerate(routes[:5]):
            print(f"  {i+1}. {route.get('route_name', 'Unknown')}")
            print(f"     From: {route.get('origin', 'Unknown')} → To: {route.get('destination', 'Unknown')}")
            print(f"     Distance: {route.get('total_distance_nm', 0)} nm")
            print(f"     Source: {route.get('source_city', 'unknown')}")
            print()
            
except Exception as e:
    print(f"❌ RTZ parser error: {e}")

# Option 3: Check RTZ Loader Fixed
print("\n3️⃣ Checking Fixed RTZ Loader...")
try:
    from backend.rtz_loader_fixed import rtz_loader
    
    print("📂 Loading routes with fixed loader...")
    data = rtz_loader.get_dashboard_data()
    
    print(f"✅ Loaded {data['total_routes']} routes")
    print(f"📍 From {data['cities_with_routes']} cities")
    print(f"🏙️ Ports: {len(data['ports_list'])}")
    
    if data['routes']:
        print("\n📋 Sample routes:")
        for i, route in enumerate(data['routes'][:3]):
            print(f"  {i+1}. {route.get('route_name', 'Unknown')}")
            print(f"     From: {route.get('origin', 'Unknown')} → To: {route.get('destination', 'Unknown')}")
            print()
            
except Exception as e:
    print(f"❌ Fixed loader error: {e}")

print("\n" + "=" * 50)
print("🎯 DIAGNOSIS:")

# Determine the problem
if route_count == 0:
    print("❌ PROBLEM: Database 'routes' table is empty")
    print("💡 SOLUTION: Load RTZ data into database or use direct file loading")
    
    print("\n🚀 QUICK FIX: Modify maritime_dashboard() function")
    print("   Change from loading from database to loading from RTZ files")
    
    fix_code = '''
# IN maritime_routes.py, change the maritime_dashboard() function:

@maritime_bp.route('/dashboard')
def maritime_dashboard():
    """
    FIXED: Loads RTZ routes directly from files instead of empty database
    """
    try:
        # Load from RTZ files instead of database
        from backend.rtz_loader_fixed import rtz_loader
        data = rtz_loader.get_dashboard_data()
        
        routes = data['routes']
        ports_list = data['ports_list']
        unique_ports_count = data['unique_ports_count']
        
        # ... rest of your code with routes data ...
        
    except Exception as e:
        # Error handling...
'''

    print(fix_code)

elif route_count > 0:
    print(f"✅ Database has {route_count} routes")
    print("💡 The issue might be in the template or data format")
    
elif len(routes) > 0:
    print(f"✅ RTZ files have {len(routes)} routes")
    print("💡 Use direct file loading instead of database")

print("\n🔧 SIMPLE FIX: Create a new route that works")
print("   Visit: http://localhost:5000/maritime/dashboard-fixed")
print("   This should show the 34 routes we found earlier")