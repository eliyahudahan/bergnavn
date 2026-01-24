#!/usr/bin/env python3
"""
RTZ ZIP Fixer - Fixes ZIP archives from Kystverket and extracts waypoints with names
This script processes ZIP RTZ files from Norwegian coastal routes,
extracts waypoints with proper names, and saves them in JSON format for map display.
"""

import os
import sys
import zipfile
import shutil
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import xml.etree.ElementTree as ET
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rtz_fixer.log')
    ]
)
logger = logging.getLogger(__name__)


def is_zip_file(filepath: str) -> bool:
    """Check if a file is a ZIP archive."""
    try:
        with open(filepath, 'rb') as f:
            return zipfile.is_zipfile(filepath)
    except:
        return False


def extract_zip_rtz_files(zip_path: str, target_dir: str) -> List[str]:
    """
    Extract RTZ files from ZIP archive.
    
    Args:
        zip_path: Path to ZIP file
        target_dir: Directory to extract files to
        
    Returns:
        List of extracted RTZ file paths
    """
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in ZIP
            file_list = zip_ref.namelist()
            logger.info(f"Found {len(file_list)} files in {os.path.basename(zip_path)}")
            
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Extract all .rtz files
            for file_name in file_list:
                if file_name.lower().endswith('.rtz'):
                    # Clean filename - take only the basename
                    clean_name = os.path.basename(file_name)
                    
                    # Skip if already extracted
                    extracted_path = os.path.join(target_dir, clean_name)
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
                            # Move from nested location to target directory
                            shutil.move(actual_extracted, extracted_path)
                            
                            # Clean up empty directories
                            parent_dir = os.path.dirname(actual_extracted)
                            if parent_dir != target_dir:
                                try:
                                    os.removedirs(parent_dir)
                                except:
                                    pass
                        
                        if os.path.exists(extracted_path):
                            logger.debug(f"Extracted: {clean_name}")
                            extracted_files.append(extracted_path)
                        else:
                            logger.warning(f"Failed to extract: {clean_name}")
                            
                    except Exception as e:
                        logger.error(f"Error extracting {file_name}: {e}")
                        continue
        
        logger.info(f"Extracted {len(extracted_files)} RTZ files from {os.path.basename(zip_path)}")
        return extracted_files
        
    except zipfile.BadZipFile:
        logger.error(f"File is not a valid ZIP archive: {zip_path}")
        return []
    except Exception as e:
        logger.error(f"Error extracting ZIP file {zip_path}: {e}")
        return []


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in nautical miles using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates in degrees
        lat2, lon2: Second point coordinates in degrees
        
    Returns:
        Distance in nautical miles
    """
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Earth radius in nautical miles (3440.065 nm)
    distance_nm = 3440.065 * c
    return distance_nm


def parse_rtz_file(rtz_file: str) -> Optional[Dict]:
    """
    Parse a single RTZ XML file and extract waypoints WITH NAMES.
    
    Args:
        rtz_file: Path to RTZ XML file
        
    Returns:
        Route dictionary with waypoint names
    """
    try:
        # Read and parse the XML file
        with open(rtz_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Register namespaces for RTZ format
        namespaces = {
            'ns': 'http://www.cirm.org/RTZ/1/0',
            'ns2': 'http://www.cirm.org/RTZ/1/1',
            '': 'http://www.cirm.org/RTZ/1/0'  # Default namespace
        }
        
        # Try to parse with different namespace approaches
        root = None
        for ns_prefix, ns_uri in namespaces.items():
            try:
                if ns_prefix:
                    ET.register_namespace(ns_prefix, ns_uri)
                root = ET.fromstring(xml_content)
                break
            except:
                continue
        
        if root is None:
            # Try without namespace
            root = ET.fromstring(xml_content)
        
        # Find routeInfo - try different namespace variations
        route_info = None
        for tag in ['routeInfo', '{http://www.cirm.org/RTZ/1/0}routeInfo', 
                    '{http://www.cirm.org/RTZ/1/1}routeInfo']:
            route_info = root.find(tag)
            if route_info is not None:
                break
        
        route_name = ""
        if route_info is not None:
            route_name = route_info.get('routeName', '')
            if not route_name:
                route_name = route_info.get('name', '')
        
        # Find waypoints - try different namespace variations
        waypoints_elem = None
        for tag in ['waypoints', '{http://www.cirm.org/RTZ/1/0}waypoints',
                    '{http://www.cirm.org/RTZ/1/1}waypoints']:
            waypoints_elem = root.find(tag)
            if waypoints_elem is not None:
                break
        
        if waypoints_elem is None:
            logger.warning(f"No waypoints found in {os.path.basename(rtz_file)}")
            return None
        
        waypoints = []
        
        # Find all waypoint elements
        wp_elements = []
        for tag in ['waypoint', '{http://www.cirm.org/RTZ/1/0}waypoint',
                    '{http://www.cirm.org/RTZ/1/1}waypoint']:
            wp_elements = waypoints_elem.findall(tag)
            if wp_elements:
                break
        
        logger.info(f"Found {len(wp_elements)} waypoints in {os.path.basename(rtz_file)}")
        
        for wp_elem in wp_elements:
            # Find position element
            position = None
            for tag in ['position', '{http://www.cirm.org/RTZ/1/0}position',
                        '{http://www.cirm.org/RTZ/1/1}position']:
                position = wp_elem.find(tag)
                if position is not None:
                    break
            
            if position is not None:
                lat = position.get('lat')
                lon = position.get('lon')
                
                if lat and lon:
                    # Extract waypoint information
                    wp_name = wp_elem.get('name', '')
                    wp_id = wp_elem.get('id', '')
                    
                    # If no name, try to get from id or create a descriptive name
                    if not wp_name and wp_id:
                        wp_name = f"WP_{wp_id}"
                    
                    # Extract additional information
                    desc = wp_elem.get('description', '')
                    if not desc:
                        # Try to find description element
                        for desc_tag in ['description', '{http://www.cirm.org/RTZ/1/0}description']:
                            desc_elem = wp_elem.find(desc_tag)
                            if desc_elem is not None and desc_elem.text:
                                desc = desc_elem.text
                                break
                    
                    waypoint = {
                        'lat': float(lat),
                        'lon': float(lon),
                        'name': wp_name,
                        'id': wp_id,
                        'description': desc,
                        'turn_radius': wp_elem.get('turnRadius', ''),
                        'speed_max': wp_elem.get('speedMax', ''),
                        'geometry_type': wp_elem.get('geometryType', 'Loxodrome')
                    }
                    waypoints.append(waypoint)
        
        if not waypoints:
            logger.warning(f"No valid waypoints found in {os.path.basename(rtz_file)}")
            return None
        
        # Calculate total distance and segment distances
        total_distance = 0.0
        segment_distances = []
        
        if len(waypoints) > 1:
            for i in range(len(waypoints) - 1):
                wp1 = waypoints[i]
                wp2 = waypoints[i + 1]
                
                distance = calculate_distance(
                    wp1['lat'], wp1['lon'],
                    wp2['lat'], wp2['lon']
                )
                
                segment_distances.append({
                    'from': wp1['name'],
                    'to': wp2['name'],
                    'distance_nm': round(distance, 2)
                })
                
                total_distance += distance
        
        # Determine origin and destination from waypoint names
        origin = "Unknown"
        destination = "Unknown"
        
        if waypoints:
            if waypoints[0]['name']:
                origin = waypoints[0]['name']
            elif waypoints[0]['id']:
                origin = f"Start_{waypoints[0]['id']}"
            
            if waypoints[-1]['name']:
                destination = waypoints[-1]['name']
            elif waypoints[-1]['id']:
                destination = f"End_{waypoints[-1]['id']}"
        
        # Extract route metadata from filename if route_name is empty
        if not route_name:
            filename = os.path.basename(rtz_file)
            route_name = filename.replace('.rtz', '').replace('_', ' ')
        
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
            'parsed_at': datetime.now().isoformat(),
            'is_valid': len(waypoints) >= 2,
            'bbox': {
                'min_lat': min(wp['lat'] for wp in waypoints),
                'max_lat': max(wp['lat'] for wp in waypoints),
                'min_lon': min(wp['lon'] for wp in waypoints),
                'max_lon': max(wp['lon'] for wp in waypoints)
            } if waypoints else None
        }
        
    except ET.ParseError as e:
        logger.error(f"XML parsing error in {rtz_file}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing RTZ file {rtz_file}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def save_routes_to_json(routes_data: Dict[str, List[Dict]], output_dir: str):
    """
    Save parsed routes to JSON files for each city.
    
    Args:
        routes_data: Dictionary with city names as keys and route lists as values
        output_dir: Directory to save JSON files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    all_routes_summary = {
        'total_cities': len(routes_data),
        'total_routes': 0,
        'total_waypoints': 0,
        'cities': {},
        'generated_at': datetime.now().isoformat()
    }
    
    for city, routes in routes_data.items():
        if not routes:
            continue
            
        city_data = {
            'city_name': city,
            'route_count': len(routes),
            'waypoint_count': sum(r['waypoint_count'] for r in routes),
            'routes': routes,
            'valid_routes': [r for r in routes if r['is_valid']],
            'invalid_routes': [r for r in routes if not r['is_valid']]
        }
        
        # Save individual city file
        city_filename = f"{city.lower()}_routes.json"
        city_path = os.path.join(output_dir, city_filename)
        
        with open(city_path, 'w', encoding='utf-8') as f:
            json.dump(city_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(routes)} routes for {city} to {city_filename}")
        
        # Update summary
        all_routes_summary['total_routes'] += len(routes)
        all_routes_summary['total_waypoints'] += city_data['waypoint_count']
        all_routes_summary['cities'][city] = {
            'routes': len(routes),
            'waypoints': city_data['waypoint_count'],
            'valid_routes': len(city_data['valid_routes']),
            'file': city_filename
        }
    
    # Save summary file
    summary_path = os.path.join(output_dir, 'routes_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_routes_summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved summary to {summary_path}")
    return all_routes_summary


def process_city_directory(city_path: str) -> List[Dict]:
    """
    Process a single city directory.
    
    Args:
        city_path: Path to city directory
        
    Returns:
        List of parsed routes
    """
    city_name = os.path.basename(city_path)
    logger.info(f"Processing city: {city_name}")
    
    # Check for raw directory
    raw_dir = os.path.join(city_path, 'raw')
    if not os.path.exists(raw_dir):
        logger.warning(f"No raw directory found for {city_name}")
        return []
    
    # Create extracted directory
    extracted_dir = os.path.join(city_path, 'extracted')
    os.makedirs(extracted_dir, exist_ok=True)
    
    all_routes = []
    
    # Look for ZIP files (files ending with _routes.rtz are actually ZIPs)
    for item in os.listdir(raw_dir):
        item_path = os.path.join(raw_dir, item)
        
        if os.path.isfile(item_path):
            # Check if it's a ZIP file (either .zip or _routes.rtz which is a ZIP)
            is_zip = False
            if item.endswith('_routes.rtz'):
                is_zip = True
            elif item.endswith('.zip'):
                is_zip = True
            elif is_zip_file(item_path):
                is_zip = True
            
            if is_zip:
                logger.info(f"Found ZIP archive: {item}")
                
                # Extract RTZ files from ZIP
                extracted_files = extract_zip_rtz_files(item_path, extracted_dir)
                
                # Parse each extracted RTZ file
                for rtz_file in extracted_files:
                    logger.info(f"Parsing RTZ file: {os.path.basename(rtz_file)}")
                    route_data = parse_rtz_file(rtz_file)
                    
                    if route_data:
                        route_data['source_city'] = city_name
                        route_data['source_zip'] = item
                        all_routes.append(route_data)
                        
                        logger.info(f"  ✓ {route_data['route_name']}: "
                                  f"{route_data['waypoint_count']} waypoints, "
                                  f"{route_data['total_distance_nm']} nm")
                    else:
                        logger.warning(f"  ✗ Failed to parse: {os.path.basename(rtz_file)}")
    
    # Also check for individual RTZ files in raw directory
    for item in os.listdir(raw_dir):
        item_path = os.path.join(raw_dir, item)
        
        if os.path.isfile(item_path) and item.endswith('.rtz') and not item.endswith('_routes.rtz'):
            # This is a standalone RTZ file (not a ZIP)
            logger.info(f"Found standalone RTZ file: {item}")
            route_data = parse_rtz_file(item_path)
            
            if route_data:
                route_data['source_city'] = city_name
                route_data['source_zip'] = None
                all_routes.append(route_data)
                
                logger.info(f"  ✓ {route_data['route_name']}: "
                          f"{route_data['waypoint_count']} waypoints, "
                          f"{route_data['total_distance_nm']} nm")
            else:
                logger.warning(f"  ✗ Failed to parse: {item}")
    
    return all_routes


def create_map_ready_format(routes: List[Dict]) -> Dict:
    """
    Create a map-ready format with proper waypoint connections.
    
    Args:
        routes: List of parsed routes
        
    Returns:
        Dictionary in map-ready format
    """
    map_data = {
        'type': 'FeatureCollection',
        'features': [],
        'routes': [],
        'waypoints': []
    }
    
    route_id = 0
    
    for route in routes:
        if not route['is_valid'] or len(route['waypoints']) < 2:
            continue
        
        route_id += 1
        
        # Create route line feature
        coordinates = [[wp['lon'], wp['lat']] for wp in route['waypoints']]
        
        route_feature = {
            'type': 'Feature',
            'properties': {
                'id': f"route_{route_id}",
                'name': route['route_name'],
                'origin': route['origin'],
                'destination': route['destination'],
                'distance_nm': route['total_distance_nm'],
                'waypoint_count': route['waypoint_count'],
                'city': route.get('source_city', 'Unknown'),
                'color': '#1E88E5',  # Default blue color
                'opacity': 0.8,
                'weight': 3
            },
            'geometry': {
                'type': 'LineString',
                'coordinates': coordinates
            }
        }
        
        map_data['features'].append(route_feature)
        
        # Add waypoints as separate features
        for i, wp in enumerate(route['waypoints']):
            wp_feature = {
                'type': 'Feature',
                'properties': {
                    'id': f"wp_{route_id}_{i}",
                    'name': wp['name'],
                    'route': route['route_name'],
                    'index': i,
                    'description': wp['description'],
                    'is_start': i == 0,
                    'is_end': i == len(route['waypoints']) - 1,
                    'marker-color': '#FF5722' if i == 0 else '#4CAF50' if i == len(route['waypoints']) - 1 else '#757575'
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [wp['lon'], wp['lat']]
                }
            }
            
            map_data['features'].append(wp_feature)
            map_data['waypoints'].append(wp_feature['properties'])
        
        # Add route metadata
        map_data['routes'].append({
            'id': f"route_{route_id}",
            'name': route['route_name'],
            'origin': route['origin'],
            'destination': route['destination'],
            'distance_nm': route['total_distance_nm'],
            'waypoints': len(route['waypoints']),
            'city': route.get('source_city', 'Unknown'),
            'file': route['file_name']
        })
    
    return map_data


def main():
    """Main function to fix ZIP RTZ files."""
    print("=" * 70)
    print("RTZ ZIP FIXER - Norwegian Coastal Routes Processor")
    print("=" * 70)
    
    # Get project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"Project root: {project_root}")
    
    # Define the routes directory
    routes_dir = os.path.join(project_root, 'backend', 'assets', 'routeinfo_routes')
    
    if not os.path.exists(routes_dir):
        print(f"❌ Routes directory not found: {routes_dir}")
        print("Please ensure you're running from the correct directory.")
        sys.exit(1)
    
    print(f"📁 Routes directory: {routes_dir}")
    
    # Process each city directory
    all_routes = {}
    total_stats = {
        'cities': 0,
        'routes': 0,
        'waypoints': 0,
        'valid_routes': 0
    }
    
    for city_dir in sorted(os.listdir(routes_dir)):
        city_path = os.path.join(routes_dir, city_dir)
        
        if os.path.isdir(city_path):
            print(f"\n{'='*50}")
            print(f"📍 Processing: {city_dir.title()}")
            print(f"{'='*50}")
            
            city_routes = process_city_directory(city_path)
            
            if city_routes:
                all_routes[city_dir.title()] = city_routes
                
                valid_count = len([r for r in city_routes if r['is_valid']])
                total_waypoints = sum(r['waypoint_count'] for r in city_routes)
                
                print(f"  ✅ Found: {len(city_routes)} routes ({valid_count} valid)")
                print(f"  📍 Waypoints: {total_waypoints}")
                
                total_stats['cities'] += 1
                total_stats['routes'] += len(city_routes)
                total_stats['waypoints'] += total_waypoints
                total_stats['valid_routes'] += valid_count
                
                # Show sample of routes
                for i, route in enumerate(city_routes[:3]):  # Show first 3
                    status = "✓" if route['is_valid'] else "✗"
                    print(f"    {status} {route['route_name']}: "
                          f"{route['origin']} → {route['destination']} "
                          f"({route['total_distance_nm']} nm)")
                
                if len(city_routes) > 3:
                    print(f"    ... and {len(city_routes) - 3} more routes")
            else:
                print(f"  ⚠️  No routes found in {city_dir}")
    
    # Save results
    if all_routes:
        print(f"\n{'='*70}")
        print("💾 SAVING RESULTS")
        print(f"{'='*70}")
        
        # Create output directory
        output_dir = os.path.join(project_root, 'backend', 'assets', 'routeinfo_routes', 'rtz_json')
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to JSON
        summary = save_routes_to_json(all_routes, output_dir)
        
        # Create map-ready format
        all_routes_list = []
        for city_routes in all_routes.values():
            all_routes_list.extend(city_routes)
        
        map_data = create_map_ready_format(all_routes_list)
        map_path = os.path.join(output_dir, 'routes_map.geojson')
        
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Map data saved to: {map_path}")
        
        # Summary
        print(f"\n{'='*70}")
        print("📊 PROCESSING SUMMARY")
        print(f"{'='*70}")
        print(f"🏙️  Cities processed: {total_stats['cities']}")
        print(f"🛣️  Total routes found: {total_stats['routes']}")
        print(f"✅ Valid routes: {total_stats['valid_routes']}")
        print(f"📍 Total waypoints: {total_stats['waypoints']}")
        print(f"💾 Output location: {output_dir}")
        
        print(f"\n🎉 Processing completed successfully!")
        print(f"\n📋 Next steps:")
        print(f"1. Check the generated files in: {output_dir}")
        print(f"2. The main map file is: routes_map.geojson")
        print(f"3. Each city has its own JSON file: <city>_routes.json")
        print(f"4. Import these files into your map application")
        
    else:
        print(f"\n❌ No routes were found in any city directory.")
        print(f"Check that the raw directories contain ZIP files with _routes.rtz extension.")
    
    print(f"\n📝 Log file created: rtz_fixer.log")


if __name__ == "__main__":
    main()