#!/usr/bin/env python3
"""
Generate JavaScript to add routes to the map
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def generate_map_js():
    """Generate JavaScript to display routes on map"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found")
        return
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Get routes with coordinates (need to parse from names)
        routes = conn.execute(text("""
            SELECT name, origin, destination, total_distance_nm
            FROM routes
            WHERE is_active = true
        """)).fetchall()
        
        print(f"📊 Found {len(routes)} routes for map")
        
        # Generate JavaScript
        js_code = """// Auto-generated route data for map
var routeData = [
"""
        
        for i, route in enumerate(routes):
            # Extract coordinates from names (simplified)
            coords = extract_coords_from_name(route.name)
            
            if coords:
                js_code += f"""    {{
        id: {i + 1},
        name: "{route.name}",
        origin: "{route.origin}",
        destination: "{route.destination}",
        distance: {route.total_distance_nm},
        coordinates: {coords}
    }},
"""
        
        js_code += """];

// Add routes to map
function addRoutesToMap() {
    if (typeof window.map === 'undefined') {
        console.log('Map not ready yet');
        setTimeout(addRoutesToMap, 1000);
        return;
    }
    
    console.log('Adding', routeData.length, 'routes to map');
    
    routeData.forEach(function(route) {
        if (route.coordinates && route.coordinates.length >= 2) {
            // Create polyline
            var polyline = L.polyline(route.coordinates, {
                color: '#3498db',
                weight: 3,
                opacity: 0.7
            }).addTo(window.map);
            
            // Add popup
            polyline.bindPopup(`
                <strong>${route.name}</strong><br>
                ${route.origin} → ${route.destination}<br>
                Distance: ${route.distance} nm
            `);
        }
    });
}

// Run when map is ready
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(addRoutesToMap, 2000);
});
"""
        
        # Save to file
        js_path = os.path.join(project_root, "backend", "static", "js", "split", "routes_on_map.js")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(js_path), exist_ok=True)
        
        with open(js_path, 'w') as f:
            f.write(js_code)
        
        print(f"✅ Generated map JavaScript: {js_path}")
        print(f"   Routes: {len(routes)}")
        print("\n💡 Add this to dashboard_base.html:")
        print(f'   <script src="{{{{ url_for(\'static\', filename=\'js/split/routes_on_map.js\') }}}}"></script>')

def extract_coords_from_name(name):
    """Extract coordinates from route name (simplified)"""
    # This is a simplified version - you'd need actual coordinate data
    import re
    
    # Look for patterns like 64.26, 9.75
    coord_pattern = r'(\d+\.\d+)[,_\s]+(\d+\.\d+)'
    matches = re.findall(coord_pattern, name)
    
    if matches:
        # Convert to Leaflet format [lat, lng]
        coords = []
        for lat, lng in matches[:2]:  # Take first two coordinates
            coords.append([float(lat), float(lng)])
        return coords
    
    return None

if __name__ == "__main__":
    print("🗺️ Generating map routes JavaScript...")
    generate_map_js()