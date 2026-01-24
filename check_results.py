# תיקיה: bergnavn/check_results.py

#!/usr/bin/env python3
"""
Check the generated route data
"""

import json
import os

def check_geojson():
    """Check the generated GeoJSON file."""
    geojson_path = "backend/assets/route_data/processed/coastal_routes.geojson"
    
    if not os.path.exists(geojson_path):
        print("❌ GeoJSON file not found")
        return
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("GEOJSON FILE CHECK")
    print("=" * 60)
    
    # Check routes
    routes = data.get('routes', {}).get('features', [])
    waypoints = data.get('waypoints', {}).get('features', [])
    metadata = data.get('metadata', {})
    
    print(f"Routes found: {len(routes)}")
    print(f"Waypoints found: {len(waypoints)}")
    
    if routes:
        print("\nSample route:")
        route = routes[0]
        props = route['properties']
        geom = route['geometry']
        
        print(f"  Name: {props['name']}")
        print(f"  City: {props['city']}")
        print(f"  From: {props['origin']} → To: {props['destination']}")
        print(f"  Distance: {props['distance_nm']} nm")
        print(f"  Waypoints: {props['waypoint_count']}")
        print(f"  Coordinates: {len(geom['coordinates'])} points")
        
        # Show first and last coordinates
        if geom['coordinates']:
            print(f"  Start: {geom['coordinates'][0]}")
            print(f"  End: {geom['coordinates'][-1]}")
    
    if waypoints:
        print(f"\nSample waypoints (first 5):")
        for i, wp in enumerate(waypoints[:5]):
            props = wp['properties']
            geom = wp['geometry']
            print(f"  {i+1}. {props['name']} ({props['route_name']})")
            print(f"     Start: {'✓' if props['is_start'] else '✗'} "
                  f"End: {'✓' if props['is_end'] else '✗'}")
            print(f"     Coords: {geom['coordinates']}")
    
    print(f"\nMetadata:")
    print(f"  Total routes: {metadata.get('total_routes', 'N/A')}")
    print(f"  Total waypoints: {metadata.get('total_waypoints', 'N/A')}")
    print(f"  Cities: {', '.join(metadata.get('cities', []))}")

def check_routes_data():
    """Check the raw routes data."""
    routes_path = "backend/assets/route_data/processed/all_routes_data.json"
    
    if not os.path.exists(routes_path):
        print("❌ Routes data file not found")
        return
    
    with open(routes_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    routes = data.get('routes', [])
    
    print(f"\n{'='*60}")
    print("ROUTES DATA CHECK")
    print(f"{'='*60}")
    print(f"Total routes: {len(routes)}")
    
    # Group by city
    cities = {}
    for route in routes:
        city = route.get('city', 'Unknown')
        if city not in cities:
            cities[city] = []
        cities[city].append(route)
    
    print(f"\nRoutes by city:")
    for city, city_routes in cities.items():
        waypoints = sum(r['waypoint_count'] for r in city_routes)
        distance = sum(r['total_distance_nm'] for r in city_routes)
        print(f"  {city}: {len(city_routes)} routes, "
              f"{waypoints} waypoints, {distance:.1f} nm")
        
        # Show longest route in city
        longest = max(city_routes, key=lambda x: x['total_distance_nm'])
        print(f"    Longest: {longest['route_name']} "
              f"({longest['total_distance_nm']} nm)")

def main():
    check_geojson()
    check_routes_data()

if __name__ == "__main__":
    main()