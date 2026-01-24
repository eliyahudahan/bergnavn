#!/usr/bin/env python3
"""
RTZ Routes Diagnosis Script
Identifies why RTZ routes are not showing in the dashboard.
Run from project root directory.
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
sys.path.insert(0, str(backend_dir))

print("🔍 RTZ Routes Diagnosis Tool")
print("=" * 60)

# Check project structure
print("\n📁 Project Structure Check:")
print(f"  Current directory: {current_dir}")
print(f"  Backend exists: {(current_dir / 'backend').exists()}")
print(f"  Assets exists: {(current_dir / 'backend' / 'assets').exists()}")

# Check RTZ files
rtz_base = current_dir / "backend" / "assets" / "routeinfo_routes"
print(f"\n📂 RTZ Files Directory: {rtz_base}")

if rtz_base.exists():
    cities = [d.name for d in rtz_base.iterdir() if d.is_dir()]
    print(f"  Found {len(cities)} cities:")
    
    for city in sorted(cities):
        city_path = rtz_base / city
        rtz_files = list(city_path.glob("**/*.rtz"))
        zip_files = list(city_path.glob("**/*.zip"))
        print(f"    • {city}: {len(rtz_files)} RTZ, {len(zip_files)} ZIP")
        
        if rtz_files:
            print(f"      Sample RTZ: {rtz_files[0].relative_to(rtz_base)}")
        if zip_files:
            print(f"      Sample ZIP: {zip_files[0].relative_to(rtz_base)}")
else:
    print(f"  ❌ RTZ directory not found!")

# Check Flask route
print("\n🚀 Checking Flask Routes:")
routes_file = current_dir / "backend" / "routes" / "maritime_routes.py"
if routes_file.exists():
    with open(routes_file, 'r') as f:
        content = f.read()
    
    if '@maritime_bp.route' in content:
        print("  ✅ maritime_routes.py exists with routes")
        
        # Check for dashboard route
        if 'dashboard' in content:
            print("  ✅ Dashboard route found")
        else:
            print("  ❌ Dashboard route NOT found in maritime_routes.py")
    else:
        print("  ❌ No routes defined in maritime_routes.py")
else:
    print(f"  ❌ maritime_routes.py not found at: {routes_file}")

# Check template
print("\n📄 Checking Template:")
template_file = current_dir / "backend" / "templates" / "maritime_split" / "dashboard_base.html"
if template_file.exists():
    print(f"  ✅ Template exists: {template_file.relative_to(current_dir)}")
else:
    print(f"  ❌ Template missing: {template_file}")

# Test RTZ parser
print("\n🧪 Testing RTZ Parser:")
try:
    from backend.services.rtz_parser import discover_rtz_files, get_processing_statistics
    
    print("  ✅ RTZ parser imported successfully")
    
    # Get statistics
    stats = get_processing_statistics()
    print(f"  📊 Statistics: {json.dumps(stats, indent=4, default=str)}")
    
    # Try to discover files
    print("  🔍 Discovering RTZ files...")
    routes = discover_rtz_files(enhanced=False)
    print(f"  ✅ Found {len(routes)} routes from RTZ files")
    
    if routes:
        print("  📋 Sample routes:")
        for i, route in enumerate(routes[:3]):
            print(f"    {i+1}. {route.get('route_name', 'Unknown')}")
            print(f"       From: {route.get('origin', 'Unknown')} → To: {route.get('destination', 'Unknown')}")
            print(f"       Distance: {route.get('total_distance_nm', 0)} nm")
    
except ImportError as e:
    print(f"  ❌ Cannot import RTZ parser: {e}")
except Exception as e:
    print(f"  ❌ Error testing RTZ parser: {e}")

print("\n" + "=" * 60)
print("💡 Next steps:")
print("1. If routes are found but not showing in dashboard, fix Flask route")
print("2. If no routes found, check RTZ file locations")
print("3. Run the fix script to apply corrections")