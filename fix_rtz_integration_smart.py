#!/usr/bin/env python3
"""
RTZ Integration Fixer - Safely integrates processed RTZ routes with existing system
This script updates only what's needed without breaking working code.
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if we're in the correct directory and environment is ready."""
    current_dir = Path(__file__).parent.absolute()
    logger.info(f"Current directory: {current_dir}")
    
    # Check for expected directories
    required_dirs = [
        'backend',
        'backend/routes'
    ]
    
    for dir_path in required_dirs:
        full_path = current_dir / dir_path
        if not full_path.exists():
            logger.error(f"❌ Missing directory: {dir_path}")
            return False
    
    # Check for processed routes
    processed_file = current_dir / 'backend' / 'assets' / 'route_data' / 'processed' / 'all_routes_data.json'
    if not processed_file.exists():
        logger.error(f"❌ Processed routes file not found: {processed_file}")
        return False
    
    logger.info("✅ Environment check passed")
    return True


def create_rtz_loader():
    """Create the RTZ loader utility file."""
    loader_content = '''"""
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
'''
    
    # Create backend/utils directory if it doesn't exist
    utils_dir = Path(__file__).parent / 'backend' / 'utils'
    utils_dir.mkdir(exist_ok=True, parents=True)
    
    # Create __init__.py if it doesn't exist
    init_file = utils_dir / '__init__.py'
    if not init_file.exists():
        init_file.write_text('# Utils package\n')
        logger.info(f"✅ Created {init_file}")
    
    # Write the loader file
    loader_file = utils_dir / 'rtz_loader.py'
    loader_file.write_text(loader_content, encoding='utf-8')
    
    logger.info(f"✅ Created RTZ loader utility: {loader_file}")
    return loader_file


def backup_maritime_file():
    """Backup the existing maritime.py file before making changes."""
    # Check which maritime file exists
    current_dir = Path(__file__).parent.absolute()
    
    # Check for maritime_routes.py first (your actual file)
    maritime_file = current_dir / 'backend' / 'routes' / 'maritime_routes.py'
    
    if not maritime_file.exists():
        # Try maritime.py as fallback
        maritime_file = current_dir / 'backend' / 'routes' / 'maritime.py'
        if not maritime_file.exists():
            logger.error(f"❌ Maritime file not found in: {maritime_file.parent}")
            return None
    
    # Create backup
    backup_file = maritime_file.with_suffix('.py.backup')
    shutil.copy2(maritime_file, backup_file)
    
    logger.info(f"✅ Backup created: {backup_file}")
    return backup_file, maritime_file


def patch_get_rtz_routes_function(content: str) -> str:
    """Patch the get_rtz_routes function to use the new loader."""
    
    # The new function content
    new_function = '''@maritime_bp.route('/api/rtz/routes')
def get_rtz_routes():
    """Get processed RTZ routes from the new JSON files"""
    try:
        logger.info("Loading RTZ routes from processed files...")
        
        # Load processed routes
        routes = load_processed_routes()
        
        # Calculate totals
        total_waypoints = calculate_total_waypoints(routes)
        total_distance = calculate_total_distance(routes)
        ports_list = get_ports_list(routes)
        
        # Transform for frontend
        routes_for_frontend = []
        for route in routes:
            routes_for_frontend.append({
                'id': route.get('route_id', f"route_{route.get('route_index', 0)}"),
                'name': route.get('clean_name', route.get('route_name', 'Unknown Route')),
                'route_name': route.get('route_name', 'Unknown'),
                'origin': route.get('origin', 'Unknown'),
                'destination': route.get('destination', 'Unknown'),
                'total_distance_nm': route.get('total_distance_nm', 0),
                'waypoint_count': route.get('waypoint_count', 0),
                'source_city': route.get('source_city', 'Unknown'),
                'waypoints': [],  # Will be loaded separately if needed
                'visual_properties': route.get('visual_properties', {
                    'color': '#3498db',
                    'weight': 3,
                    'opacity': 0.8
                })
            })
        
        response = {
            'routes': routes_for_frontend,
            'total': len(routes),
            'total_waypoints': total_waypoints,
            'total_distance_nm': round(total_distance, 2),
            'ports': ports_list,
            'ports_count': len(ports_list),
            'timestamp': datetime.now().isoformat(),
            'source': 'processed_rtz_files',
            'status': 'success'
        }
        
        logger.info(f"Returning {len(routes)} routes with {total_waypoints} waypoints")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error loading RTZ routes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Fallback to empty response
        return jsonify({
            'routes': [],
            'total': 0,
            'total_waypoints': 0,
            'total_distance_nm': 0,
            'ports': [],
            'ports_count': 0,
            'timestamp': datetime.now().isoformat(),
            'source': 'error',
            'status': 'error',
            'error': str(e)
        }), 500'''
    
    # Check if the function already exists
    if 'def get_rtz_routes():' in content:
        # Find and replace the existing function
        lines = content.split('\n')
        new_lines = []
        in_function = False
        skip_until_deindent = False
        current_indent = 0
        
        for line in lines:
            if 'def get_rtz_routes():' in line:
                # Start of the function we want to replace
                in_function = True
                current_indent = len(line) - len(line.lstrip())
                new_lines.append(new_function)
                skip_until_deindent = True
                continue
            
            if skip_until_deindent:
                # Check if we're out of the function
                if line.strip() and len(line) - len(line.lstrip()) <= current_indent:
                    skip_until_deindent = False
                    new_lines.append(line)
                # Otherwise skip this line (it's part of the old function)
                continue
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    else:
        # Function doesn't exist, add it at the end before the last line
        lines = content.strip().split('\n')
        
        # Find a good place to add it (before the last function or at the end)
        insert_point = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('def ') or lines[i].strip().startswith('@'):
                insert_point = i + 1
                break
        
        lines.insert(insert_point, '\n' + new_function)
        return '\n'.join(lines)


