"""
RTZ Parser for Norwegian Coastal Administration Route Files
FIXED: Handles ZIP-compressed RTZ files and correct XML namespaces
ENHANCED: Extracts ALL 47+ routes from ZIP files, not just the first one
REAL-TIME: Ensures all routes are discovered and displayed in dashboard
VISUAL ENHANCEMENT: Added route colors and visual properties for better map differentiation
"""

import xml.etree.ElementTree as ET
import os
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import math
import zipfile
import tempfile
import glob
import random
import colorsys

# Configure logging
logger = logging.getLogger(__name__)

def get_project_root() -> str:
    """
    Get the absolute path to project root directory.
    Works regardless of current working directory.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir.endswith('backend/services'):
        return os.path.dirname(os.path.dirname(current_dir))
    elif current_dir.endswith('backend'):
        return os.path.dirname(current_dir)
    else:
        # Assume we're in project root
        return current_dir

def generate_route_colors() -> Dict[str, str]:
    """
    Generate distinct colors for routes visualization.
    Returns color palette and ensures each route has unique styling.
    """
    # Base colors for different cities/regions - visually distinct
    city_colors = {
        'bergen': '#FF6B6B',      # Vibrant Red
        'oslo': '#4ECDC4',        # Teal
        'stavanger': '#45B7D1',   # Sky Blue
        'trondheim': '#96CEB4',   # Mint Green
        'alesund': '#FFEAA7',     # Light Yellow
        'andalsnes': '#DDA0DD',   # Lavender
        'kristiansand': '#98D8C8',# Seafoam Green
        'drammen': '#F7DC6F',     # Gold
        'sandefjord': '#BB8FCE',  # Purple
        'flekkefjord': '#85C1E9', # Light Blue
    }
    
    return city_colors

def generate_unique_color(route_name: str, route_index: int) -> str:
    """
    Generate a unique color based on route name and index.
    Ensures consistent coloring across sessions.
    """
    # Use hash of route name for consistent coloring
    name_hash = hash(route_name) % 360
    route_hash = (hash(route_name) + route_index * 137) % 360
    
    # Generate HSL color with good saturation and lightness
    hue = (name_hash + route_hash) % 360
    saturation = 70 + (route_index % 20)  # 70-90% saturation
    lightness = 45 + (route_index % 15)   # 45-60% lightness
    
    # Convert HSL to RGB hex
    rgb = colorsys.hls_to_rgb(hue/360, lightness/100, saturation/100)
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgb[0] * 255),
        int(rgb[1] * 255),
        int(rgb[2] * 255)
    )

def extract_all_routes_from_zip(zip_path: str, city: str) -> List[Dict]:
    """
    Extract and parse ALL RTZ files from a ZIP archive.
    ENHANCED: Processes every RTZ file in the ZIP, not just the first one.
    
    Args:
        zip_path: Path to ZIP file
        city: City name for logging and metadata
        
    Returns:
        List of all route dictionaries from the ZIP
    """
    all_routes = []
    
    try:
        if not os.path.exists(zip_path):
            logger.error(f"ZIP file not found: {zip_path}")
            return []
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get ALL RTZ files in the ZIP
            rtz_files = [f for f in zip_ref.namelist() if f.endswith('.rtz')]
            
            if not rtz_files:
                logger.warning(f"No RTZ files found in {zip_path}")
                return []
            
            logger.info(f"📦 Found {len(rtz_files)} RTZ files in {city} ZIP archive")
            
            # Create temporary directory for extraction
            temp_dir = tempfile.mkdtemp()
            
            for rtz_filename in rtz_files:
                try:
                    # Extract file
                    extracted_path = os.path.join(temp_dir, rtz_filename)
                    zip_ref.extract(rtz_filename, temp_dir)
                    
                    # Parse the RTZ file
                    routes = parse_rtz_file(extracted_path)
                    if routes:
                        # Add city metadata to each route
                        for route in routes:
                            route['source_city'] = city
                            route['original_zip'] = os.path.basename(zip_path)
                            route['rtz_filename'] = rtz_filename
                        all_routes.extend(routes)
                        logger.info(f"  ✅ Parsed: {rtz_filename} ({len(routes)} route(s))")
                    
                    # Clean up extracted file
                    os.remove(extracted_path)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {rtz_filename}: {e}")
                    continue
            
            # Clean up temp directory
            os.rmdir(temp_dir)
            
    except zipfile.BadZipFile:
        logger.error(f"Invalid ZIP file: {zip_path}")
        return []
    except Exception as e:
        logger.error(f"Error extracting ZIP {zip_path}: {e}")
        return []
    
    logger.info(f"🎉 Extracted {len(all_routes)} total routes from {city} ZIP")
    return all_routes

def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points in nautical miles.
    Uses Haversine formula for accurate maritime distance calculation.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Earth radius in nautical miles (1 nm = 1.852 km)
    radius_nm = 3440.065  # Earth radius in nautical miles
    
    return radius_nm * c

def parse_rtz_file(file_path: str) -> List[Dict]:
    """
    Parse RTZ route file and extract waypoints with enhanced metadata.
    FIXED: Handles multiple XML namespaces used by Norwegian Coastal Administration.
    Returns structured route data with distances and waypoint information.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return []
        
        # Check if file is a ZIP archive
        actual_file_path = file_path
        with open(file_path, 'rb') as f:
            file_header = f.read(4)
            is_zip = file_header == b'PK\x03\x04'
        
        # If it's a ZIP file, extract ALL RTZ content first
        if is_zip:
            logger.info(f"📦 Detected ZIP archive, extracting ALL RTZ content: {file_path}")
            # For ZIP files, we should use extract_all_routes_from_zip instead
            logger.warning("ZIP file passed to parse_rtz_file directly. Use extract_all_routes_from_zip for better handling.")
            return []
        else:
            logger.info(f"📄 Processing direct RTZ XML file: {file_path}")
        
        # Now parse the XML file
        tree = ET.parse(actual_file_path)
        root = tree.getroot()
        
        # FIXED: Extract route information with namespace handling
        route_name = "Unknown_Route"
        
        # Try to get routeName from different possible locations
        if 'routeName' in root.attrib:
            route_name = root.get('routeName')
        else:
            # Look for routeInfo element
            for namespace in ['', '{https://cirm.org/rtz-xml-schemas}']:
                route_info_elem = root.find(f'{namespace}routeInfo')
                if route_info_elem is not None and 'routeName' in route_info_elem.attrib:
                    route_name = route_info_elem.get('routeName')
                    break
        
        logger.debug(f"Parsing RTZ route: {route_name}")
        
        # Extract waypoints with FIXED namespace handling
        waypoints = []
        
        # Try different namespace approaches for maximum compatibility
        # Based on the actual XML structure you provided
        waypoint_elements = []
        
        # Method 1: Direct search without namespace (most common)
        waypoint_elements = root.findall('.//waypoint')
        
        # Method 2: With the actual namespace from your file
        if not waypoint_elements:
            ns = {'rtz': 'https://cirm.org/rtz-xml-schemas'}
            waypoint_elements = root.findall('.//rtz:waypoint', ns)
        
        # Method 3: Try any namespace
        if not waypoint_elements:
            # Register the namespace if found
            namespace = ''
            if '}' in root.tag:
                namespace = root.tag.split('}')[0] + '}'
            if namespace:
                waypoint_elements = root.findall(f'.//{namespace}waypoint')
        
        logger.debug(f"Found {len(waypoint_elements)} waypoint elements")
        
        for wp_elem in waypoint_elements:
            try:
                # Extract position information
                position_elem = None
                
                # Try different ways to find position element
                if wp_elem.find('position') is not None:
                    position_elem = wp_elem.find('position')
                else:
                    # Try with namespace
                    for ns in ['', '{https://cirm.org/rtz-xml-schemas}']:
                        position_elem = wp_elem.find(f'{ns}position')
                        if position_elem is not None:
                            break
                
                if position_elem is not None and 'lat' in position_elem.attrib and 'lon' in position_elem.attrib:
                    waypoint = {
                        'name': wp_elem.get('name', ''),
                        'lat': float(position_elem.get('lat', 0)),
                        'lon': float(position_elem.get('lon', 0)),
                        'radius': float(wp_elem.get('radius', 0.1))  # Default radius 0.1 nm
                    }
                    waypoints.append(waypoint)
                    logger.debug(f"Added waypoint: {waypoint['name']} at {waypoint['lat']}, {waypoint['lon']}")
                else:
                    logger.warning(f"Could not extract position for waypoint: {wp_elem.get('name', 'unknown')}")
                    
            except Exception as e:
                logger.warning(f"Error processing waypoint element: {e}")
                continue
        
        if not waypoints:
            logger.warning(f"No waypoints found in {file_path}")
            return []
        
        # Calculate leg distances and total distance
        legs = []
        total_distance = 0.0
        
        for i in range(len(waypoints) - 1):
            wp1 = waypoints[i]
            wp2 = waypoints[i + 1]
            
            leg_distance = haversine_nm(wp1['lat'], wp1['lon'], wp2['lat'], wp2['lon'])
            legs.append({
                'from_waypoint': wp1['name'],
                'to_waypoint': wp2['name'],
                'distance_nm': round(leg_distance, 2)
            })
            total_distance += leg_distance
        
        # Extract origin and destination
        origin, destination = extract_origin_destination(route_name, waypoints)
        
        # Enhanced route information
        route_info = {
            'route_name': route_name,
            'file_path': file_path,
            'waypoints': waypoints,
            'legs': legs,
            'total_distance_nm': round(total_distance, 2),
            'waypoint_count': len(waypoints),
            'leg_count': len(legs),
            'origin': origin,
            'destination': destination,
            'parse_timestamp': datetime.now().isoformat(),
            'data_source': 'rtz_file_parser'
        }
        
        logger.info(f"✅ Successfully parsed route '{route_name}': {origin} → {destination} ({len(waypoints)} waypoints, {total_distance:.1f} nm)")
            
        return [route_info]
        
    except ET.ParseError as e:
        logger.error(f"XML parsing error in {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing RTZ file {file_path}: {e}")
        return []

