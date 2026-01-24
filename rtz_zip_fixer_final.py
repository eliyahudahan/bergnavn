#!/usr/bin/env python3
"""
RTZ ZIP Fixer - Final Version with correct namespace handling
Processes Norwegian coastal routes from Kystverket ZIP files
"""

import os
import sys
import zipfile
import shutil
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rtz_processing.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def extract_zip_files(zip_path: str, target_dir: str) -> List[str]:
    """Extract all RTZ files from ZIP archive."""
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in ZIP
            file_list = zip_ref.namelist()
            logger.info(f"Found {len(file_list)} files in {os.path.basename(zip_path)}")
            
            # Create target directory
            os.makedirs(target_dir, exist_ok=True)
            
            # Extract all .rtz files
            for file_name in file_list:
                if file_name.lower().endswith('.rtz'):
                    # Clean filename
                    clean_name = os.path.basename(file_name)
                    extracted_path = os.path.join(target_dir, clean_name)
                    
                    # Skip if already exists
                    if os.path.exists(extracted_path):
                        logger.debug(f"Already exists: {clean_name}")
                        extracted_files.append(extracted_path)
                        continue
                    
                    try:
                        # Extract the file
                        zip_ref.extract(file_name, target_dir)
                        
                        # Handle nested directories
                        actual_extracted = os.path.join(target_dir, file_name)
                        if os.path.exists(actual_extracted) and actual_extracted != extracted_path:
                            shutil.move(actual_extracted, extracted_path)
                        
                        extracted_files.append(extracted_path)
                        logger.debug(f"Extracted: {clean_name}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting {file_name}: {e}")
        
        logger.info(f"Extracted {len(extracted_files)} RTZ files")
        return extracted_files
        
    except Exception as e:
        logger.error(f"Error extracting {zip_path}: {e}")
        return []