def patch_maritime_dashboard_function(content: str) -> str:
    """Patch the maritime_dashboard function to use the new loader."""
    
    # Find the function
    if 'def maritime_dashboard():' not in content:
        return content  # Function doesn't exist
    
    lines = content.split('\n')
    new_lines = []
    in_function = False
    function_indent = 0
    skip_until_deindent = False
    
    for i, line in enumerate(lines):
        if 'def maritime_dashboard():' in line:
            in_function = True
            function_indent = len(line) - len(line.lstrip())
            new_lines.append(line)
            continue
        
        if in_function and not skip_until_deindent:
            # Check if we're at the right place to insert our code
            if 'try:' in line and len(line) - len(line.lstrip()) == function_indent + 4:
                # Found the try block, now look for where to insert
                new_lines.append(line)
                # Insert after the try: line
                next_line_idx = i + 1
                while next_line_idx < len(lines) and lines[next_line_idx].strip().startswith('#'):
                    new_lines.append(lines[next_line_idx])
                    next_line_idx += 1
                
                # Insert our new loading code
                indent = ' ' * (function_indent + 8)
                new_lines.append(f'{indent}# Load processed RTZ routes')
                new_lines.append(f'{indent}routes = load_processed_routes()')
                new_lines.append(f'{indent}ports_list = get_ports_list(routes)')
                new_lines.append(f'{indent}total_waypoints = calculate_total_waypoints(routes)')
                new_lines.append(f'{indent}total_routes = len(routes)')
                new_lines.append(f'{indent}total_distance = calculate_total_distance(routes)')
                new_lines.append('')
                
                # Skip the old loading code
                skip_until_deindent = True
                continue
        
        if skip_until_deindent:
            # Skip lines until we find the context preparation
            if 'context = {' in line and len(line) - len(line.lstrip()) == function_indent + 8:
                skip_until_deindent = False
                # Insert before context preparation
                indent = ' ' * (function_indent + 8)
                new_lines.append(f'{indent}# Prepare route data for template')
                new_lines.append(f'{indent}routes_data = []')
                new_lines.append(f'{indent}for route in routes:')
                new_lines.append(f'{indent}    routes_data.append({{')
                new_lines.append(f'{indent}        \'route_name\': route.get(\'route_name\', \'Unknown\'),')
                new_lines.append(f'{indent}        \'clean_name\': route.get(\'clean_name\', route.get(\'route_name\', \'Unknown\')),')
                new_lines.append(f'{indent}        \'origin\': route.get(\'origin\', \'Unknown\'),')
                new_lines.append(f'{indent}        \'destination\': route.get(\'destination\', \'Unknown\'),')
                new_lines.append(f'{indent}        \'total_distance_nm\': route.get(\'total_distance_nm\', 0),')
                new_lines.append(f'{indent}        \'source_city\': route.get(\'source_city\', \'Unknown\'),')
                new_lines.append(f'{indent}        \'waypoint_count\': route.get(\'waypoint_count\', 0),')
                new_lines.append(f'{indent}        \'route_id\': route.get(\'route_id\', f"route_{{route.get(\'route_index\', 0)}}"),')
                new_lines.append(f'{indent}        \'visual_properties\': route.get(\'visual_properties\', {{}})')
                new_lines.append(f'{indent}    }})')
                new_lines.append('')
                new_lines.append(line)
            continue
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)