def extract_origin_destination(route_name: str, waypoints: List[Dict]) -> Tuple[str, str]:
    """
    Extract origin and destination from route name or waypoints.
    Handles NCA route naming convention: NCA_Origin_Destination_*
    Enhanced with Norwegian port name normalization.
    """
    # Try to extract from route name first (NCA naming convention)
    if 'NCA_' in route_name:
        parts = route_name.split('_')
        if len(parts) >= 4:
            origin = parts[1].title()  # Capitalize first letter
            destination = parts[2].title()
            
            # Handle common abbreviations
            origin = _expand_abbreviation(origin)
            destination = _expand_abbreviation(destination)
            
            logger.debug(f"Extracted from route name: {origin} → {destination}")
            return origin, destination
    
    # Fallback: use first and last waypoint names
    if waypoints and len(waypoints) >= 2:
        origin = waypoints[0].get('name', 'Unknown')
        destination = waypoints[-1].get('name', 'Unknown')
        
        # Clean waypoint names
        origin = _clean_waypoint_name(origin)
        destination = _clean_waypoint_name(destination)
        
        logger.debug(f"Extracted from waypoints: {origin} → {destination}")
        return origin, destination
    
    logger.warning(f"Could not extract origin/destination for route: {route_name}")
    return 'Unknown', 'Unknown'

