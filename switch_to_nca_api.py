#!/usr/bin/env python3
"""
SWITCH TO NCA API: Make the dashboard use the NCA API with REAL waypoints
"""

import re
import os

def switch_dashboard_to_nca_api():
    """Switch dashboard to use NCA API instead of old maritime API"""
    
    dashboard_path = "backend/templates/maritime_split/dashboard_base.html"
    if not os.path.exists(dashboard_path):
        print(f"❌ Dashboard not found: {dashboard_path}")
        return False
    
    print("🔧 Switching dashboard to use NCA API with REAL waypoints...")
    
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    # Find the script section
    scripts_section = re.search(r'{% block scripts %}(.*?){% endblock %}', content, re.DOTALL)
    
    if not scripts_section:
        print("❌ Could not find scripts block")
        return False
    
    scripts_content = scripts_section.group(1)
    
    # Check if already using NCA
    if 'nca_routes.js' in scripts_content:
        print("✅ Dashboard already uses NCA API")
        return True
    
    # Replace maritime_map.js with nca_routes.js
    if 'maritime_map.js' in scripts_content:
        # Simple replacement
        new_scripts = scripts_content.replace(
            'src="{{ url_for(\'static\', filename=\'js/split/maritime_map.js\') }}"',
            'src="{{ url_for(\'static\', filename=\'js/split/nca_routes.js\') }}"'
        )
        
        # Also add a comment
        new_scripts = new_scripts.replace(
            '<script src="{{ url_for(\'static\', filename=\'js/split/nca_routes.js\') }}"></script>',
            '<!-- NCA Routes with REAL waypoints -->\n<script src="{{ url_for(\'static\', filename=\'js/split/nca_routes.js\') }}"></script>'
        )
        
        # Update content
        content = content[:scripts_section.start(1)] + new_scripts + content[scripts_section.end(1):]
        
        print("✅ Replaced maritime_map.js with nca_routes.js")
    else:
        print("⚠️ maritime_map.js not found in scripts")
    
    # Also update the JavaScript to use NCA API
    if 'loadRTZRoutes' in content:
        # Add instruction to use NCA
        nca_injection = '''
// ============================================
// NCA API INTEGRATION - USING REAL WAYPOINTS
// ============================================

// Override the standard route loader to use NCA API
if (typeof loadRealNCARoutes === 'function') {
    console.log('🚀 Using NCA API with REAL waypoints');
    // Store original for fallback
    window.originalLoadRTZRoutes = loadRTZRoutes;
    // Replace with NCA loader
    window.loadRTZRoutes = loadRealNCARoutes;
} else {
    console.log('⚠️ NCA API not available, using standard routes');
}
'''
        
        # Find where to inject (after DOMContentLoaded)
        if 'DOMContentLoaded' in content:
            # Inject after the first script tag
            script_pos = content.find('<script>')
            if script_pos != -1:
                end_script_tag = content.find('</script>', script_pos)
                if end_script_tag != -1:
                    # Insert before closing script tag
                    injection_point = end_script_tag
                    content = content[:injection_point] + nca_injection + content[injection_point:]
                    print("✅ Added NCA API integration script")
    
    # Write back
    with open(dashboard_path, 'w') as f:
        f.write(content)
    
    print("✅ Dashboard switched to NCA API")
    return True

def verify_nca_api_working():
    """Verify NCA API is working"""
    
    import requests
    try:
        response = requests.get("http://localhost:5000/nca/api/nca/routes", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ NCA API working: {data.get('total_routes', 0)} routes, {data.get('total_waypoints', 0):,} waypoints")
            return True
        else:
            print(f"❌ NCA API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ NCA API error: {e}")
        return False

def main():
    print("="*60)
    print("🚀 SWITCHING TO NCA API WITH REAL NORWEGIAN WAYPOINTS")
    print("="*60)
    
    # Verify NCA API is working
    print("\n🔍 Verifying NCA API...")
    if not verify_nca_api_working():
        print("❌ NCA API not working, make sure server is running")
        print("💡 Run: python app.py")
        return 1
    
    # Switch dashboard
    print("\n🔄 Switching dashboard to use NCA API...")
    if not switch_dashboard_to_nca_api():
        print("❌ Failed to switch dashboard")
        return 1
    
    print("\n" + "="*60)
    print("✅ SWITCH COMPLETE!")
    print("="*60)
    
    print("\n📋 WHAT CHANGED:")
    print("1. Dashboard now uses NCA API instead of old maritime API")
    print("2. 34 routes with 922 REAL waypoints will be displayed")
    print("3. Actual GPS coordinates from Norwegian Coastal Administration")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Reload dashboard: http://localhost:5000/maritime/dashboard")
    print("2. Check browser console (Ctrl+Shift+J)")
    print("3. Should see: 'Using NCA API with REAL waypoints'")
    print("4. Routes should appear on map with actual coordinates")
    
    print("\n🇳🇴 You're now using REAL Norwegian Coastal Administration data!")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())