#!/usr/bin/env python3
"""
Fix the duplicate addRoutesToMap function conflict in maritime_map.js
"""

import os

def fix_maritime_map_conflict():
    map_js_path = 'backend/static/js/split/maritime_map.js'
    
    if not os.path.exists(map_js_path):
        print(f"❌ File not found: {map_js_path}")
        return False
    
    with open(map_js_path, 'r') as f:
        content = f.read()
    
    print("🔧 Fixing duplicate addRoutesToMap conflict...")
    
    # Find the duplicate function at the end (the demo one)
    duplicate_start = content.find('// ============================================================================\n// ROUTE DISPLAY FUNCTIONS\n// ============================================================================')
    
    if duplicate_start != -1:
        # Keep everything before the duplicate
        fixed_content = content[:duplicate_start]
        
        # Add proper export of the real function
        fixed_content += '''
// ============================================================================
// EXPORT FUNCTIONS FOR DASHBOARD INTEGRATION
// ============================================================================

// Export addRoutesToMap for dashboard (points to the real function)
window.addRoutesToMap = displayRoutesOnMap;

// Trigger map ready event for dashboard integration
setTimeout(() => {
    if (typeof window.triggerMapReady === 'function') {
        window.triggerMapReady();
    }
}, 1500);

console.log("✅ Maritime map module ready for dashboard integration");
'''
        
        # Write back
        with open(map_js_path, 'w') as f:
            f.write(fixed_content)
        
        print("✅ Removed duplicate function and added proper export")
        return True
    
    print("⚠️ Duplicate function not found, checking if export exists...")
    
    # Check if window.addRoutesToMap is already exported
    if 'window.addRoutesToMap = displayRoutesOnMap' not in content:
        # Add the export at the end
        export_code = '''

// ============================================================================
// DASHBOARD INTEGRATION
// ============================================================================

// Export for dashboard_base.html
window.addRoutesToMap = displayRoutesOnMap;

// Auto-initialize routes if data is available
if (window.routeData && window.routeData.length > 0) {
    setTimeout(() => {
        displayRoutesOnMap();
    }, 2000);
}

console.log("🗺️ Map module ready for dashboard");
'''
        
        content += export_code
        
        with open(map_js_path, 'w') as f:
            f.write(content)
        
        print("✅ Added dashboard integration export")
        return True
    
    print("✅ Export already exists")
    return True

if __name__ == "__main__":
    fix_maritime_map_conflict()
    print("\n✅ Fix applied!")
    print("📋 Next: Reload the dashboard page")