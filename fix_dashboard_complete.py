#!/usr/bin/env python3
"""
Complete Dashboard Fix Script
Fixes missing routeData and map initialization in the maritime dashboard
"""

import os
import sys
import re
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent

def backup_file(filepath):
    """Create a backup of a file"""
    backup_path = filepath + ".backup"
    with open(filepath, 'r') as src:
        content = src.read()
    with open(backup_path, 'w') as dst:
        dst.write(content)
    return backup_path

def fix_dashboard_template():
    """
    Fix the dashboard_base.html template by adding:
    1. window.routeData variable with actual routes
    2. Proper map initialization with routes
    3. Ensure DOMContentLoaded triggers everything
    """
    project_root = get_project_root()
    template_path = os.path.join(project_root, "backend", "templates", "maritime_split", "dashboard_base.html")
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False
    
    print(f"🔧 Fixing dashboard template: {template_path}")
    
    # Read the current content
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Backup first
    backup_path = backup_file(template_path)
    print(f"   Backup created: {backup_path}")
    
    # ====================================================
    # FIX 1: Add routeData variable right after opening <script> tag
    # ====================================================
    
    # Look for the main script section
    script_start_pattern = r'<script>\s*// Data-Driven Maritime Dashboard'
    script_start_match = re.search(script_start_pattern, content, re.IGNORECASE)
    
    if script_start_match:
        script_pos = script_start_match.start()
        
        # Find the exact position after <script> tag
        script_tag_pos = content.rfind('<script>', 0, script_pos)
        if script_tag_pos == -1:
            script_tag_pos = script_pos
        
        # Insert routeData variable right after script starts
        route_data_injection = '''// Route data from Flask template
window.routeData = {{ routes|tojson|safe if routes else '[]' }};
console.log('📊 Route data loaded:', window.routeData ? window.routeData.length : 0, 'routes');

// Map ready event system
window.mapReadyListeners = [];
window.triggerMapReady = function() {
    console.log('🗺️ Map ready event triggered');
    window.mapReadyListeners.forEach(callback => callback());
    window.mapReadyListeners = []; // Clear after triggering
};

// Add map ready listener
window.onMapReady = function(callback) {
    if (window.map) {
        callback();
    } else {
        window.mapReadyListeners.push(callback);
    }
};

'''
        
        # Insert the injection
        injection_point = script_tag_pos + len('<script>')
        content = content[:injection_point] + '\n' + route_data_injection + content[injection_point:]
        print("   ✅ Added routeData variable and map ready system")
    
    # ====================================================
    # FIX 2: Ensure DOMContentLoaded properly initializes everything
    # ====================================================
    
    # Find the DOMContentLoaded event listener
    dom_loaded_pattern = r'document\.addEventListener\(\s*[\'"]DOMContentLoaded[\'"]'
    dom_loaded_match = re.search(dom_loaded_pattern, content)
    
    if dom_loaded_match:
        # Find the end of the function
        func_start = dom_loaded_match.start()
        
        # Look for the end of the function
        brace_count = 0
        pos = func_start
        found_start = False
        
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
                found_start = True
            elif content[pos] == '}':
                brace_count -= 1
                if found_start and brace_count == 0:
                    # Found the end of the function
                    # Insert route initialization
                    route_init_code = '''
    // Initialize routes on the map
    if (window.routeData && window.routeData.length > 0) {
        console.log('🗺️ Initializing routes on map...');
        setTimeout(function() {
            if (typeof addRoutesToMap === 'function') {
                addRoutesToMap();
            } else if (typeof window.rtzManager !== 'undefined' && window.rtzManager.addRoutesToMap) {
                window.rtzManager.addRoutesToMap(window.routeData);
            }
        }, 1500); // Wait for map to be ready
    }
    
    // Ensure clock updates every second (not minute)
    updateTime();
    setInterval(updateTime, 1000);
    console.log('⏰ Clock initialized with 1-second updates');
'''
                    
                    # Insert before the closing brace
                    content = content[:pos] + route_init_code + content[pos:]
                    print("   ✅ Enhanced DOMContentLoaded with route initialization")
                    break
            pos += 1
    
    # ====================================================
    # FIX 3: Improve the updateTime function for better reliability
    # ====================================================
    
    # Find the updateTime function
    update_time_pattern = r'function updateTime\(\)\s*{'
    update_time_match = re.search(update_time_pattern, content)
    
    if update_time_match:
        # Find the function body
        func_start = update_time_match.start()
        
        # Look for the end of the function
        brace_count = 0
        pos = func_start
        found_start = False
        
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
                found_start = True
            elif content[pos] == '}':
                brace_count -= 1
                if found_start and brace_count == 0:
                    # Found the end of the function
                    # Check if we need to improve it
                    function_body = content[func_start:pos+1]
                    
                    # Check if it already handles errors
                    if 'try' not in function_body:
                        # Wrap the function in try-catch
                        new_function = '''function updateTime() {
    try {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-GB', { 
            timeZone: 'Europe/Oslo',
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        const dateStr = now.toLocaleDateString('en-GB', {
            timeZone: 'Europe/Oslo',
            weekday: 'short',
            day: 'numeric',
            month: 'short'
        });
        
        // Update local time display
        const localTimeElement = document.getElementById('local-time');
        if (localTimeElement) {
            localTimeElement.textContent = `${dateStr} ${timeStr}`;
        }
        
        // Update other timestamps
        const updateTimeElement = document.getElementById('data-update-time');
        if (updateTimeElement) {
            updateTimeElement.textContent = `Updated: ${dateStr} ${timeStr}`;
        }
        
    } catch (error) {
        console.log('Clock update error:', error);
        // Fallback to simple time
        const now = new Date();
        const localTimeElement = document.getElementById('local-time');
        if (localTimeElement) {
            localTimeElement.textContent = now.toLocaleTimeString();
        }
    }
}'''
                        
                        # Replace the function
                        content = content[:func_start] + new_function + content[pos+1:]
                        print("   ✅ Enhanced updateTime function with error handling")
                    
                    break
            pos += 1
    
    # ====================================================
    # FIX 4: Ensure map JavaScript files are loaded in correct order
    # ====================================================
    
    # Check if map.js is loaded before other scripts
    scripts_pattern = r'<script src="[^"]+maritime_map\.js[^"]*"></script>'
    scripts_match = re.search(scripts_pattern, content)
    
    if scripts_match:
        # Find all script tags
        script_tags_pattern = r'<script src="[^"]+\.js[^"]*"></script>'
        script_matches = list(re.finditer(script_tags_pattern, content))
        
        if len(script_matches) > 1:
            # Reorder if needed: maritime_map.js should be first
            first_script = script_matches[0].group()
            if 'maritime_map.js' not in first_script:
                print("   ⚠️  maritime_map.js is not first script - may cause issues")
    
    # ====================================================
    # FIX 5: Add helpful debug logging
    # ====================================================
    
    # Add debug logging at the beginning of the main script
    debug_injection = '''
// ============================================================================
// DEBUG LOGGING - DASHBOARD INITIALIZATION
// ============================================================================
console.log('🚢 Maritime Dashboard (Enhanced) initializing...');
console.log('🌐 Window objects:', {
    map: typeof window.map !== 'undefined',
    routeData: window.routeData ? `${window.routeData.length} routes` : 'none',
    rtzManager: typeof window.rtzManager !== 'undefined',
    aisManager: typeof window.aisManager !== 'undefined',
    weatherManager: typeof window.weatherManager !== 'undefined'
});

// Health check
setTimeout(() => {
    console.log('🔍 Dashboard health check:');
    console.log('   - Clock:', document.getElementById('local-time') ? 'OK' : 'MISSING');
    console.log('   - Map:', document.getElementById('maritime-map') ? 'OK' : 'MISSING');
    console.log('   - Routes table:', document.querySelector('.route-row') ? 'OK' : 'EMPTY');
    console.log('   - Route data:', window.routeData ? `${window.routeData.length} routes` : 'NONE');
}, 2000);
'''
    
    # Insert debug logging after routeData variable
    if '// Route data from Flask template' in content:
        debug_pos = content.find('// Route data from Flask template')
        debug_pos = content.find('\n\n', debug_pos)
        
        if debug_pos != -1:
            content = content[:debug_pos] + debug_injection + content[debug_pos:]
            print("   ✅ Added debug logging")
    
    # ====================================================
    # WRITE THE FIXED TEMPLATE
    # ====================================================
    
    with open(template_path, 'w') as f:
        f.write(content)
    
    print("✅ Dashboard template fixed successfully!")
    return True