def patch_maritime_file():
    """
    Patch the maritime.py or maritime_routes.py file to use the new RTZ loader.
    """
    # Find which file to patch
    current_dir = Path(__file__).parent.absolute()
    
    # Try maritime_routes.py first
    maritime_file = current_dir / 'backend' / 'routes' / 'maritime_routes.py'
    if not maritime_file.exists():
        # Try maritime.py
        maritime_file = current_dir / 'backend' / 'routes' / 'maritime.py'
        if not maritime_file.exists():
            logger.error("❌ Could not find maritime routes file")
            return False
    
    logger.info(f"🔄 Patching file: {maritime_file}")
    
    # Read the current file
    with open(maritime_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import if not already present
    if 'from backend.utils.rtz_loader import' not in content:
        # Find where to add import
        lines = content.split('\n')
        import_added = False
        
        for i, line in enumerate(lines):
            if 'import' in line and ('jsonify' in line or 'Blueprint' in line):
                lines.insert(i + 1, 'from backend.utils.rtz_loader import load_processed_routes, get_ports_list, calculate_total_waypoints, calculate_total_distance')
                import_added = True
                break
        
        if not import_added:
            # Add at the beginning
            lines.insert(0, 'from backend.utils.rtz_loader import load_processed_routes, get_ports_list, calculate_total_waypoints, calculate_total_distance')
        
        content = '\n'.join(lines)
    
    # Patch the get_rtz_routes function
    content = patch_get_rtz_routes_function(content)
    
    # Patch the maritime_dashboard function
    content = patch_maritime_dashboard_function(content)
    
    # Write the updated file
    with open(maritime_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✅ Successfully patched {maritime_file.name}")
    return True


def test_integration():
    """Test that the integration works."""
    try:
        # Add the backend directory to Python path
        backend_dir = Path(__file__).parent / 'backend'
        sys.path.insert(0, str(backend_dir.parent))
        
        # Try to import the loader
        from backend.utils.rtz_loader import load_processed_routes
        
        # Try to load routes
        routes = load_processed_routes()
        
        logger.info(f"✅ Integration test passed: loaded {len(routes)} routes")
        
        # Show some stats
        if routes:
            ports = set(r['source_city'] for r in routes if r['source_city'])
            total_waypoints = sum(r['waypoint_count'] for r in routes)
            total_distance = sum(r['total_distance_nm'] for r in routes)
            
            logger.info(f"   - Ports: {len(ports)}")
            logger.info(f"   - Total waypoints: {total_waypoints}")
            logger.info(f"   - Total distance: {total_distance:.1f} NM")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def create_test_script():
    """Create a test script to verify the integration."""
    test_script = '''#!/usr/bin/env python3
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
    print(f"\\n📋 Sample routes (first 3):")
    for i, route in enumerate(routes[:3]):
        print(f"   {i+1}. {route.get('clean_name', 'Unnamed')}")
        print(f"      From: {route.get('origin', 'Unknown')} → To: {route.get('destination', 'Unknown')}")
        print(f"      Distance: {route.get('total_distance_nm', 0):.1f} NM, Waypoints: {route.get('waypoint_count', 0)}")
        print(f"      Port: {route.get('source_city', 'Unknown')}")
    
    print("\\n🎉 Integration test passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)
'''
    
    test_file = Path(__file__).parent / 'test_rtz_integration.py'
    test_file.write_text(test_script, encoding='utf-8')
    
    # Make it executable
    os.chmod(test_file, 0o755)
    
    logger.info(f"✅ Created test script: {test_file}")
    return test_file


def main():
    """Main function to run the fixer."""
    print("=" * 70)
    print("RTZ INTEGRATION FIXER")
    print("=" * 70)
    print("This script will safely integrate processed RTZ routes with your system")
    print("without breaking existing working code.")
    print()
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed. Please run from project root.")
        sys.exit(1)
    
    # Ask for confirmation
    response = input("Continue with the integration? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Operation cancelled.")
        sys.exit(0)
    
    print()
    print("🔄 Starting integration...")
    print()
    
    # Create RTZ loader
    loader_file = create_rtz_loader()
    if not loader_file or not loader_file.exists():
        print("❌ Failed to create RTZ loader")
        sys.exit(1)
    
    # Backup original file
    backup_info = backup_maritime_file()
    if not backup_info:
        print("❌ Failed to backup maritime file")
        sys.exit(1)
    
    backup_file, maritime_file = backup_info
    
    # Patch maritime.py
    if not patch_maritime_file():
        print("❌ Failed to patch maritime file")
        print("⚠️  The backup file has been created")
        response = input("Restore backup? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            shutil.copy2(backup_file, maritime_file)
            print("✅ Backup restored")
        sys.exit(1)
    
    # Test integration
    if not test_integration():
        print("❌ Integration test failed")
        print("⚠️  The backup file has been created: backend/routes/maritime_routes.py.backup")
        response = input("Restore backup? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            shutil.copy2(backup_file, maritime_file)
            print("✅ Backup restored")
        sys.exit(1)
    
    # Create test script
    test_script = create_test_script()
    
    print()
    print("=" * 70)
    print("🎉 INTEGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("📋 What was done:")
    print("   1. ✅ Created backend/utils/rtz_loader.py")
    print("   2. ✅ Backed up maritime_routes.py to maritime_routes.py.backup")
    print("   3. ✅ Patched maritime_routes.py to use processed routes")
    print("   4. ✅ Tested the integration")
    print("   5. ✅ Created test script")
    print()
    print("🚀 Next steps:")
    print("   1. Run the test script:")
    print(f"      python {test_script.name}")
    print("   2. Restart your Flask server:")
    print("      pkill -f 'python app.py'")
    print("      python app.py")
    print("   3. Visit: http://localhost:5000/maritime/dashboard")
    print()
    print("📝 Note: Backup file available at backend/routes/maritime_routes.py.backup")
    print("      If anything goes wrong, you can restore it.")


if __name__ == "__main__":
    main()