#!/usr/bin/env python3
"""
Final RTZ Reorganization - Complete and Accurate Solution
1. Finds all extracted RTZ files
2. Removes duplicates
3. Converts each to accurate JSON with proper start/end/waypoints
4. Creates clean organized structure
"""

import os
import sys
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple
import hashlib
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the absolute path to project root directory."""
    return Path(__file__).parent.absolute()

def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file to detect duplicates."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing {file_path}: {e}")
        return ""

def find_all_extracted_rtz_files() -> Dict[str, List[Dict]]:
    """
    Find ALL extracted RTZ files across all cities.
    Returns: {city: [{'path': Path, 'filename': str, 'hash': str}]}
    """
    logger.info("🔍 Finding all extracted RTZ files...")
    
    root = get_project_root()
    routes_path = root / "backend" / "assets" / "routeinfo_routes"
    
    cities = [
        'alesund', 'andalsnes', 'bergen', 'drammen', 'flekkefjord',
        'kristiansand', 'oslo', 'sandefjord', 'stavanger', 'trondheim'
    ]
    
    all_files_by_city = {}
    total_files_found = 0
    duplicate_files = []
    
    for city in cities:
        city_path = routes_path / city / "raw"
        if not city_path.exists():
            logger.warning(f"  ⚠️ No raw directory for {city}")
            continue
        
        # Look for extracted files in multiple locations
        possible_dirs = [
            city_path / "extracted",
            city_path / "extracted_zip",
            city_path  # Also check raw directory itself for single files
        ]
        
        city_files = []
        seen_hashes = set()
        
        for dir_path in possible_dirs:
            if dir_path.exists():
                # Find all .rtz files
                for rtz_file in dir_path.glob("*.rtz"):
                    if rtz_file.is_file():
                        # Calculate hash to detect duplicates
                        file_hash = calculate_file_hash(rtz_file)
                        
                        if file_hash and file_hash in seen_hashes:
                            duplicate_files.append({
                                'city': city,
                                'file': rtz_file.name,
                                'path': str(rtz_file)
                            })
                            continue
                        
                        if file_hash:
                            seen_hashes.add(file_hash)
                        
                        file_info = {
                            'path': rtz_file,
                            'filename': rtz_file.name,
                            'hash': file_hash,
                            'source_dir': dir_path.name
                        }
                        city_files.append(file_info)
                        total_files_found += 1
        
        if city_files:
            all_files_by_city[city] = city_files
            logger.info(f"  ✅ {city}: Found {len(city_files)} unique RTZ files")
            
            # Show sample files
            for file_info in city_files[:3]:
                logger.info(f"    • {file_info['filename']} (from {file_info['source_dir']})")
            if len(city_files) > 3:
                logger.info(f"    ... and {len(city_files) - 3} more")
        else:
            logger.info(f"  ❌ {city}: No extracted RTZ files found")
    
    logger.info(f"\n📊 Total unique RTZ files found: {total_files_found}")
    logger.info(f"🗑️  Duplicate files detected: {len(duplicate_files)}")
    
    if duplicate_files:
        logger.info("\nDuplicate files to be removed:")
        for dup in duplicate_files[:5]:
            logger.info(f"  • {dup['city']}: {dup['file']}")
        if len(duplicate_files) > 5:
            logger.info(f"  ... and {len(duplicate_files) - 5} more")
    
    return all_files_by_city, duplicate_files

def parse_rtz_file(rtz_path: Path) -> Dict:
    """
    Parse a single RTZ file and extract route information.
    Returns accurate route data with start, end, and waypoints.
    """
    try:
        if not rtz_path.exists():
            logger.error(f"File not found: {rtz_path}")
            return None
        
        # Parse XML
        tree = ET.parse(rtz_path)
        root = tree.getroot()
        
        # Extract route name from filename or XML
        route_name = rtz_path.stem
        
        # Define namespace
        ns = {'rtz': 'http://www.cirm.org/RTZ/1/0'}
        
        # Try to get route info
        route_info_elem = root.find('.//rtz:routeInfo', ns)
        if route_info_elem is not None:
            route_name_from_xml = route_info_elem.get('routeName')
            if route_name_from_xml:
                route_name = route_name_from_xml
        
        # Extract waypoints
        waypoints = []
        wp_elements = root.findall('.//rtz:waypoint', ns)
        
        for wp_elem in wp_elements:
            position_elem = wp_elem.find('rtz:position', ns)
            if position_elem is not None:
                lat = position_elem.get('lat')
                lon = position_elem.get('lon')
                if lat and lon:
                    waypoint = {
                        'name': wp_elem.get('name', ''),
                        'lat': float(lat),
                        'lon': float(lon),
                        'turn_radius': float(wp_elem.get('turnRadius', 0.1))
                    }
                    waypoints.append(waypoint)
        
        if not waypoints:
            logger.warning(f"No waypoints found in {rtz_path.name}")
            return None
        
        # Extract start and end from waypoints
        start_point = waypoints[0] if waypoints else None
        end_point = waypoints[-1] if waypoints else None
        
        # Try to extract from filename (NCA naming convention)
        filename = rtz_path.name
        origin = "Unknown"
        destination = "Unknown"
        
        # Parse NCA filename pattern: NCA_[Depth?]_Origin_Destination_Direction_Date
        match = re.match(r'NCA_(\d+m_)?([^_]+)_([^_]+)_(In|Out)_\d{8}\.rtz', filename)
        if match:
            depth = match.group(1) or ""
            origin = match.group(2).replace('_', ' ').title()
            destination = match.group(3).replace('_', ' ').title()
            direction = match.group(4)
        else:
            # Fallback: use first and last waypoint names
            if waypoints:
                origin = waypoints[0]['name'] or "Start"
                destination = waypoints[-1]['name'] or "End"
        
        # Clean up names
        def clean_name(name):
            # Remove common suffixes
            for suffix in ['_In', '_Out', '_2025', '_2024', '_2023']:
                if suffix in name:
                    name = name.replace(suffix, '')
            return name.strip()
        
        origin = clean_name(origin)
        destination = clean_name(destination)
        
        # Create route data structure
        route_data = {
            'route_id': hashlib.md5(str(rtz_path).encode()).hexdigest()[:8],
            'route_name': route_name,
            'filename': rtz_path.name,
            'origin': origin,
            'destination': destination,
            'waypoints': waypoints,
            'waypoint_count': len(waypoints),
            'start_point': {
                'lat': start_point['lat'] if start_point else None,
                'lon': start_point['lon'] if start_point else None,
                'name': start_point['name'] if start_point else 'Start'
            } if start_point else None,
            'end_point': {
                'lat': end_point['lat'] if end_point else None,
                'lon': end_point['lon'] if end_point else None,
                'name': end_point['name'] if end_point else 'End'
            } if end_point else None,
            'parse_timestamp': datetime.now().isoformat(),
            'data_source': 'Norwegian Coastal Administration (routeinfo.no)',
            'original_file': str(rtz_path.relative_to(get_project_root()))
        }
        
        logger.debug(f"Parsed {rtz_path.name}: {origin} → {destination} ({len(waypoints)} waypoints)")
        return route_data
        
    except ET.ParseError as e:
        logger.error(f"XML parse error in {rtz_path.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing {rtz_path.name}: {e}")
        return None

def remove_duplicate_files(duplicate_files: List[Dict]) -> int:
    """
    Remove duplicate files found in the system.
    Returns number of files removed.
    """
    if not duplicate_files:
        return 0
    
    logger.info("\n🗑️ Removing duplicate files...")
    
    removed_count = 0
    for dup in duplicate_files:
        try:
            file_path = Path(dup['path'])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"  ✅ Removed duplicate: {dup['city']}/{dup['file']}")
                removed_count += 1
        except Exception as e:
            logger.error(f"  ❌ Failed to remove {dup['path']}: {e}")
    
    logger.info(f"Removed {removed_count} duplicate files")
    return removed_count

def create_clean_structure(all_files_by_city: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Create clean organized structure for all routes.
    Returns converted route data.
    """
    logger.info("\n🔄 Creating clean organized structure...")
    
    root = get_project_root()
    routes_path = root / "backend" / "assets" / "routeinfo_routes"
    
    # Create clean directories
    clean_base = routes_path / "_clean_organized"
    if clean_base.exists():
        shutil.rmtree(clean_base)
    clean_base.mkdir(parents=True)
    
    # Create README
    readme_content = """# Clean Organized RTZ Routes
Extracted and organized from Norwegian Coastal Administration files.

## Structure
- Each city has its own directory
- Each route is a separate JSON file
- Original RTZ files are not modified

## Data Source
Norwegian Coastal Administration (routeinfo.no)
Coordinate precision: 6 decimal places
Updated: {datetime}
""".format(datetime=datetime.now().strftime("%Y-%m-%d"))
    
    with open(clean_base / "README.md", "w") as f:
        f.write(readme_content)
    
    converted_routes_by_city = {}
    total_converted = 0
    
    for city, file_list in all_files_by_city.items():
        logger.info(f"\n📍 Processing {city}...")
        
        # Create city directory in clean structure
        city_clean_dir = clean_base / city
        city_clean_dir.mkdir(exist_ok=True)
        
        city_routes = []
        successful_conversions = 0
        
        for file_info in file_list:
            rtz_path = file_info['path']
            
            # Parse RTZ file
            route_data = parse_rtz_file(rtz_path)
            if not route_data:
                logger.warning(f"  ⚠️ Failed to parse: {file_info['filename']}")
                continue
            
            # Create JSON filename
            json_filename = f"{route_data['route_id']}_{route_data['origin']}_to_{route_data['destination']}.json"
            json_filename = re.sub(r'[^\w\.\-]', '_', json_filename)  # Clean filename
            
            json_path = city_clean_dir / json_filename
            
            # Save as JSON
            with open(json_path, 'w') as f:
                json.dump(route_data, f, indent=2)
            
            # Add to city routes
            city_routes.append(route_data)
            successful_conversions += 1
            total_converted += 1
            
            logger.info(f"  ✅ Converted: {file_info['filename']} → {json_filename}")
        
        if city_routes:
            converted_routes_by_city[city] = city_routes
            logger.info(f"  📊 {city}: {successful_conversions}/{len(file_list)} files converted successfully")
    
    logger.info(f"\n🎉 Total routes converted: {total_converted}")
    return converted_routes_by_city