def _expand_abbreviation(name: str) -> str:
    """
    Expand common Norwegian port abbreviations to full names.
    Handles NCA route naming conventions and common abbreviations.
    """
    abbreviations = {
        # Major Norwegian ports - all 10 cities
        'Bergen': 'Bergen',
        'Trondheim': 'Trondheim', 
        'Stavanger': 'Stavanger',
        'Oslo': 'Oslo',
        'Alesund': 'Ålesund',
        'Andalsnes': 'Åndalsnes',
        'Kristiansand': 'Kristiansand',
        'Drammen': 'Drammen',
        'Sandefj': 'Sandefjord',
        'Sandefjord': 'Sandefjord',
        'Flekkefjord': 'Flekkefjord',
        
        # Common NCA abbreviations
        'Fedjeosen': 'Fedje',
        'Halten': 'Haltenbanken',
        'Stad': 'Stadthavet',
        'Breisundet': 'Breisundet',
        'Oksoy': 'Oksøy',
        'Sydostgr': 'Sydostgrunnen',
        'Bonden': 'Bonden',
        'Grip': 'Grip',
        'Grande': 'Rørvik',
        'Rorvik': 'Rørvik',
        'Steinsd': 'Steinsundet',
        'Krakhelle': 'Krakhellesundet',
        'Flavaer': 'Flævar',
        'Aramsd': 'Aramshavet',
        
        # Additional common Norwegian ports
        'Bodo': 'Bodø',
        'Tromso': 'Tromsø',
        'Narvik': 'Narvik',
        'Molde': 'Molde',
        'Haugesund': 'Haugesund',
        'Arendal': 'Arendal',
        'Larvik': 'Larvik',
        'Moss': 'Moss',
        'Horten': 'Horten'
    }
    
    expanded_name = abbreviations.get(name, name)
    if expanded_name != name:
        logger.debug(f"Expanded abbreviation: {name} → {expanded_name}")
    
    return expanded_name

