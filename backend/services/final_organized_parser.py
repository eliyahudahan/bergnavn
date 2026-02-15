"""
Final Organized JSON Route Parser
Reads pre-processed JSON route files from _final_organized directory
"""

import json
import os
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

def get_final_organized_routes() -> List[Dict]:
    """
    Read all route JSON files from _final_organized directory.
    Returns clean, unique routes without duplicates.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    final_org_path = os.path.join(project_root, "assets", "routeinfo_routes", "_final_organized")
    
    if not os.path.exists(final_org_path):
        logger.error(f"Final organized directory not found: {final_org_path}")
        return []
    
    all_routes = []
    
    # Process each city directory
    for city in os.listdir(final_org_path):
        city_path = os.path.join(final_org_path, city)
        if not os.path.isdir(city_path):
            continue
        
        logger.info(f"Processing {city}...")
        
        # Read all JSON files in this city directory
        for filename in os.listdir(city_path):
            if filename.endswith('.json'):
                filepath = os.path.join(city_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        route_data = json.load(f)
                    
                    # Extract and clean route information
                    route = extract_route_from_json(route_data, city, filename)
                    if route:
                        all_routes.append(route)
                        logger.debug(f"  Added route: {route.get('route_name', filename)}")
                        
                except Exception as e:
                    logger.error(f"Error reading {filepath}: {e}")
    
    logger.info(f"Total routes found: {len(all_routes)}")
    
    # Remove any potential duplicates
    unique_routes = remove_json_duplicates(all_routes)
    logger.info(f"Unique routes after deduplication: {len(unique_routes)}")
    
    return unique_routes

def extract_route_from_json(json_data: Dict, city: str, filename: str) -> Dict:
    """Extract route information from JSON structure."""
    try:
        # Extract basic route info
        route_name = json_data.get('route_name', '')
        if not route_name and 'routeInfo' in json_data:
            route_name = json_data['routeInfo'].get('routeName', '')
        
        # Extract waypoints
        waypoints = []
        if 'waypoints' in json_data:
            for wp in json_data['waypoints']:
                waypoint = {
                    'name': wp.get('name', ''),
                    'lat': wp.get('lat', 0),
                    'lon': wp.get('lon', 0),
                    'radius': wp.get('turnRadius', 0.1)
                }
                waypoints.append(waypoint)
        
        if not waypoints:
            logger.warning(f"No waypoints found in {filename}")
            return None
        
        # Calculate total distance
        total_distance = calculate_total_distance(waypoints)
        
        # Extract origin and destination from filename or route name
        origin, destination = extract_origin_destination(filename, route_name, waypoints)
        
        # Create clean route object
        route = {
            'route_id': filename.replace('.json', ''),
            'route_name': route_name,
            'clean_name': create_clean_route_name(route_name, origin, destination),
            'waypoints': waypoints,
            'waypoint_count': len(waypoints),
            'total_distance_nm': total_distance,
            'origin': origin,
            'destination': destination,
            'source_city': city.title(),
            'data_source': 'final_organized_json',
            'filename': filename,
            'parse_timestamp': datetime.now().isoformat()
        }
        
        # Add visual properties
        route['visual_properties'] = {
            'color': get_city_color(city),
            'weight': 3,
            'opacity': 0.7,
            'start_marker_color': '#28a745',
            'end_marker_color': '#dc3545'
        }
        
        return route
        
    except Exception as e:
        logger.error(f"Error extracting route from {filename}: {e}")
        return None

def calculate_total_distance(waypoints: List[Dict]) -> float:
    """Calculate total route distance in nautical miles."""
    import math
    
    def haversine_nm(lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return 3440.065 * c  # Earth radius in nautical miles
    
    total = 0.0
    for i in range(len(waypoints) - 1):
        wp1 = waypoints[i]
        wp2 = waypoints[i + 1]
        total += haversine_nm(wp1['lat'], wp1['lon'], wp2['lat'], wp2['lon'])
    
    return round(total, 2)

def extract_origin_destination(filename: str, route_name: str, waypoints: List[Dict]) -> tuple:
    """Extract origin and destination from filename or waypoints."""
    # Try to extract from filename first
    name_parts = filename.replace('.json', '').split('_')
    if len(name_parts) > 2:
        # Format is: hash_Origin_to_Destination.json
        # Find the 'to' part
        for i, part in enumerate(name_parts):
            if part.lower() == 'to':
                if i > 1 and i < len(name_parts) - 1:
                    origin = ' '.join(name_parts[1:i]).replace('_', ' ')
                    destination = ' '.join(name_parts[i+1:]).replace('_', ' ')
                    
                    # Clean up common abbreviations
                    origin = clean_port_name(origin)
                    destination = clean_port_name(destination)
                    return origin, destination
    
    # Try from route name
    if route_name and '_' in route_name:
        parts = route_name.split('_')
        if len(parts) >= 3:
            return clean_port_name(parts[1]), clean_port_name(parts[2])
    
    # Fallback to waypoint names
    if waypoints:
        origin = waypoints[0].get('name', 'Unknown')
        destination = waypoints[-1].get('name', 'Unknown')
        return clean_port_name(origin), clean_port_name(destination)
    
    return 'Unknown', 'Unknown'

def clean_port_name(name: str) -> str:
    """Clean port names from abbreviations."""
    name = name.strip()
    
    # Common abbreviations
    abbreviations = {
        'Alesund': 'Ålesund',
        'Andalsnes': 'Åndalsnes',
        'Oslowest': 'Oslo West',
        'Osloeast': 'Oslo East',
        'Kristiansande': 'Kristiansand East',
        'Kristiansandw': 'Kristiansand West',
        '7_to_5M': 'Route 7 to 5M',
        '9M_to': 'Route 9M to',
        'In': 'Inbound',
        'Out': 'Outbound'
    }
    
    for abbr, full in abbreviations.items():
        if abbr in name:
            name = name.replace(abbr, full)
    
    # Capitalize properly
    return ' '.join(word.capitalize() for word in name.split())

def create_clean_route_name(route_name: str, origin: str, destination: str) -> str:
    """Create a clean, readable route name."""
    if route_name and '_' in route_name:
        # Clean NCA style names
        clean = route_name.replace('NCA_', '').replace('_', ' ').title()
        return clean
    
    # Create from origin/destination
    if origin != 'Unknown' and destination != 'Unknown':
        return f"{origin} to {destination}"
    
    return route_name if route_name else "Norwegian Coastal Route"

def get_city_color(city: str) -> str:
    """Assign consistent colors to cities."""
    colors = {
        'bergen': '#FF6B6B',
        'oslo': '#4ECDC4',
        'stavanger': '#45B7D1',
        'trondheim': '#96CEB4',
        'alesund': '#FFEAA7',
        'andalsnes': '#DDA0DD',
        'kristiansand': '#98D8C8',
        'drammen': '#F7DC6F',
        'sandefjord': '#BB8FCE',
        'flekkefjord': '#85C1E9'
    }
    return colors.get(city.lower(), '#3498db')

def remove_json_duplicates(routes: List[Dict]) -> List[Dict]:
    """Remove duplicate routes based on waypoint coordinates."""
    seen = set()
    unique_routes = []
    
    for route in routes:
        # Create unique key from waypoints
        waypoint_key = ''
        for wp in route.get('waypoints', []):
            waypoint_key += f"{wp.get('lat', 0):.6f},{wp.get('lon', 0):.6f};"
        
        route_key = f"{route.get('origin')}_{route.get('destination')}_{waypoint_key}"
        
        if route_key not in seen:
            seen.add(route_key)
            unique_routes.append(route)
    
    return unique_routes

def get_route_statistics(routes: List[Dict]) -> Dict:
    """Get statistics about loaded routes."""
    if not routes:
        return {}
    
    cities = set()
    total_distance = 0
    total_waypoints = 0
    
    for route in routes:
        cities.add(route.get('source_city', ''))
        total_distance += route.get('total_distance_nm', 0)
        total_waypoints += route.get('waypoint_count', 0)
    
    return {
        'total_routes': len(routes),
        'total_cities': len(cities),
        'cities': sorted(list(cities)),
        'total_distance_nm': round(total_distance, 1),
        'total_waypoints': total_waypoints,
        'avg_distance': round(total_distance / len(routes), 1) if routes else 0,
        'avg_waypoints': round(total_waypoints / len(routes), 1) if routes else 0
    }

# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Loading routes from _final_organized...")
    routes = get_final_organized_routes()
    
    if routes:
        stats = get_route_statistics(routes)
        print(f"\n✅ Loaded {stats['total_routes']} routes")
        print(f"📊 Statistics:")
        print(f"   Cities: {', '.join(stats['cities'])}")
        print(f"   Total distance: {stats['total_distance_nm']} NM")
        print(f"   Total waypoints: {stats['total_waypoints']}")
        print(f"   Average distance: {stats['avg_distance']} NM")
        
        # Save for dashboard
        output_path = os.path.join(os.path.dirname(__file__), "static", "data", "final_routes.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(routes, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved to {output_path}")
    else:
        print("❌ No routes found")