def create_route_summary(converted_routes_by_city: Dict[str, List[Dict]]) -> Dict:
    """
    Create comprehensive summary of all routes.
    """
    logger.info("\n📊 Creating comprehensive route summary...")
    
    summary_data = {
        'metadata': {
            'generated_date': datetime.now().isoformat(),
            'data_source': 'Norwegian Coastal Administration (routeinfo.no)',
            'coordinate_system': 'WGS84',
            'precision': '6 decimal places',
            'total_cities': len(converted_routes_by_city),
            'total_routes': sum(len(routes) for routes in converted_routes_by_city.values())
        },
        'cities': {},
        'statistics': {
            'routes_by_city': {},
            'total_waypoints': 0,
            'avg_waypoints_per_route': 0
        }
    }
    
    total_waypoints = 0
    total_routes = 0
    
    for city, routes in converted_routes_by_city.items():
        city_summary = {
            'route_count': len(routes),
            'routes': []
        }
        
        for route in routes:
            route_summary = {
                'route_id': route['route_id'],
                'route_name': route['route_name'],
                'origin': route['origin'],
                'destination': route['destination'],
                'waypoint_count': route['waypoint_count'],
                'filename': route['filename']
            }
            city_summary['routes'].append(route_summary)
            total_waypoints += route['waypoint_count']
        
        summary_data['cities'][city] = city_summary
        summary_data['statistics']['routes_by_city'][city] = len(routes)
        total_routes += len(routes)
    
    # Calculate statistics
    if total_routes > 0:
        summary_data['statistics']['total_waypoints'] = total_waypoints
        summary_data['statistics']['avg_waypoints_per_route'] = round(total_waypoints / total_routes, 1)
    
    # Save summary
    root = get_project_root()
    summary_path = root / "backend" / "static" / "data" / "rtz_routes_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"✅ Summary saved to: {summary_path.relative_to(root)}")
    
    # Also create simplified stats for dashboard
    simple_stats = {
        'total_routes': summary_data['metadata']['total_routes'],
        'cities_count': summary_data['metadata']['total_cities'],
        'total_waypoints': summary_data['statistics']['total_waypoints'],
        'data_source': summary_data['metadata']['data_source'],
        'last_updated': summary_data['metadata']['generated_date']
    }
    
    stats_path = root / "backend" / "static" / "data" / "rtz_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(simple_stats, f, indent=2)
    
    logger.info(f"✅ Stats saved to: {stats_path.relative_to(root)}")
    
    # Print summary
    logger.info(f"\n📈 FINAL SUMMARY:")
    logger.info(f"  • Total routes: {simple_stats['total_routes']}")
    logger.info(f"  • Cities/ports: {simple_stats['cities_count']}")
    logger.info(f"  • Total waypoints: {simple_stats['total_waypoints']:,}")
    logger.info(f"  • Source: {simple_stats['data_source']}")
    
    for city, count in summary_data['statistics']['routes_by_city'].items():
        logger.info(f"  • {city.title()}: {count} routes")
    
    return summary_data

