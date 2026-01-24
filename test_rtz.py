#!/usr/bin/env python3
"""
Quick test for RTZ routes
"""

import sys
from pathlib import Path

# Add backend
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from backend.services.rtz_parser import discover_rtz_files
    
    print("🔍 Testing RTZ parser...")
    routes = discover_rtz_files(enhanced=False)
    
    print(f"✅ Found {len(routes)} routes")
    
    if routes:
        print("
📋 First 5 routes:")
        for i, route in enumerate(routes[:5]):
            print(f"{i+1}. {route.get('route_name', 'Unknown')}")
            print(f"   From: {route.get('origin', 'Unknown')}")
            print(f"   To: {route.get('destination', 'Unknown')}")
            print(f"   Distance: {route.get('total_distance_nm', 0)} nm")
            print(f"   Waypoints: {route.get('waypoint_count', 0)}")
            print()
    
    # Check file locations
    print("
📁 Checking RTZ files...")
    from backend.services.rtz_parser import find_rtz_files
    files = find_rtz_files()
    
    for city, file_list in files.items():
        print(f"  {city.title()}: {len(file_list)} files")
        for f in file_list[:2]:
            print(f"    • {Path(f).name}")
        if len(file_list) > 2:
            print(f"    ... and {len(file_list)-2} more")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