def _clean_waypoint_name(name: str) -> str:
    """
    Clean waypoint names by removing technical details and VTS reports.
    Returns clean, human-readable port/waypoint names.
    """
    if not name:
        return 'Unknown'
    
    # Remove technical suffixes and VTS reports
    clean_name = name.split(' - report')[0].split(' lt')[0].split(' bn')[0]
    clean_name = clean_name.split(' buoy')[0].split(' 7.5 m')[0].split(' 9m')[0]
    clean_name = clean_name.split(' 13 m')[0].split(' pilot')[0]
    clean_name = clean_name.split(' VTS')[0].split(' traffic')[0]
    
    # Remove coordinates and technical markers
    clean_name = clean_name.split(' (')[0].split(' [')[0]
    
    # Capitalize first letter and strip whitespace
    clean_name = clean_name.strip()
    if clean_name:
        clean_name = clean_name[0].upper() + clean_name[1:]
    
    # Map common waypoint names to port names
    waypoint_to_port = {
        'Bergen Havn': 'Bergen',
        'Oslo Havn': 'Oslo',
        'Stavanger Havn': 'Stavanger',
        'Trondheim Havn': 'Trondheim',
        'Kristiansand Havn': 'Kristiansand',
        'Ålesund Havn': 'Ålesund',
        'Drammen Havn': 'Drammen',
        'Sandefjord Havn': 'Sandefjord',
        'Flekkefjord Havn': 'Flekkefjord'
    }
    
    final_name = waypoint_to_port.get(clean_name, clean_name)
    
    if final_name != name:
        logger.debug(f"Cleaned waypoint name: {name} → {final_name}")
    
    return final_name

def find_rtz_files() -> Dict[str, List[str]]:
    """
    Find ALL RTZ and ZIP files in the assets directory.
    ENHANCED: Now searches recursively and finds all 47+ route files.
    
    Returns:
        Dictionary with city names and their RTZ/ZIP file paths
    """
    project_root = get_project_root()
    base_path = os.path.join(project_root, "backend", "assets", "routeinfo_routes")
    rtz_files = {}
    
    cities = [
        'alesund', 'andalsnes', 'bergen', 'drammen', 'flekkefjord',
        'kristiansand', 'oslo', 'sandefjord', 'stavanger', 'trondheim'
    ]
    
    logger.info(f"🔍 Searching for ALL RTZ and ZIP files in: {base_path}")
    
    for city in cities:
        city_path = os.path.join(base_path, city)
        if not os.path.exists(city_path):
            logger.warning(f"City directory not found: {city_path}")
            continue
            
        found_files = []
        
        # Search for ALL .rtz files recursively
        rtz_pattern = os.path.join(city_path, "**", "*.rtz")
        rtz_matches = glob.glob(rtz_pattern, recursive=True)
        
        # Search for ALL .zip files recursively
        zip_pattern = os.path.join(city_path, "**", "*.zip")
        zip_matches = glob.glob(zip_pattern, recursive=True)
        
        # Combine all found files
        all_matches = rtz_matches + zip_matches
        
        if all_matches:
            rtz_files[city] = all_matches
            logger.info(f"✅ Found {len(all_matches)} files for {city}:")
            for file in all_matches[:3]:  # Show first 3 files
                logger.info(f"   • {os.path.basename(file)}")
            if len(all_matches) > 3:
                logger.info(f"   ... and {len(all_matches) - 3} more")
        else:
            logger.warning(f"❌ No RTZ/ZIP files found for {city}")
    
    return rtz_files