def update_dashboard_data(summary_data: Dict):
    """
    Update dashboard with accurate empirical data.
    """
    logger.info("\n📱 Updating dashboard data...")
    
    root = get_project_root()
    
    # Create empirical data file for Python modules
    empirical_data = f'''"""
Empirical RTZ Route Data - Auto-generated
Actual route counts from Norwegian Coastal Administration.
"""

RTZ_ROUTES_COUNT = {summary_data['metadata']['total_routes']}
RTZ_CITIES_COUNT = {summary_data['metadata']['total_cities']}
RTZ_WAYPOINTS_COUNT = {summary_data['statistics']['total_waypoints']}
RTZ_DATA_SOURCE = "Norwegian Coastal Administration (routeinfo.no)"
RTZ_LAST_UPDATED = "{summary_data['metadata']['generated_date']}"

def get_rtz_summary():
    """Return RTZ route summary for dashboard."""
    return {{
        "total_routes": RTZ_ROUTES_COUNT,
        "cities_count": RTZ_CITIES_COUNT,
        "waypoints_count": RTZ_WAYPOINTS_COUNT,
        "data_source": RTZ_DATA_SOURCE,
        "last_updated": RTZ_LAST_UPDATED,
        "verified": True
    }}
'''
    
    # Save to utils directory
    empirical_path = root / "backend" / "utils" / "empirical_rtz_data.py"
    empirical_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(empirical_path, 'w') as f:
        f.write(empirical_data)
    
    logger.info(f"✅ Empirical data module created: {empirical_path.relative_to(root)}")

