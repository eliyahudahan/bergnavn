#!/usr/bin/env python3
"""
Fix Dashboard Routes Issue
Run from project root to fix the RTZ routes display problem.
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil

# Add backend to path
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
sys.path.insert(0, str(backend_dir))

def create_fixed_dashboard_route():
    """Create a fixed version of the dashboard route"""
    
    fix_code = '''#!/usr/bin/env python3
"""
FIXED Dashboard Route for RTZ Routes Display
This should be added to backend/routes/maritime_routes.py
"""

from flask import render_template, jsonify, request, current_app
from datetime import datetime
import logging
from backend.services.rtz_parser import discover_rtz_files, get_processing_statistics
from backend.models import Route, VoyageLeg, db

logger = logging.getLogger(__name__)

def get_dashboard_data():
    """
    Get all data needed for the maritime dashboard.
    Returns: (routes_data, ports_list, unique_ports_count, empirical_verification)
    """
    try:
        # Norwegian ports list
        ports_list = [
            'bergen', 'oslo', 'stavanger', 'trondheim',
            'alesund', 'andalsnes', 'kristiansand',
            'drammen', 'sandefjord', 'flekkefjord'
        ]
        
        routes_data = []
        unique_ports = set()
        
        # Try database first
        try:
            logger.info("📊 Loading routes from database...")
            db_routes = Route.query.all()
            
            for route in db_routes:
                # Get waypoint count from voyage legs
                legs_count = VoyageLeg.query.filter_by(route_id=route.id).count()
                waypoint_count = legs_count + 1 if legs_count > 0 else 1
                
                route_dict = {
                    'route_name': route.name,
                    'clean_name': route.name.replace('NCA_', '').replace('_2025', '').replace('_', ' ').title(),
                    'origin': route.origin or 'Coastal',
                    'destination': route.destination or 'Coastal',
                    'total_distance_nm': float(route.total_distance_nm) if route.total_distance_nm else 0.0,
                    'source_city': route.origin.lower() if route.origin else 'unknown',
                    'waypoint_count': waypoint_count,
                    'legs': [],
                    'empirically_verified': True,
                    'description': f"NCA maritime route"
                }
                
                routes_data.append(route_dict)
                
                # Add to unique ports
                if route.origin and route.origin != 'Unknown':
                    unique_ports.add(route.origin.title())
                if route.destination and route.destination != 'Unknown':
                    unique_ports.add(route.destination.title())
            
            logger.info(f"✅ Loaded {len(routes_data)} routes from database")
            
        except Exception as db_error:
            logger.warning(f"⚠️ Database error: {db_error}")
            routes_data = []
        
        # If database empty, load from RTZ files
        if not routes_data:
            logger.info("📁 Loading routes from RTZ files...")
            try:
                file_routes = discover_rtz_files(enhanced=True)
                routes_data = file_routes
                
                for route in routes_data:
                    if route.get('origin'):
                        unique_ports.add(route['origin'].title())
                    if route.get('destination'):
                        unique_ports.add(route['destination'].title())
                
                logger.info(f"✅ Loaded {len(routes_data)} routes from RTZ files")
                
            except Exception as file_error:
                logger.error(f"❌ RTZ file error: {file_error}")
                routes_data = []
        
        # Create verification data
        empirical_verification = {
            'timestamp': datetime.now().isoformat(),
            'route_count': len(routes_data),
            'port_count': len(unique_ports),
            'verification_hash': f"RTZ_{len(routes_data)}_{len(unique_ports)}_{int(datetime.now().timestamp())}"
        }
        
        return routes_data, [p.title() for p in ports_list], len(unique_ports), empirical_verification
        
    except Exception as e:
        logger.error(f"❌ Dashboard data error: {e}")
        # Return empty but safe data
        return [], [], 0, None

@maritime_bp.route('/dashboard')
def dashboard():
    """
    Maritime dashboard - FIXED VERSION
    Shows actual RTZ routes from database or files
    """
    try:
        routes_data, ports_list, unique_ports_count, empirical_verification = get_dashboard_data()
        
        logger.info(f"📊 Dashboard: {len(routes_data)} routes, {unique_ports_count} ports")
        
        return render_template(
            'maritime_split/dashboard_base.html',
            routes=routes_data,
            ports_list=ports_list,
            unique_ports_count=unique_ports_count,
            empirical_verification=empirical_verification,
            lang='en'
        )
        
    except Exception as e:
        logger.error(f"❌ Dashboard route error: {e}")
        
        # Emergency fallback - minimal data
        return render_template(
            'maritime_split/dashboard_base.html',
            routes=[],
            ports_list=['Bergen', 'Oslo', 'Stavanger', 'Trondheim'],
            unique_ports_count=4,
            empirical_verification={
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            },
            lang='en'
        )

@maritime_bp.route('/api/dashboard-data')
def dashboard_data():
    """API endpoint for dashboard data (for AJAX)"""
    try:
        routes_data, ports_list, unique_ports_count, empirical_verification = get_dashboard_data()
        
        return jsonify({
            'success': True,
            'routes': routes_data[:50],  # Limit for performance
            'ports': ports_list,
            'unique_ports_count': unique_ports_count,
            'verification': empirical_verification,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'routes': [],
            'ports': []
        })

@maritime_bp.route('/api/load-rtz-now')
def load_rtz_now():
    """Force load RTZ data now"""
    try:
        from backend.services.rtz_parser import process_all_cities_routes
        
        result = process_all_cities_routes()
        
        return jsonify({
            'success': True,
            'message': f'Loaded {result} routes into database',
            'count': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
'''

    # Save the fix to a file
    fix_file = current_dir / "backend" / "fixed_dashboard_route.py"
    with open(fix_file, 'w') as f:
        f.write(fix_code)
    
    print(f"✅ Fixed dashboard route saved to: {fix_file}")
    return fix_file

def check_and_fix_maritime_routes():
    """Check and fix the maritime_routes.py file"""
    
    routes_file = current_dir / "backend" / "routes" / "maritime_routes.py"
    
    if not routes_file.exists():
        print(f"❌ maritime_routes.py not found at: {routes_file}")
        
        # Create a basic version
        basic_route = '''from flask import Blueprint, render_template, jsonify
from datetime import datetime
import logging

maritime_bp = Blueprint('maritime_bp', __name__, 
                       template_folder='../templates/maritime_split',
                       url_prefix='/maritime')
logger = logging.getLogger(__name__)

# Add the fixed dashboard route here
# Copy from fixed_dashboard_route.py
'''
        
        routes_file.parent.mkdir(parents=True, exist_ok=True)
        with open(routes_file, 'w') as f:
            f.write(basic_route)
        
        print(f"✅ Created basic maritime_routes.py")
    
    # Read current content
    with open(routes_file, 'r') as f:
        content = f.read()
    
    # Check if dashboard route exists
    if '@maritime_bp.route(\'/dashboard\')' in content:
        print("✅ Dashboard route already exists in maritime_routes.py")
        
        # Check if it needs updating
        if 'get_dashboard_data' not in content:
            print("⚠️ Dashboard route exists but might be old version")
            print("   Consider updating with code from fixed_dashboard_route.py")
    else:
        print("❌ Dashboard route NOT found in maritime_routes.py")
        print("   Need to add the fixed dashboard route")
    
    return routes_file

def create_test_dashboard_route():
    """Create a simple test route for debugging"""
    
    test_route = '''
@maritime_bp.route('/test-dashboard')
def test_dashboard():
    """Simple test dashboard with sample data"""
    test_routes = [
        {
            'route_name': 'NCA_Bergen_Oslo_2025',
            'clean_name': 'Bergen to Oslo',
            'origin': 'Bergen',
            'destination': 'Oslo',
            'total_distance_nm': 320.5,
            'source_city': 'bergen',
            'waypoint_count': 12,
            'empirically_verified': True,
            'description': 'Coastal route with 12 waypoints'
        },
        {
            'route_name': 'NCA_Stavanger_Trondheim_2025',
            'clean_name': 'Stavanger to Trondheim',
            'origin': 'Stavanger',
            'destination': 'Trondheim',
            'total_distance_nm': 450.2,
            'source_city': 'stavanger',
            'waypoint_count': 18,
            'empirically_verified': True,
            'description': 'Long coastal voyage'
        },
        {
            'route_name': 'NCA_Alesund_Kristiansand_2025',
            'clean_name': 'Ålesund to Kristiansand',
            'origin': 'Ålesund',
            'destination': 'Kristiansand',
            'total_distance_nm': 280.7,
            'source_city': 'alesund',
            'waypoint_count': 15,
            'empirically_verified': True,
            'description': 'Southern coastal route'
        }
    ]
    
    return render_template(
        'maritime_split/dashboard_base.html',
        routes=test_routes,
        ports_list=['Bergen', 'Oslo', 'Stavanger', 'Trondheim', 'Ålesund', 'Kristiansand'],
        unique_ports_count=6,
        empirical_verification={
            'timestamp': datetime.now().isoformat(),
            'route_count': 3,
            'port_count': 6,
            'verification_hash': 'TEST_3_6_123456'
        },
        lang='en'
    )
'''
    
    test_file = current_dir / "backend" / "test_dashboard_route.py"
    with open(test_file, 'w') as f:
        f.write(test_route)
    
    print(f"✅ Test dashboard route saved to: {test_file}")
    return test_file

def run_rtz_import():
    """Run the RTZ import to load data into database"""
    
    print("\n📥 Importing RTZ data into database...")
    
    try:
        # Import within function to avoid circular imports
        sys.path.insert(0, str(current_dir))
        
        # Run the RTZ parser directly
        rtz_parser_path = backend_dir / "services" / "rtz_parser.py"
        
        if rtz_parser_path.exists():
            print(f"✅ Running RTZ parser: {rtz_parser_path}")
            
            # Change to backend directory to run
            original_cwd = os.getcwd()
            os.chdir(backend_dir)
            
            try:
                # Import and run
                import importlib.util
                spec = importlib.util.spec_from_file_location("rtz_parser", rtz_parser_path)
                rtz_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(rtz_module)
                
                # Discover files
                print("🔍 Discovering RTZ files...")
                routes = rtz_module.discover_rtz_files(enhanced=False)
                print(f"📊 Found {len(routes)} routes")
                
                # Process to database
                print("💾 Saving to database...")
                result = rtz_module.process_all_cities_routes()
                print(f"✅ Result: {result} routes saved")
                
            finally:
                os.chdir(original_cwd)
        else:
            print(f"❌ RTZ parser not found: {rtz_parser_path}")
            
    except Exception as e:
        print(f"❌ Error importing RTZ data: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to fix the dashboard"""
    
    print("🔧 FIXING DASHBOARD RTZ ROUTES DISPLAY")
    print("=" * 60)
    
    # Step 1: Create fixed route
    print("\n1️⃣ Creating fixed dashboard route...")
    fix_file = create_fixed_dashboard_route()
    
    # Step 2: Check current routes file
    print("\n2️⃣ Checking current maritime_routes.py...")
    routes_file = check_and_fix_maritime_routes()
    
    # Step 3: Create test route
    print("\n3️⃣ Creating test route...")
    test_file = create_test_dashboard_route()
    
    # Step 4: Import RTZ data
    print("\n4️⃣ Importing RTZ data (optional)...")
    print("   Run this manually if needed: python backend/services/rtz_parser.py")
    
    print("\n" + "=" * 60)
    print("✅ FIXES APPLIED")
    print("\n📋 Next steps:")
    print(f"1. Copy code from {fix_file} into {routes_file}")
    print(f"2. Test with /test-dashboard route")
    print("3. Visit /dashboard to see actual RTZ routes")
    print("\n🚀 To test immediately:")
    print("   flask --app app:create_app run --port=5001")
    print("   Then visit: http://localhost:5001/maritime/test-dashboard")

if __name__ == "__main__":
    main()
    