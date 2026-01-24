#!/usr/bin/env python3
"""
Test script to verify RTZ routes integration
"""

import sys
import os

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from backend.utils.rtz_loader import load_processed_routes
    
    print("=" * 60)
    print("RTZ INTEGRATION TEST")
    print("=" * 60)
    
    routes = load_processed_routes()
    
    if not routes:
        print("❌ No routes loaded!")
        sys.exit(1)
    
    print(f"✅ Loaded {len(routes)} routes")
    
    # Show some stats
    ports = set()
    total_waypoints = 0
    total_distance = 0.0
    
    for route in routes:
        if route.get('source_city'):
            ports.add(route['source_city'])
        total_waypoints += route.get('waypoint_count', 0)
        total_distance += route.get('total_distance_nm', 0.0)
    
    print(f"📊 Statistics:")
    print(f"   - Ports: {len(ports)}")
    print(f"   - Total waypoints: {total_waypoints}")
    print(f"   - Total distance: {total_distance:.1f} NM")
    
    # Show first 3 routes
    print(f"\n📋 Sample routes (first 3):")
    for i, route in enumerate(routes[:3]):
        print(f"   {i+1}. {route.get('clean_name', 'Unnamed')}")
        print(f"      From: {route.get('origin', 'Unknown')} → To: {route.get('destination', 'Unknown')}")
        print(f"      Distance: {route.get('total_distance_nm', 0):.1f} NM, Waypoints: {route.get('waypoint_count', 0)}")
        print(f"      Port: {route.get('source_city', 'Unknown')}")
    
    print("\n🎉 Integration test passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
