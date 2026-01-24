"""
FIXED RTZ LOADER - Correctly loads all 37+ RTZ files from Norwegian ports
Handles all 10 cities: bergen, oslo, stavanger, trondheim, alesund, 
andalsnes, kristiansand, drammen, sandefjord, flekkefjord

IMPORTANT FIX: Now includes actual waypoint coordinates in the returned data
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import math
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# All Norwegian ports
NORWEGIAN_PORTS = {
    'bergen': 'Bergen',
    'oslo': 'Oslo',
    'stavanger': 'Stavanger',
    'trondheim': 'Trondheim',
    'alesund': 'Ålesund',
    'andalsnes': 'Åndalsnes',
    'kristiansand': 'Kristiansand',
    'drammen': 'Drammen',
    'sandefjord': 'Sandefjord',
    'flekkefjord': 'Flekkefjord'
}

class FixedRTZLoader:
    """
    Fixed RTZ loader that correctly parses all Norwegian Coastal Administration files
    Now includes complete waypoint data for accurate map display
    """
    
    def __init__(self):
        self.base_path = Path("backend/assets/routeinfo_routes")
        self.city_colors = {
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
    
    def clean_coordinate(self, value):
        """Clean coordinate string from any non-numeric characters"""
        if isinstance(value, str):
            # Remove everything except digits, dots, and minus
            cleaned = re.sub(r'[^\d\.\-]', '', value)
            try:
                return float(cleaned) if cleaned else 0.0
            except:
                return 0.0
        return float(value) if value else 0.0
    
    def clean_port_name(self, name: str) -> str:
        """Clean port name from RTZ file"""
        if not name:
            return 'Coastal'
        
        # Remove technical parts
        clean = name.split(' - report')[0].split(' lt')[0].split(' bn')[0]
        clean = clean.split(' buoy')[0].split(' 7.5 m')[0].split(' 9m')[0]
        clean = clean.split(' 13 m')[0].split(' pilot')[0]
        clean = clean.split(' VTS')[0].split(' traffic')[0]
        clean = clean.split(' (')[0].split(' [')[0].strip()
        
        # Check if it's a known port
        for port_key, port_name in NORWEGIAN_PORTS.items():
            if port_key in name.lower() or port_name.lower() in name.lower():
                return port_name
        
        # Capitalize first letter
        if clean:
            return clean[0].upper() + clean[1:]
        
        return 'Coastal'
    
    def parse_rtz_file(self, file_path: Path, city: str) -> Optional[Dict]:
        """Parse single RTZ file - returns complete route data with waypoints"""
        try:
            logger.info(f"📄 Parsing: {file_path.name}")
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Register namespace
            ns = {'rtz': 'https://cirm.org/rtz-xml-schemas'}
            ET.register_namespace('rtz', 'https://cirm.org/rtz-xml-schemas')
            
            # Get route name
            route_name = "Unknown_Route"
            route_info = root.find('.//rtz:routeInfo', ns)
            if route_info is not None and 'routeName' in route_info.attrib:
                route_name = route_info.get('routeName')
            
            # Extract waypoints with detailed information
            waypoints = []
            waypoint_elements = root.findall('.//rtz:waypoint', ns)
            
            for wp_elem in waypoint_elements:
                try:
                    pos_elem = wp_elem.find('rtz:position', ns)
                    if pos_elem is not None:
                        lat = self.clean_coordinate(pos_elem.get('lat', '0'))
                        lon = self.clean_coordinate(pos_elem.get('lon', '0'))
                        
                        # Skip invalid coordinates
                        if lat == 0.0 and lon == 0.0:
                            continue
                            
                        waypoint = {
                            'name': wp_elem.get('name', f'WP{len(waypoints)+1}'),
                            'lat': lat,
                            'lon': lon,
                            'radius': float(wp_elem.get('radius', 0.3)),
                            'element_id': wp_elem.get('id', ''),
                            'geometry': {
                                'type': 'Point',
                                'coordinates': [lon, lat]
                            }
                        }
                        waypoints.append(waypoint)
                except Exception as e:
                    logger.debug(f"Error parsing waypoint: {e}")
                    continue
            
            if len(waypoints) < 2:
                logger.warning(f"Not enough waypoints in {file_path.name}")
                return None
            
            # Calculate distance
            total_distance = self.calculate_route_distance(waypoints)
            
            # Extract origin and destination
            origin, destination = self.extract_ports_from_route(route_name, waypoints, city)
            
            # Create complete geometry for the route
            geometry_coordinates = [[wp['lon'], wp['lat']] for wp in waypoints]
            
            # Create complete route data INCLUDING waypoints
            route_data = {
                'route_name': route_name,
                'clean_name': self.clean_route_name(route_name),
                'origin': origin,
                'destination': destination,
                'total_distance_nm': round(total_distance, 2),
                'waypoint_count': len(waypoints),
                'waypoints': waypoints,  # <<< INCLUDING ACTUAL WAYPOINT DATA
                'geometry': {
                    'type': 'LineString',
                    'coordinates': geometry_coordinates
                },
                'path': [[wp['lat'], wp['lon']] for wp in waypoints],  # Alternative format for map
                'source_city': city,
                'source_city_name': NORWEGIAN_PORTS.get(city, city.title()),
                'source_file': file_path.name,
                'description': f"Official NCA route: {origin} → {destination}",
                'verified': True,
                'data_source': 'routeinfo.no (Norwegian Coastal Administration)',
                'timestamp': datetime.now().isoformat(),
                'visual_properties': {
                    'color': self.city_colors.get(city, '#007bff'),
                    'weight': 3,
                    'opacity': 0.8,
                    'start_marker_color': '#28a745',
                    'end_marker_color': '#dc3545'
                },
                'metadata': {
                    'has_waypoints': len(waypoints) > 0,
                    'waypoint_details': True,
                    'extracted_at': datetime.now().isoformat()
                }
            }
            
            logger.info(f"✅ {origin} → {destination} ({total_distance:.1f} nm, {len(waypoints)} points)")
            return route_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing {file_path}: {e}")
            return None
    
    def calculate_route_distance(self, waypoints: List[Dict]) -> float:
        """Calculate total distance in nautical miles"""
        total = 0.0
        
        for i in range(len(waypoints) - 1):
            lat1, lon1 = waypoints[i]['lat'], waypoints[i]['lon']
            lat2, lon2 = waypoints[i+1]['lat'], waypoints[i+1]['lon']
            total += self.haversine_nm(lat1, lon1, lat2, lon2)
        
        return total
    
    def haversine_nm(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula for nautical miles"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return 3440.065 * c
    
    def extract_ports_from_route(self, route_name: str, waypoints: List[Dict], city: str) -> Tuple[str, str]:
        """Extract origin and destination from route"""
        
        # Try from route name first
        if 'NCA_' in route_name:
            parts = route_name.split('_')
            if len(parts) >= 4:
                # Handle special cases
                origin_part = parts[1]
                dest_part = parts[2]
                
                # Clean up number codes
                origin = self.decode_port_code(origin_part, city)
                destination = self.decode_port_code(dest_part, city)
                
                if origin != 'Unknown' and destination != 'Unknown':
                    return origin, destination
        
        # Try from waypoints names
        if waypoints:
            first_wp = waypoints[0]
            last_wp = waypoints[-1]
            
            first_name = self.clean_port_name(first_wp.get('name', ''))
            last_name = self.clean_port_name(last_wp.get('name', ''))
            
            if first_name != 'Coastal' and last_name != 'Coastal':
                return first_name, last_name
        
        # Default to city names
        origin_name = NORWEGIAN_PORTS.get(city, 'Coastal')
        return origin_name, 'Coastal'
    
    def decode_port_code(self, code: str, default_city: str) -> str:
        """Decode port codes from RTZ filenames"""
        # Map common codes
        code_map = {
            '7': 'Ålesund',
            '5m': 'Stad',
            '9m': 'Deep',
            'Bergen': 'Bergen',
            'Oslo': 'Oslo',
            'Stavanger': 'Stavanger',
            'Trondheim': 'Trondheim',
            'Alesund': 'Ålesund',
            'Andalsnes': 'Åndalsnes',
            'Kristiansand': 'Kristiansand',
            'Drammen': 'Drammen',
            'Sandefj': 'Sandefjord',
            'Sandefjord': 'Sandefjord',
            'Flekkefjord': 'Flekkefjord',
            'Stad': 'Stad',
            'Fedje': 'Fedje',
            'Halten': 'Halten',
            'Marstein': 'Marstein',
            'Skudefjorden': 'Skudefjorden',
            'Feistein': 'Feistein',
            'Oksoy': 'Oksøy',
            'Breisundet': 'Breisundet',
            'Grande': 'Grande',
            'Rorvik': 'Rørvik',
            'Grip': 'Grip',
            'Bonden': 'Bonden',
            'Sydostgr': 'South East'
        }
        
        # Check direct mapping
        if code in code_map:
            return code_map[code]
        
        # Check if contains port name
        for port_key, port_name in NORWEGIAN_PORTS.items():
            if port_key in code.lower():
                return port_name
        
        # Return default city
        return NORWEGIAN_PORTS.get(default_city, 'Coastal')
    
    def clean_route_name(self, route_name: str) -> str:
        """Create clean display name"""
        clean = route_name.replace('NCA_', '').replace('_2025', '').replace('_2024', '').replace('_', ' ')
        
        # Replace codes with readable names
        replacements = {
            '7 5m': '7.5m Draft',
            '9m': '9m Draft',
            'AlesundN': 'Ålesund North',
            'AlesundS': 'Ålesund South',
            'In': 'Inbound',
            'Out': 'Outbound',
            'West': 'West',
            'East': 'East',
            'W': 'West',
            'E': 'East',
            'N': 'North',
            'S': 'South'
        }
        
        for old, new in replacements.items():
            clean = clean.replace(old, new)
        
        return clean.title()
    
    def load_all_routes(self) -> List[Dict]:
        """Load ALL routes from all cities - returns complete route data including waypoints"""
        all_routes = []
        
        logger.info(f"🚀 Loading routes from {len(NORWEGIAN_PORTS)} Norwegian ports...")
        
        for city_key in NORWEGIAN_PORTS.keys():
            city_path = self.base_path / city_key / "raw"
            
            if not city_path.exists():
                # Try alternative paths
                city_path = self.base_path / city_key
                if not city_path.exists():
                    logger.warning(f"City directory not found: {city_key}")
                    continue
            
            logger.info(f"📂 Processing {city_key.title()}...")
            
            # Find all RTZ files
            rtz_files = list(city_path.glob("*.rtz"))
            
            if not rtz_files:
                logger.warning(f"No RTZ files found in {city_key}")
                continue
            
            logger.info(f"  Found {len(rtz_files)} RTZ files")
            
            # Parse each file
            city_routes = []
            for rtz_file in rtz_files:
                route = self.parse_rtz_file(rtz_file, city_key)
                if route:
                    city_routes.append(route)
            
            all_routes.extend(city_routes)
            logger.info(f"  ✅ Loaded {len(city_routes)} routes from {city_key.title()}")
        
        logger.info(f"🎉 Total routes loaded: {len(all_routes)}")
        
        # Generate summary
        if all_routes:
            routes_by_city = {}
            total_waypoints = 0
            
            for route in all_routes:
                city = route['source_city']
                routes_by_city[city] = routes_by_city.get(city, 0) + 1
                total_waypoints += route['waypoint_count']
            
            logger.info("📊 Routes by city:")
            for city, count in sorted(routes_by_city.items()):
                logger.info(f"  • {city.title()}: {count} routes")
            
            logger.info(f"📍 Total waypoints: {total_waypoints}")
        
        return all_routes
    
    def get_dashboard_data(self) -> Dict:
        """Get all data needed for dashboard - includes complete waypoint data"""
        routes = self.load_all_routes()
        
        # Add route IDs for frontend reference
        for i, route in enumerate(routes):
            route['route_id'] = f"rtz_{i+1:03d}"
        
        # Get unique ports
        unique_ports = set()
        for route in routes:
            if route['origin'] != 'Coastal':
                unique_ports.add(route['origin'])
            if route['destination'] != 'Coastal':
                unique_ports.add(route['destination'])
        
        # Add city names to ports list
        ports_list = list(NORWEGIAN_PORTS.values())
        
        # Calculate total waypoints
        total_waypoints = sum(route['waypoint_count'] for route in routes)
        
        return {
            'routes': routes,  # <<< COMPLETE ROUTE DATA INCLUDING WAYPOINTS
            'ports_list': ports_list,
            'unique_ports': sorted(list(unique_ports)),
            'unique_ports_count': len(unique_ports),
            'total_routes': len(routes),
            'total_waypoints': total_waypoints,
            'cities_with_routes': len(set(r['source_city'] for r in routes)),
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'data_format': 'complete',
                'includes_waypoints': True,
                'includes_coordinates': True,
                'route_count': len(routes),
                'waypoint_count': total_waypoints
            }
        }
    
    def get_route_by_id(self, route_id: str) -> Optional[Dict]:
        """Get specific route by ID"""
        routes = self.load_all_routes()
        for route in routes:
            if route.get('route_id') == route_id:
                return route
        return None

# Create singleton instance
rtz_loader = FixedRTZLoader()