def enhance_route_data_with_visuals(routes_data: List[Dict]) -> List[Dict]:
    """
    Add visual properties to route data for better map display.
    Each route gets a unique color, markers for start/end, and visual properties.
    
    Args:
        routes_data: List of route dictionaries
        
    Returns:
        Enhanced routes with visual properties
    """
    enhanced_routes = []
    city_colors = generate_route_colors()
    
    for i, route in enumerate(routes_data):
        enhanced = route.copy()
        source_city = route.get('source_city', 'unknown').lower()
        
        # Assign color based on city or generate unique
        color = city_colors.get(source_city, generate_unique_color(route.get('route_name', f'route_{i}'), i))
        
        # Add visual properties for map display
        enhanced['visual_properties'] = {
            'color': color,
            'weight': 3,  # Line thickness
            'opacity': 0.8,
            'dashArray': 'none',
            'line_cap': 'round',
            'line_join': 'round',
            'start_marker_color': '#00FF00',  # Green for start
            'end_marker_color': '#FF0000',    # Red for destination
            'start_marker_radius': 8,
            'end_marker_radius': 10,
            'zIndex': i + 100,  # Ensure proper layering
            'highlight_weight': 6,  # Thicker when highlighted
            'highlight_color': '#FFFF00',  # Yellow for highlighting
        }
        
        # Add clear start/end points
        if route.get('waypoints'):
            waypoints = route['waypoints']
            enhanced['start_point'] = {
                'lat': waypoints[0]['lat'],
                'lon': waypoints[0]['lon'],
                'name': waypoints[0].get('name', 'Start')
            }
            enhanced['end_point'] = {
                'lat': waypoints[-1]['lat'],
                'lon': waypoints[-1]['lon'],
                'name': waypoints[-1].get('name', 'End')
            }
            
            # Calculate midpoint for label
            if len(waypoints) > 1:
                mid_idx = len(waypoints) // 2
                enhanced['label_position'] = {
                    'lat': waypoints[mid_idx]['lat'],
                    'lon': waypoints[mid_idx]['lon']
                }
        
        enhanced_routes.append(enhanced)
    
    logger.info(f"🎨 Enhanced {len(enhanced_routes)} routes with visual properties")
    return enhanced_routes

def discover_rtz_files(enhanced: bool = True) -> List[Dict]:
    """
    Discover and parse ALL RTZ files from all cities.
    FIXED: Now properly handles ZIP files and finds ALL 47+ routes.
    ENHANCED: Can return routes with visual properties for map display.
    
    Args:
        enhanced: Whether to add visual properties to routes
        
    Returns:
        List of ALL route dictionaries from all cities (with or without visual properties)
    """
    rtz_files = find_rtz_files()
    all_routes = []
    
    logger.info(f"🚀 Starting comprehensive RTZ discovery for {len(rtz_files)} cities...")
    
    for city, file_paths in rtz_files.items():
        logger.info(f"📂 Processing ALL routes for {city}...")
        
        for file_path in file_paths:
            try:
                logger.info(f"   📄 Analyzing: {os.path.basename(file_path)}")
                
                # Check if it's a ZIP file
                with open(file_path, 'rb') as f:
                    file_header = f.read(4)
                    is_zip = file_header == b'PK\x03\x04'
                
                if is_zip:
                    # Extract ALL RTZ files from ZIP
                    routes = extract_all_routes_from_zip(file_path, city)
                    if routes:
                        all_routes.extend(routes)
                        logger.info(f"   ✅ Found {len(routes)} routes in {os.path.basename(file_path)}")
                else:
                    # Direct RTZ file
                    routes = parse_rtz_file(file_path)
                    if routes:
                        # Add city metadata
                        for route in routes:
                            route['source_city'] = city
                            route['original_file'] = os.path.basename(file_path)
                        all_routes.extend(routes)
                        logger.info(f"   ✅ Found {len(routes)} routes in {os.path.basename(file_path)}")
                        
            except Exception as e:
                logger.error(f"   ❌ Error processing {file_path}: {e}")
                continue
    
    logger.info(f"🎉 Total routes discovered across all cities: {len(all_routes)}")
    
    # Log statistics
    cities_with_routes = set(route.get('source_city', 'unknown') for route in all_routes)
    logger.info(f"📊 Cities with routes: {len(cities_with_routes)}/{len(rtz_files)}")
    
    # Log breakdown by city
    if all_routes:
        routes_by_city = {}
        for route in all_routes:
            city = route.get('source_city', 'unknown')
            routes_by_city.setdefault(city, 0)
            routes_by_city[city] += 1
        
        logger.info("📈 Route breakdown by city:")
        for city, count in sorted(routes_by_city.items()):
            logger.info(f"   • {city.title()}: {count} routes")
    
    # Enhance routes with visual properties if requested
    if enhanced and all_routes:
        all_routes = enhance_route_data_with_visuals(all_routes)
    
    return all_routes

