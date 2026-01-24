"""
RTZ Loader Utility - Loads processed RTZ routes from JSON files
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def load_processed_routes(base_dir: str = None) -> List[Dict]:
    """
    Load all processed RTZ routes from the JSON files.
    
    Args:
        base_dir: Base directory (optional, will be auto-detected)
    
    Returns:
        List of route dictionaries ready for the dashboard
    """
    try:
        if base_dir is None:
            # Try to auto-detect the base directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.join(current_dir, '..', '..')
            base_dir = os.path.abspath(base_dir)
        
        # Path to processed routes
        processed_dir = os.path.join(
            base_dir,
            'backend',
            'assets',
            'route_data',
            'processed'
        )
        
        routes_file = os.path.join(processed_dir, 'all_routes_data.json')
        
        if not os.path.exists(routes_file):
            logger.warning(f"Processed routes file not found: {routes_file}")
            return []
        
        with open(routes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        routes = data.get('routes', [])
        logger.info(f"Loaded {len(routes)} routes from processed file")
        
        # Enhance routes with additional properties for the dashboard
        enhanced_routes = []
        for i, route in enumerate(routes):
            if not route.get('is_valid', True):
                continue  # Skip invalid routes
            
            # Create enhanced route object
            enhanced_route = {
                'route_id': f"route_{i:03d}",
                'route_index': i,
                'route_name': route.get('route_name', f"Route {i+1}"),
                'clean_name': clean_route_name(route.get('route_name', '')),
                'origin': route.get('origin', 'Unknown'),
                'destination': route.get('destination', 'Unknown'),
                'total_distance_nm': float(route.get('total_distance_nm', 0)),
                'waypoint_count': int(route.get('waypoint_count', 0)),
                'source_city': route.get('source_city', 'Unknown'),
                'file_name': route.get('file_name', ''),
                'parsed_at': route.get('parsed_at', ''),
                'is_valid': route.get('is_valid', True),
                'bbox': route.get('bbox'),
                'visual_properties': {
                    'color': get_city_color(route.get('source_city', '')),
                    'weight': 3,
                    'opacity': 0.7,
                    'start_marker_color': '#28a745',
                    'end_marker_color': '#dc3545',
                    'highlight_color': '#FFFF00',
                    'highlight_weight': 6
                }
            }
            
            # Add waypoints if available (but limit for performance)
            waypoints = route.get('waypoints', [])
            if waypoints and len(waypoints) > 0:
                enhanced_route['has_waypoints'] = True
                enhanced_route['origin_coords'] = {
                    'lat': waypoints[0].get('lat', 0),
                    'lon': waypoints[0].get('lon', 0)
                }
                enhanced_route['destination_coords'] = {
                    'lat': waypoints[-1].get('lat', 0),
                    'lon': waypoints[-1].get('lon', 0)
                }
            
            enhanced_routes.append(enhanced_route)
        
        return enhanced_routes
        
    except Exception as e:
        logger.error(f"Error loading processed routes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def clean_route_name(name: str) -> str:
    """Clean route name for display."""
    if not name:
        return "Unnamed Route"
    
    # Remove common prefixes and suffixes
    cleaned = name
    # Remove NCA prefix
    if cleaned.startswith('NCA_'):
        cleaned = cleaned[4:]
    
    # Remove date suffixes
    date_patterns = ['_In_20250801', '_20250801', '_In_20250731', '_20250731']
    for pattern in date_patterns:
        cleaned = cleaned.replace(pattern, '')
    
    # Remove underscores and title case
    cleaned = cleaned.replace('_', ' ').strip()
    
    # Simple title case
    cleaned = ' '.join(word.capitalize() for word in cleaned.split())
    
    return cleaned if cleaned else "Norwegian Route"

def get_city_color(city_name: str) -> str:
    """Get consistent color for each city."""
    color_map = {
        'bergen': '#1e88e5',      # Blue
        'oslo': '#43a047',        # Green
        'stavanger': '#fb8c00',   # Orange
        'trondheim': '#e53935',   # Red
        'alesund': '#8e24aa',     # Purple
        'andalsnes': '#3949ab',   # Indigo
        'kristiansand': '#00897b', # Teal
        'drammen': '#f4511e',     # Deep Orange
        'sandefjord': '#5e35b1',  # Deep Purple
        'flekkefjord': '#039be5'  # Light Blue
    }
    
    if not city_name:
        return '#757575'  # Gray default
    
    city_lower = city_name.lower().strip()
    return color_map.get(city_lower, '#757575')

def get_ports_list(routes: List[Dict]) -> List[str]:
    """Extract unique ports/cities from routes."""
    ports = set()
    for route in routes:
        city = route.get('source_city')
        if city and isinstance(city, str) and city.lower() != 'unknown':
            # Format city name nicely
            city_formatted = city.title()
            ports.add(city_formatted)
    
    return sorted(list(ports))

def calculate_total_waypoints(routes: List[Dict]) -> int:
    """Calculate total waypoints across all routes."""
    total = 0
    for route in routes:
        total += route.get('waypoint_count', 0)
    return total

def calculate_total_distance(routes: List[Dict]) -> float:
    """Calculate total distance across all routes."""
    total = 0.0
    for route in routes:
        total += route.get('total_distance_nm', 0.0)
    return total

def get_route_by_id(routes: List[Dict], route_id: str) -> Optional[Dict]:
    """Find a route by its ID."""
    for route in routes:
        if route.get('route_id') == route_id:
            return route
    return None

def get_routes_by_city(routes: List[Dict], city: str) -> List[Dict]:
    """Filter routes by city."""
    if not city or city.lower() == 'all':
        return routes
    
    city_lower = city.lower()
    return [r for r in routes if r.get('source_city', '').lower() == city_lower]