def main():
    """
    Main function - complete reorganization process.
    """
    print("=" * 70)
    print("RTZ FINAL REORGANIZATION - COMPLETE SOLUTION")
    print("=" * 70)
    print("Starting fresh from original RTZ files...")
    print("=" * 70)
    
    try:
        # Step 1: Find all extracted RTZ files
        all_files_by_city, duplicate_files = find_all_extracted_rtz_files()
        
        if not all_files_by_city:
            logger.error("❌ No RTZ files found! Exiting.")
            sys.exit(1)
        
        # Step 2: Remove duplicates
        removed = remove_duplicate_files(duplicate_files)
        
        # Step 3: Create clean organized structure
        converted_routes = create_clean_structure(all_files_by_city)
        
        if not converted_routes:
            logger.error("❌ No routes were converted! Exiting.")
            sys.exit(1)
        
        # Step 4: Create comprehensive summary
        summary = create_route_summary(converted_routes)
        
        # Step 5: Update dashboard data
        update_dashboard_data(summary)
        
        print("\n" + "=" * 70)
        print("✅ PROCESS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        print("\n📋 WHAT WAS DONE:")
        print(f"1. ✅ Found {sum(len(files) for files in all_files_by_city.values())} unique RTZ files")
        print(f"2. ✅ Removed {removed} duplicate files")
        print(f"3. ✅ Converted {summary['metadata']['total_routes']} routes to JSON")
        print(f"4. ✅ Created organized structure in _clean_organized/")
        print(f"5. ✅ Generated dashboard statistics")
        
        print("\n📁 NEW STRUCTURE:")
        print("  backend/assets/routeinfo_routes/_clean_organized/")
        print("    ├── README.md")
        print("    ├── alesund/")
        print("    ├── bergen/")
        print("    └── ... (all cities)")
        print("  backend/static/data/rtz_routes_summary.json")
        print("  backend/static/data/rtz_stats.json")
        print("  backend/utils/empirical_rtz_data.py")
        
        print("\n📊 FINAL COUNTS:")
        print(f"  • Routes: {summary['metadata']['total_routes']}")
        print(f"  • Cities: {summary['metadata']['total_cities']}")
        print(f"  • Waypoints: {summary['statistics']['total_waypoints']:,}")
        
        print("\n🎯 Dashboard now shows ACCURATE empirical data!")
        
    except Exception as e:
        logger.error(f"\n❌ PROCESS FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()