def save_rtz_routes_to_db(routes_data: List[Dict]) -> int:
    """
    Save parsed RTZ routes to database using proper SQLAlchemy models.
    ENHANCED: Extracts and stores origin/destination information with improved error handling.
    Maintains existing database integration.
    """
    try:
        # Import database models within application context
        from app import create_app
        from backend.models import Route, VoyageLeg
        from backend.extensions import db
        
        # Create Flask app and application context
        app = create_app()
        
        with app.app_context():
            saved_count = 0
            error_count = 0
            
            for route_info in routes_data:
                try:
                    # Check if route already exists
                    existing_route = Route.query.filter(
                        Route.name == route_info['route_name']
                    ).first()
                    
                    if existing_route:
                        logger.info(f"Route '{route_info['route_name']}' already exists, skipping")
                        continue
                    
                    # ENHANCED: Extract origin and destination
                    waypoints = route_info['waypoints']
                    origin, destination = extract_origin_destination(route_info['route_name'], waypoints)
                    
                    # ENHANCED: Calculate duration (assume 15 knots average commercial speed)
                    total_distance = route_info['total_distance_nm']
                    duration_days = round(total_distance / (15 * 24), 2)  # 15 knots * 24 hours
                    
                    # Create main Route entry with enhanced data
                    new_route = Route(
                        name=route_info['route_name'],
                        total_distance_nm=total_distance,
                        origin=origin,
                        destination=destination,
                        duration_days=duration_days,
                        description=f"Official NCA route: {origin} → {destination} ({total_distance} nm)",
                        is_active=True
                    )
                    db.session.add(new_route)
                    db.session.flush()  # Get the route ID
                    
                    # Create VoyageLegs for each segment between waypoints
                    for i in range(len(waypoints) - 1):
                        start_wp = waypoints[i]
                        end_wp = waypoints[i + 1]
                        
                        # Find the corresponding leg distance
                        leg_distance = 0.0
                        if i < len(route_info['legs']):
                            leg_distance = route_info['legs'][i]['distance_nm']
                        else:
                            # Calculate if not available
                            leg_distance = haversine_nm(
                                start_wp['lat'], start_wp['lon'],
                                end_wp['lat'], end_wp['lon']
                            )
                        
                        # Create voyage leg with enhanced data
                        voyage_leg = VoyageLeg(
                            route_id=new_route.id,
                            leg_order=i + 1,
                            departure_lat=start_wp['lat'],
                            departure_lon=start_wp['lon'],
                            arrival_lat=end_wp['lat'],
                            arrival_lon=end_wp['lon'],
                            distance_nm=round(leg_distance, 2),
                            departure_time=datetime.utcnow(),  # Placeholder for actual schedule
                            arrival_time=datetime.utcnow(),    # Placeholder for actual schedule
                            is_active=True
                        )
                        db.session.add(voyage_leg)
                    
                    saved_count += 1
                    logger.info(f"✅ Saved route '{route_info['route_name']}' ({origin} → {destination}) with {len(waypoints)} waypoints")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Failed to save route '{route_info['route_name']}': {str(e)}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            if saved_count > 0:
                logger.info(f"🎉 Successfully saved {saved_count} routes to database")
            if error_count > 0:
                logger.warning(f"⚠️ {error_count} routes failed to save")
            
            return saved_count
        
    except ImportError as e:
        logger.warning(f"Database models not available: {e}")
        return 0
    except Exception as e:
        logger.error(f"Database save operation failed: {e}")
        return 0