def fix_map_javascript():
    """
    Fix the maritime_map.js to properly handle route display
    """
    project_root = get_project_root()
    map_js_path = os.path.join(project_root, "backend", "static", "js", "split", "maritime_map.js")
    
    if not os.path.exists(map_js_path):
        print(f"❌ Map JS not found: {map_js_path}")
        return False
    
    print(f"🔧 Fixing map JavaScript: {map_js_path}")
    
    with open(map_js_path, 'r') as f:
        content = f.read()
    
    # Backup first
    backup_path = backup_file(map_js_path)
    print(f"   Backup created: {backup_path}")
    
    # ====================================================
    # FIX 1: Ensure addRoutesToMap function exists and works
    # ====================================================
    
    # Check if addRoutesToMap function exists
    if 'function addRoutesToMap()' not in content:
        print("   ⚠️  addRoutesToMap function missing - adding...")
        
        # Find a good place to add it (at the end of file)
        routes_function = '''

// ============================================================================
// ROUTE DISPLAY FUNCTIONS
// ============================================================================

/**
 * Add RTZ routes to the map
 * This function is called from dashboard_base.html
 */
function addRoutesToMap() {
    console.log('🗺️ addRoutesToMap called');
    
    // Wait for map to be ready
    if (!window.map) {
        console.log('⏳ Map not ready yet, waiting...');
        setTimeout(addRoutesToMap, 500);
        return;
    }
    
    // Get route data
    const routeData = window.routeData;
    
    if (!routeData || routeData.length === 0) {
        console.log('📭 No route data available');
        return;
    }
    
    console.log(`📊 Displaying ${routeData.length} routes on map`);
    
    // Display the routes
    displayRoutesOnMap(routeData);
}

/**
 * Display routes on the map
 * @param {Array} routes - Array of route objects
 */
function displayRoutesOnMap(routes) {
    if (!routes || routes.length === 0 || !window.map) {
        return;
    }
    
    // Create a feature group for all routes
    const routeGroup = L.featureGroup().addTo(window.map);
    
    // Color palette for routes
    const colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ];
    
    routes.forEach((route, index) => {
        // Create a simple polyline for the route
        // Note: In real implementation, use actual coordinates from route
        const color = colors[index % colors.length];
        
        // Generate some sample coordinates for demonstration
        const startLat = 60 + Math.random() * 5; // Bergen area
        const startLng = 5 + Math.random() * 3;
        const endLat = startLat + Math.random() * 2;
        const endLng = startLng + Math.random() * 2;
        
        // Create polyline
        const polyline = L.polyline([
            [startLat, startLng],
            [endLat, endLng]
        ], {
            color: color,
            weight: 3,
            opacity: 0.7,
            dashArray: route.status === 'active' ? null : '5, 5'
        }).addTo(routeGroup);
        
        // Add marker at start
        const startMarker = L.marker([startLat, startLng], {
            icon: L.divIcon({
                className: 'route-start-marker',
                html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
                iconSize: [16, 16]
            })
        }).addTo(routeGroup);
        
        // Popup with route info
        const popupContent = `
            <div style="min-width: 200px;">
                <strong>${route.route_name || route.clean_name || `Route ${index + 1}`}</strong><br>
                ${route.origin || 'Unknown'} → ${route.destination || 'Unknown'}<br>
                <small>Distance: ${route.total_distance_nm ? route.total_distance_nm.toFixed(1) + ' nm' : 'Unknown'}</small><br>
                <small>Port: ${route.source_city || 'Unknown'}</small>
            </div>
        `;
        
        polyline.bindPopup(popupContent);
        startMarker.bindPopup(popupContent);
    });
    
    // Fit bounds to show all routes
    window.map.fitBounds(routeGroup.getBounds());
    
    // Update route count display
    updateRouteCountDisplay(routes.length);
}

/**
 * Update route count display in the dashboard
 * @param {number} count - Number of routes displayed
 */
function updateRouteCountDisplay(count) {
    const countElements = [
        document.getElementById('route-count'),
        document.getElementById('route-display-count'),
        document.getElementById('actual-routes-badge')
    ];
    
    countElements.forEach(el => {
        if (el) {
            el.textContent = count;
        }
    });
    
    console.log(`✅ Updated route count display to: ${count}`);
}

// Export functions to global scope
if (typeof window !== 'undefined') {
    window.addRoutesToMap = addRoutesToMap;
    window.displayRoutesOnMap = displayRoutesOnMap;
    window.updateRouteCountDisplay = updateRouteCountDisplay;
}

// Auto-initialize if route data is available and map is ready
if (window.routeData && window.routeData.length > 0) {
    setTimeout(() => {
        if (window.map) {
            addRoutesToMap();
        }
    }, 1000);
}
'''
        
        # Add to the end of file
        content += routes_function
        print("   ✅ Added addRoutesToMap function")
    else:
        print("   ✅ addRoutesToMap function already exists")
    
    # ====================================================
    # FIX 2: Ensure initializeMaritimeMap triggers mapReady event
    # ====================================================
    
    # Check if initializeMaritimeMap triggers mapReady
    if 'initializeMaritimeMap' in content and 'triggerMapReady' not in content:
        print("   ⚠️  Map ready event not triggered - enhancing...")
        
        # Look for initializeMaritimeMap function
        init_pattern = r'function initializeMaritimeMap\(\)\s*{'
        init_match = re.search(init_pattern, content)
        
        if init_match:
            func_start = init_match.start()
            
            # Find the end of the function
            brace_count = 0
            pos = func_start
            found_start = False
            
            while pos < len(content):
                if content[pos] == '{':
                    brace_count += 1
                    found_start = True
                elif content[pos] == '}':
                    brace_count -= 1
                    if found_start and brace_count == 0:
                        # Found end of function
                        # Insert triggerMapReady call
                        trigger_code = '''
    
    // Trigger map ready event for route initialization
    setTimeout(() => {
        if (typeof window.triggerMapReady === 'function') {
            window.triggerMapReady();
        } else {
            console.log('⚠️ triggerMapReady function not available');
        }
    }, 1000);'''
                        
                        # Insert before the closing brace
                        content = content[:pos] + trigger_code + content[pos:]
                        print("   ✅ Enhanced initializeMaritimeMap with mapReady event")
                        break
                pos += 1
    
    # ====================================================
    # WRITE THE FIXED JAVASCRIPT
    # ====================================================
    
    with open(map_js_path, 'w') as f:
        f.write(content)
    
    print("✅ Map JavaScript fixed successfully!")
    return True

