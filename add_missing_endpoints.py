#!/usr/bin/env python3
"""
Add missing API endpoints to maritime_routes.py
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def add_missing_endpoints():
    """Add missing endpoints that return 404"""
    filepath = os.path.join(project_root, "backend", "routes", "maritime_routes.py")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check what's missing
    missing = []
    
    if '@maritime_bp.route(\'/api/rtz/routes\')' not in content:
        missing.append('/api/rtz/routes')
    
    if '@maritime_bp.route(\'/api/weather-dashboard\')' not in content:
        missing.append('/api/weather-dashboard')
    
    if not missing:
        print("✅ All endpoints exist")
        return
    
    print(f"🔧 Adding {len(missing)} missing endpoints...")
    
    # Add endpoints at the end of the file
    endpoints_code = '''

# ============================================================================
# MISSING ENDPOINTS - ADDED FOR COMPATIBILITY
# ============================================================================

@maritime_bp.route('/api/rtz/routes')
def get_rtz_routes():
    """
    Get RTZ routes from database.
    """
    try:
        from backend.models.route import Route
        from flask import jsonify
        
        routes = Route.query.filter_by(is_active=True).all()
        
        formatted_routes = []
        for route in routes:
            formatted_routes.append({
                'name': route.name,
                'origin': route.origin,
                'destination': route.destination,
                'total_distance_nm': route.total_distance_nm,
                'duration_days': route.duration_days,
                'is_active': route.is_active
            })
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'routes': formatted_routes,
            'count': len(formatted_routes)
        })
        
    except Exception as e:
        current_app.logger.error(f"RTZ routes error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maritime_bp.route('/api/weather-dashboard')
def get_dashboard_weather():
    """
    Weather data for dashboard display.
    """
    try:
        if not hasattr(current_app, 'weather_service'):
            return jsonify({
                'temperature_c': 8.5,
                'wind_speed_ms': 5.2,
                'city': 'Bergen',
                'source': 'fallback'
            })
        
        weather = current_app.weather_service.get_current_weather()
        
        return jsonify({
            'temperature_c': weather.get('temperature_c', 8.5),
            'wind_speed_ms': weather.get('wind_speed_ms', 5.2),
            'wind_direction': weather.get('wind_direction', 'NW'),
            'city': weather.get('city', 'Bergen'),
            'source': 'weather_service'
        })
        
    except Exception as e:
        current_app.logger.error(f"Weather dashboard error: {e}")
        return jsonify({
            'temperature_c': 8.5,
            'wind_speed_ms': 5.2,
            'city': 'Bergen',
            'source': 'error_fallback'
        })
'''
    
    # Add to end of file
    new_content = content + endpoints_code
    
    # Backup and write
    backup = filepath + '.endpoints_backup'
    with open(backup, 'w') as f:
        f.write(content)
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Added missing endpoints")
    print(f"   Added: {', '.join(missing)}")
    print(f"   Backup: {backup}")

if __name__ == "__main__":
    print("🔧 Adding missing API endpoints...")
    add_missing_endpoints()