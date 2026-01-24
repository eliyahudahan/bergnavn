#!/usr/bin/env python3
"""
Test script for RTZ Dashboard Fix
"""

import sys
from pathlib import Path

# Add backend
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
sys.path.insert(0, str(backend_dir))

print("🔍 Testing RTZ Dashboard Fix")
print("=" * 50)

try:
    # Test 1: Import fixed loader
    print("\n1️⃣ Testing fixed loader...")
    from rtz_loader_fixed import rtz_loader
    
    print("✅ Fixed loader imported")
    
    # Test 2: Load routes
    print("\n2️⃣ Loading routes...")
    data = rtz_loader.get_dashboard_data()
    
    print(f"✅ Found {data['total_routes']} routes")
    print(f"📍 Ports: {len(data['ports_list'])}")
    print(f"🏙️ Cities with routes: {data['cities_with_routes']}")
    
    # Show ports
    print("\n📋 Norwegian ports:")
    for port in data['ports_list']:
        print(f"  • {port}")
    
    # Show sample routes
    if data['routes']:
        print(f"\n📊 Sample routes (first 3):")
        for i, route in enumerate(data['routes'][:3]):
            print(f"{i+1}. {route.get('route_name', 'Unknown')}")
            print(f"   From: {route.get('origin', 'Unknown')}")
            print(f"   To: {route.get('destination', 'Unknown')}")
            print(f"   Distance: {route.get('total_distance_nm', 0)} nm")
            print(f"   Waypoints: {route.get('waypoint_count', 0)}")
            print()
    
    # Test 3: Check file structure
    print("\n3️⃣ Checking file structure...")
    base_path = Path("backend/assets/routeinfo_routes")
    
    if base_path.exists():
        cities_found = []
        for city_dir in base_path.iterdir():
            if city_dir.is_dir():
                rtz_count = len(list(city_dir.glob("**/*.rtz")))
                if rtz_count > 0:
                    cities_found.append(f"{city_dir.name} ({rtz_count} files)")
        
        print(f"✅ Found RTZ files in {len(cities_found)} cities:")
        for city_info in cities_found:
            print(f"  • {city_info}")
    else:
        print(f"❌ RTZ directory not found: {base_path}")
    
    print("\n🎉 All tests passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