def parse_rtz_file_correctly(rtz_file: str) -> Optional[Dict]:
    """
    Parse RTZ file with the correct namespace from Kystverket.
    """
    try:
        with open(rtz_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse XML with the correct namespace
        root = ET.fromstring(content)
        
        # Define namespace - exactly as in the file
        ns = {'rtz': 'https://cirm.org/rtz-xml-schemas'}
        
        # Find routeInfo
        route_info = root.find('rtz:routeInfo', ns)
        route_name = route_info.get('routeName', '') if route_info is not None else ''
        
        # If no route name from XML, use filename
        if not route_name:
            filename = os.path.basename(rtz_file)
            route_name = filename.replace('.rtz', '').replace('_', ' ')
        
        # Find waypoints
        waypoints_elem = root.find('rtz:waypoints', ns)
        if waypoints_elem is None:
            logger.warning(f"No waypoints element found in {os.path.basename(rtz_file)}")
            return None
        
        # Get all waypoint elements
        waypoints = []
        wp_elements = waypoints_elem.findall('rtz:waypoint', ns)
        
        logger.info(f"Found {len(wp_elements)} waypoint elements")
        
        for wp_elem in wp_elements:
            # Get waypoint attributes
            wp_id = wp_elem.get('id', '')
            wp_name = wp_elem.get('name', '')
            
            # Find position element
            position = wp_elem.find('rtz:position', ns)
            if position is not None:
                lat = position.get('lat')
                lon = position.get('lon')
                
                if lat and lon:
                    try:
                        waypoint = {
                            'id': wp_id,
                            'name': wp_name,
                            'lat': float(lat),
                            'lon': float(lon),
                            'description': wp_elem.get('description', ''),
                            'radius': wp_elem.get('radius', ''),
                            'turn_radius': wp_elem.get('turnRadius', '')
                        }
                        waypoints.append(waypoint)
                    except ValueError:
                        logger.warning(f"Invalid coordinates in waypoint {wp_id}: lat={lat}, lon={lon}")
        
        if not waypoints:
            logger.warning(f"No valid waypoints found in {os.path.basename(rtz_file)}")
            return None
        
        # Calculate total distance
        total_distance = 0.0
        segment_distances = []
        
        if len(waypoints) > 1:
            for i in range(len(waypoints) - 1):
                wp1 = waypoints[i]
                wp2 = waypoints[i + 1]
                
                # Convert to radians
                lat1_rad = math.radians(wp1['lat'])
                lon1_rad = math.radians(wp1['lon'])
                lat2_rad = math.radians(wp2['lat'])
                lon2_rad = math.radians(wp2['lon'])
                
                # Haversine formula
                dlon = lon2_rad - lon1_rad
                dlat = lat2_rad - lat1_rad
                a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance_nm = 3440.065 * c
                
                segment_distances.append({
                    'from': wp1['name'],
                    'to': wp2['name'],
                    'distance_nm': round(distance_nm, 2)
                })
                
                total_distance += distance_nm
        
        # Get origin and destination
        origin = waypoints[0]['name'] if waypoints else "Unknown"
        destination = waypoints[-1]['name'] if waypoints else "Unknown"
        
        # Create bounding box for map
        bbox = None
        if waypoints:
            lats = [wp['lat'] for wp in waypoints]
            lons = [wp['lon'] for wp in waypoints]
            bbox = {
                'min_lat': min(lats),
                'max_lat': max(lats),
                'min_lon': min(lons),
                'max_lon': max(lons)
            }
        
        return {
            'route_name': route_name,
            'file_name': os.path.basename(rtz_file),
            'file_path': rtz_file,
            'waypoints': waypoints,
            'waypoint_count': len(waypoints),
            'total_distance_nm': round(total_distance, 2),
            'segment_distances': segment_distances,
            'origin': origin,
            'destination': destination,
            'origin_coords': waypoints[0] if waypoints else None,
            'destination_coords': waypoints[-1] if waypoints else None,
            'bbox': bbox,
            'parsed_at': datetime.now().isoformat(),
            'is_valid': len(waypoints) >= 2,
            'source_zip': os.path.basename(rtz_file).replace('.rtz', '_routes.rtz')
        }
        
    except ET.ParseError as e:
        logger.error(f"XML parsing error in {rtz_file}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing {rtz_file}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def process_city(city_path: str) -> List[Dict]:
    """Process all ZIP files in a city directory."""
    city_name = os.path.basename(city_path)
    logger.info(f"Processing city: {city_name}")
    
    routes = []
    
    # Check raw directory
    raw_dir = os.path.join(city_path, 'raw')
    if not os.path.exists(raw_dir):
        logger.warning(f"No raw directory found: {raw_dir}")
        return routes
    
    # Create extracted directory
    extracted_dir = os.path.join(city_path, 'extracted')
    os.makedirs(extracted_dir, exist_ok=True)
    
    # Find ZIP files (files ending with _routes.rtz)
    for item in os.listdir(raw_dir):
        if item.endswith('_routes.rtz'):
            zip_path = os.path.join(raw_dir, item)
            
            if not os.path.exists(zip_path):
                continue
            
            logger.info(f"Processing ZIP: {item}")
            
            # Extract files
            extracted_files = extract_zip_files(zip_path, extracted_dir)
            
            # Parse each RTZ file
            for rtz_file in extracted_files:
                logger.info(f"Parsing: {os.path.basename(rtz_file)}")
                route_data = parse_rtz_file_correctly(rtz_file)
                
                if route_data:
                    route_data['city'] = city_name
                    routes.append(route_data)
                    
                    logger.info(f"  ✓ {route_data['route_name']}: "
                              f"{route_data['waypoint_count']} waypoints, "
                              f"{route_data['total_distance_nm']} nm, "
                              f"{route_data['origin']} → {route_data['destination']}")
                else:
                    logger.warning(f"  ✗ Failed to parse: {os.path.basename(rtz_file)}")
    
    return routes


def create_geojson_output(routes: List[Dict], output_dir: str) -> Dict:
    """Create GeoJSON format for map display."""
    
    # Create FeatureCollection for routes (lines)
    route_features = []
    
    # Create FeatureCollection for waypoints (points)
    waypoint_features = []
    
    route_id = 0
    
    for route in routes:
        if not route['is_valid'] or len(route['waypoints']) < 2:
            continue
        
        route_id += 1
        
        # Create line feature for the route
        coordinates = [[wp['lon'], wp['lat']] for wp in route['waypoints']]
        
        route_feature = {
            'type': 'Feature',
            'properties': {
                'id': f"route_{route_id}",
                'name': route['route_name'],
                'city': route.get('city', 'Unknown'),
                'origin': route['origin'],
                'destination': route['destination'],
                'distance_nm': route['total_distance_nm'],
                'waypoint_count': route['waypoint_count'],
                'source_file': route['file_name'],
                'color': '#1E88E5',
                'opacity': 0.7,
                'weight': 3
            },
            'geometry': {
                'type': 'LineString',
                'coordinates': coordinates
            }
        }
        
        route_features.append(route_feature)
        
        # Create point features for waypoints
        for i, wp in enumerate(route['waypoints']):
            is_start = i == 0
            is_end = i == len(route['waypoints']) - 1
            
            wp_feature = {
                'type': 'Feature',
                'properties': {
                    'id': f"wp_{route_id}_{i+1}",
                    'route_id': f"route_{route_id}",
                    'route_name': route['route_name'],
                    'name': wp['name'],
                    'description': wp.get('description', ''),
                    'order': i + 1,
                    'is_start': is_start,
                    'is_end': is_end,
                    'marker_color': '#FF5722' if is_start else '#4CAF50' if is_end else '#757575',
                    'marker_size': 'large' if is_start or is_end else 'medium'
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [wp['lon'], wp['lat']]
                }
            }
            
            waypoint_features.append(wp_feature)
    
    # Create the complete GeoJSON structure
    geojson_data = {
        'routes': {
            'type': 'FeatureCollection',
            'features': route_features
        },
        'waypoints': {
            'type': 'FeatureCollection',
            'features': waypoint_features
        },
        'metadata': {
            'total_routes': len([r for r in routes if r['is_valid']]),
            'total_waypoints': sum(len(r['waypoints']) for r in routes if r['is_valid']),
            'generated_at': datetime.now().isoformat(),
            'cities': list(set(r.get('city', 'Unknown') for r in routes if r['is_valid']))
        }
    }
    
    # Save to file
    geojson_file = os.path.join(output_dir, 'coastal_routes.geojson')
    with open(geojson_file, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"GeoJSON saved to: {geojson_file}")
    
    # Also save simplified version for quick loading
    simplified = {
        'type': 'FeatureCollection',
        'features': route_features + waypoint_features
    }
    
    simplified_file = os.path.join(output_dir, 'coastal_routes_simple.geojson')
    with open(simplified_file, 'w', encoding='utf-8') as f:
        json.dump(simplified, f, indent=2, ensure_ascii=False)
    
    return geojson_data


def main():
    """Main processing function."""
    print("=" * 70)
    print("NORWEGIAN COASTAL ROUTES PROCESSOR")
    print("=" * 70)
    
    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths
    routes_dir = os.path.join(project_root, 'backend', 'assets', 'routeinfo_routes')
    output_dir = os.path.join(project_root, 'backend', 'assets', 'route_data', 'processed')
    
    if not os.path.exists(routes_dir):
        print(f"❌ Routes directory not found: {routes_dir}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Source directory: {routes_dir}")
    print(f"💾 Output directory: {output_dir}")
    
    # Process each city
    all_routes = []
    city_stats = {}
    
    for city_dir in sorted(os.listdir(routes_dir)):
        city_path = os.path.join(routes_dir, city_dir)
        
        if os.path.isdir(city_path) and not city_dir.startswith('_'):
            print(f"\n📍 Processing: {city_dir.title()}")
            
            routes = process_city(city_path)
            
            if routes:
                all_routes.extend(routes)
                
                valid_routes = [r for r in routes if r['is_valid']]
                waypoint_count = sum(len(r['waypoints']) for r in valid_routes)
                
                city_stats[city_dir] = {
                    'total_routes': len(routes),
                    'valid_routes': len(valid_routes),
                    'waypoint_count': waypoint_count
                }
                
                print(f"  ✅ Found: {len(valid_routes)} valid routes, {waypoint_count} waypoints")
                
                # Show sample
                for route in valid_routes[:2]:
                    print(f"    🛣️  {route['route_name']}: "
                          f"{route['origin']} → {route['destination']} "
                          f"({route['total_distance_nm']} nm)")
                
                if len(valid_routes) > 2:
                    print(f"    ... and {len(valid_routes) - 2} more")
            else:
                print(f"  ⚠️  No routes found")
    
    # Process results
    if all_routes:
        valid_routes = [r for r in all_routes if r['is_valid']]
        
        print(f"\n{'='*70}")
        print("📊 PROCESSING SUMMARY")
        print(f"{'='*70}")
        
        total_waypoints = sum(len(r['waypoints']) for r in valid_routes)
        total_distance = sum(r['total_distance_nm'] for r in valid_routes)
        
        print(f"🏙️  Cities processed: {len(city_stats)}")
        print(f"🛣️  Total valid routes: {len(valid_routes)}")
        print(f"📍 Total waypoints: {total_waypoints}")
        print(f"📏 Total distance: {round(total_distance, 2)} nautical miles")
        
        # Save statistics
        stats_file = os.path.join(output_dir, 'processing_stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'city_stats': city_stats,
                'total_valid_routes': len(valid_routes),
                'total_waypoints': total_waypoints,
                'total_distance_nm': round(total_distance, 2),
                'generated_at': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Statistics saved to: {stats_file}")
        
        # Create GeoJSON output
        print(f"\n🗺️  Creating map data...")
        geojson_data = create_geojson_output(valid_routes, output_dir)
        
        # Also save raw routes data
        routes_file = os.path.join(output_dir, 'all_routes_data.json')
        with open(routes_file, 'w', encoding='utf-8') as f:
            json.dump({
                'routes': valid_routes,
                'metadata': {
                    'count': len(valid_routes),
                    'generated_at': datetime.now().isoformat()
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Routes data saved to: {routes_file}")
        
        print(f"\n🎉 PROCESSING COMPLETED SUCCESSFULLY!")
        print(f"\n📋 Next steps:")
        print(f"1. GeoJSON files are ready in: {output_dir}")
        print(f"2. Use 'coastal_routes.geojson' or 'coastal_routes_simple.geojson' in your map")
        print(f"3. Waypoints are included with names, coordinates, and start/end markers")
        print(f"4. Each route is a complete line from origin to destination")
        
    else:
        print(f"\n❌ No valid routes were found.")
        print(f"Check the log file for details: rtz_processing.log")
    
    print(f"\n📝 Log file: rtz_processing.log")


if __name__ == "__main__":
    main()