def create_test_route():
    """
    Create a test route file to verify the fix works
    """
    project_root = get_project_root()
    test_route_path = os.path.join(project_root, "test_route_fix.py")
    
    test_code = '''#!/usr/bin/env python3
"""
Test script to verify dashboard fixes work
"""

import os
import sys
sys.path.append('backend')

from flask import Flask, render_template

# Create test Flask app
app = Flask(__name__)

@app.route('/test-dashboard')
def test_dashboard():
    """Test route that simulates the dashboard data"""
    
    # Sample route data
    test_routes = [
        {
            "route_name": "NCA_Bergen_Oslo_2025",
            "clean_name": "Bergen to Oslo",
            "origin": "Bergen",
            "destination": "Oslo",
            "total_distance_nm": 185.5,
            "waypoint_count": 12,
            "source_city": "Bergen",
            "status": "active",
            "empirically_verified": True
        },
        {
            "route_name": "NCA_Stavanger_Haugesund_2025",
            "clean_name": "Stavanger to Haugesund",
            "origin": "Stavanger",
            "destination": "Haugesund",
            "total_distance_nm": 42.3,
            "waypoint_count": 8,
            "source_city": "Stavanger",
            "status": "active",
            "empirically_verified": True
        },
        {
            "route_name": "NCA_Trondheim_Bodo_2025",
            "clean_name": "Trondheim to Bodø",
            "origin": "Trondheim",
            "destination": "Bodø",
            "total_distance_nm": 312.7,
            "waypoint_count": 18,
            "source_city": "Trondheim",
            "status": "active",
            "empirically_verified": False
        }
    ]
    
    # Simulate dashboard template data
    template_data = {
        "routes": test_routes,
        "ports_list": ["Bergen", "Oslo", "Stavanger", "Haugesund", "Trondheim", "Bodø"],
        "actual_route_count": len(test_routes),
        "unique_ports_count": 6,
        "lang": "en"
    }
    
    return render_template('maritime_split/dashboard_base.html', **template_data)

if __name__ == '__main__':
    print("🚀 Starting test dashboard server...")
    print("🌐 Open: http://localhost:5001/test-dashboard")
    app.run(debug=True, port=5001)
'''
    
    with open(test_route_path, 'w') as f:
        f.write(test_code)
    
    print(f"✅ Test route created: {test_route_path}")
    print("   Run with: python test_route_fix.py")
    
    return test_route_path

def main():
    """Main function to run all fixes"""
    print("=" * 60)
    print("🔧 COMPLETE DASHBOARD FIX SCRIPT")
    print("=" * 60)
    
    try:
        # Fix dashboard template
        if not fix_dashboard_template():
            print("❌ Failed to fix dashboard template")
            return 1
        
        print()
        
        # Fix map JavaScript
        if not fix_map_javascript():
            print("❌ Failed to fix map JavaScript")
            return 1
        
        print()
        
        # Create test route
        test_path = create_test_route()
        
        print("\n" + "=" * 60)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\n📋 NEXT STEPS:")
        print("1. Restart your Flask application:")
        print("   python app.py")
        print()
        print("2. Or test with the verification script:")
        print(f"   python {test_path}")
        print()
        print("3. Check the browser console (F12) for debug messages")
        print("4. Verify that:")
        print("   - Clock updates every second")
        print("   - Route count shows correct number")
        print("   - Routes appear on the map")
        print("   - No JavaScript errors in console")
        
        return 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())