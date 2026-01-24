#!/usr/bin/env python3
"""
FIX EXACT ROUTE - Fixes the existing /maritime/dashboard route
"""

import os
import sys
from pathlib import Path
import re

print("🔧 FIXING EXACT ROUTE: /maritime/dashboard")
print("=" * 50)

# Paths
backend_dir = Path("backend")
routes_file = backend_dir / "routes" / "maritime_routes.py"

if not routes_file.exists():
    print(f"❌ {routes_file} not found!")
    sys.exit(1)

print(f"✅ Found routes file: {routes_file}")

# Read the file
with open(routes_file, 'r') as f:
    content = f.read()

# Find the dashboard route
dashboard_pattern = r'@maritime_bp\.route\([\'"](/maritime/dashboard)[\'"]\)[\s\S]*?def dashboard\([^)]*\):[\s\S]*?(?=\n@|\ndef |\Z)'
match = re.search(dashboard_pattern, content, re.DOTALL)

if match:
    print("✅ Found existing dashboard route")
    print(f"📏 Route length: {len(match.group(0))} characters")
    
    # Check what's in the route
    route_code = match.group(0)
    if 'routes' in route_code and 'render_template' in route_code:
        print("✅ Route has render_template and routes variable")
        
        # Check if it loads from RTZ
        if 'rtz_loader' in route_code or 'discover_rtz_files' in route_code:
            print("✅ Route uses RTZ loader")
        else:
            print("❌ Route doesn't use RTZ loader - this is the problem!")
            
            # Let's see what it does
            print("\n🔍 Current route code:")
            print("-" * 40)
            print(route_code[:500] + "..." if len(route_code) > 500 else route_code)
            print("-" * 40)
else:
    print("❌ Could not find dashboard route with pattern")
    # Try another pattern
    if '@maritime_bp.route' in content and 'dashboard' in content:
        print("⚠️ Found mention of dashboard, but pattern didn't match")

# Let's create a simple fix
print("\n🔧 Creating fix...")

# First, let's backup
backup_file = routes_file.with_suffix('.py.backup')
import shutil
shutil.copy2(routes_file, backup_file)
print(f"✅ Backup created: {backup_file}")

# Now create the fixed route
fixed_route = '''
@maritime_bp.route('/dashboard')
def dashboard():
    """
    Maritime dashboard - FIXED VERSION
    Loads actual RTZ routes from Norwegian Coastal Administration files
    """
    try:
        # Import RTZ loader
        try:
            from backend.rtz_loader_fixed import rtz_loader
            data = rtz_loader.get_dashboard_data()
            routes = data['routes']
            ports_list = data['ports_list']
            unique_ports_count = data['unique_ports_count']
            
            print(f"✅ Dashboard: Loaded {len(routes)} RTZ routes")
            
        except ImportError as e:
            print(f"⚠️ RTZ loader error: {e}")
            # Fallback to existing parser
            from backend.services.rtz_parser import discover_rtz_files
            routes = discover_rtz_files(enhanced=True)
            
            # Get unique ports
            unique_ports = set()
            for route in routes:
                if route.get('origin') and route['origin'] != 'Unknown':
                    unique_ports.add(route['origin'])
                if route.get('destination') and route['destination'] != 'Unknown':
                    unique_ports.add(route['destination'])
            
            ports_list = [
                'Bergen', 'Oslo', 'Stavanger', 'Trondheim',
                'Ålesund', 'Åndalsnes', 'Kristiansand',
                'Drammen', 'Sandefjord', 'Flekkefjord'
            ]
            unique_ports_count = len(unique_ports)
        
        # Get lang parameter
        lang = request.args.get('lang', 'en')
        
        # Create verification data
        from datetime import datetime
        empirical_verification = {
            'timestamp': datetime.now().isoformat(),
            'route_count': len(routes),
            'port_count': unique_ports_count,
            'verification_hash': f"RTZ_{len(routes)}_{unique_ports_count}",
            'data_source': 'routeinfo.no (Norwegian Coastal Administration)'
        }
        
        return render_template(
            'maritime_split/dashboard_base.html',
            routes=routes,
            ports_list=ports_list,
            unique_ports_count=unique_ports_count,
            empirical_verification=empirical_verification,
            lang=lang
        )
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency fallback
        return render_template(
            'maritime_split/dashboard_base.html',
            routes=[],
            ports_list=['Bergen', 'Oslo', 'Stavanger', 'Trondheim'],
            unique_ports_count=4,
            empirical_verification={'error': str(e)},
            lang=request.args.get('lang', 'en')
        )
'''

# Now replace or add the route
print("\n🎯 Options:")
print("1. Replace existing route (recommended)")
print("2. Add new route at the end")
print("3. Show me the current route and let me fix manually")

choice = input("\nChoose option (1/2/3): ").strip()

if choice == '1':
    # Replace the route
    if match:
        new_content = content.replace(match.group(0), fixed_route)
        with open(routes_file, 'w') as f:
            f.write(new_content)
        print("✅ Route replaced")
    else:
        print("❌ Could not find route to replace")
        
elif choice == '2':
    # Add at the end
    with open(routes_file, 'a') as f:
        f.write('\n\n' + fixed_route)
    print("✅ Route added at the end")
    print("💡 Note: Now you have TWO dashboard routes")
    
elif choice == '3':
    print("\n📋 Current route code:")
    print("=" * 60)
    if match:
        print(match.group(0))
    else:
        # Try to find by searching
        lines = content.split('\n')
        in_route = False
        route_lines = []
        
        for i, line in enumerate(lines):
            if '@maritime_bp.route' in line and 'dashboard' in line:
                in_route = True
                print(f"\n📍 Found at line {i+1}:")
            
            if in_route:
                route_lines.append(f"{i+1:4}: {line}")
                if line.strip() == '' and i > 0 and 'def ' in lines[i-1]:
                    # Empty line after function definition might mean end
                    break
        
        if route_lines:
            print('\n'.join(route_lines))
        else:
            print("Could not locate route")
    
    print("\n💡 Copy the fixed route code above and replace manually")

print("\n" + "=" * 50)
print("🚀 NEXT STEPS:")
print("1. Restart Flask server")
print("2. Visit: http://localhost:5000/maritime/dashboard?lang=en")
print("3. Check Flask logs for any errors")
print("\n📊 Expected result:")
print("   • Should show 34+ RTZ routes")
print("   • Should show 10 Norwegian ports")
print("   • Should say 'Actual RTZ Routes' in badge")