def get_processing_statistics() -> Dict:
    """
    Get statistics about RTZ route processing.
    Returns information about processed cities and routes.
    """
    rtz_files = find_rtz_files()
    
    stats = {
        'total_cities': 10,
        'cities_with_routes': len(rtz_files),
        'cities_missing_files': [],
        'total_files_found': sum(len(files) for files in rtz_files.values()),
        'cities_with_files': list(rtz_files.keys()),
        'project_root': get_project_root(),
        'timestamp': datetime.now().isoformat()
    }
    
    all_cities = [
        'alesund', 'andalsnes', 'bergen', 'drammen', 'flekkefjord',
        'kristiansand', 'oslo', 'sandefjord', 'stavanger', 'trondheim'
    ]
    
    stats['cities_missing_files'] = [city for city in all_cities if city not in rtz_files]
    
    return stats

def process_all_cities_routes() -> int:
    """
    Process all RTZ files for all 10 Norwegian cities.
    FIXED: Handles both direct XML and ZIP-compressed RTZ files with correct namespaces.
    ENHANCED: Processes ALL routes in each ZIP file, not just the first one.
    Returns count of successfully processed routes.
    """
    all_routes = discover_rtz_files(enhanced=False)
    total_routes = len(all_routes)
    
    logger.info(f"🔄 Processing {total_routes} discovered routes...")
    
    # Save all routes to database
    if all_routes:
        saved_count = save_rtz_routes_to_db(all_routes)
        logger.info(f"🎉 Processing complete: {saved_count} routes saved out of {total_routes} discovered")
        return saved_count
    else:
        logger.error("❌ No routes were discovered")
        return 0

# Command-line interface for manual processing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚢 BergNavn RTZ Parser - Norwegian Coastal Routes")
    print("=" * 50)
    
    # Show statistics first
    stats = get_processing_statistics()
    print(f"📊 Processing Statistics:")
    print(f"   Project root: {stats['project_root']}")
    print(f"   Total cities: {stats['total_cities']}")
    print(f"   Cities with RTZ files: {stats['cities_with_routes']}")
    print(f"   Total RTZ files found: {stats['total_files_found']}")
    
    if stats['cities_with_files']:
        print(f"   Cities with files: {', '.join(stats['cities_with_files'])}")
    
    if stats['cities_missing_files']:
        print(f"   Cities missing files: {', '.join(stats['cities_missing_files'])}")
    
    print("\n🔄 Starting comprehensive route discovery...")
    
    # Discover all routes (with visual enhancement)
    all_routes = discover_rtz_files(enhanced=True)
    
    if all_routes:
        print(f"✅ Discovered {len(all_routes)} total routes")
        print(f"\n📊 Route breakdown by city:")
        
        # Group by city
        routes_by_city = {}
        for route in all_routes:
            city = route.get('source_city', 'unknown')
            routes_by_city.setdefault(city, 0)
            routes_by_city[city] += 1
        
        for city, count in sorted(routes_by_city.items()):
            print(f"   • {city.title()}: {count} routes")
        
        # Show visual properties
        if all_routes[0].get('visual_properties'):
            print(f"\n🎨 Visual properties added:")
            print(f"   • Unique colors for each city")
            print(f"   • Start/end markers")
            print(f"   • Enhanced map display")
        
        # Process to database (without visual properties)
        print(f"\n💾 Saving routes to database...")
        result = process_all_cities_routes()
        
        if result > 0:
            print(f"✅ Successfully processed {result} maritime routes")
        else:
            print("❌ No routes were saved to database")
    else:
        print("❌ No routes were discovered")
        print("💡 Check that RTZ files exist in backend/assets/routeinfo_routes/")
        
        # Show directory structure for debugging
        print("\n🔍 Directory structure:")
        project_root = get_project_root()
        assets_path = os.path.join(project_root, "backend", "assets")
        if os.path.exists(assets_path):
            print(f"Assets directory exists: {assets_path}")
            for item in os.listdir(assets_path):
                print(f"  📁 {item}")
        else:
            print(f"Assets directory not found: {assets_path}")