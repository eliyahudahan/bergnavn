# backend/controllers/maritime_controller.py
"""
Controller for maritime operations - UPDATED with COMPLETE RTZ route data including waypoints.
FIXED: Now uses FixedRTZLoader to get complete route data with actual waypoint coordinates.
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from datetime import datetime
from backend.services.maritime_service import maritime_service
from backend.services.route_service import route_service
from backend.utils.helpers import get_current_language
# IMPORTANT: Import the FixedRTZLoader to get complete route data
from backend.services.rtz_loader_fixed import rtz_loader

# Blueprint for maritime routes
maritime_bp = Blueprint('maritime', __name__, url_prefix='/maritime')

@maritime_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Render the maritime dashboard with COMPLETE RTZ route data including waypoints."""
    try:
        lang = get_current_language()
        
        # FIXED: Use FixedRTZLoader to get complete route data WITH waypoints
        # Instead of route_service.get_empirical_count() which returns limited data
        complete_dashboard_data = rtz_loader.get_dashboard_data()
        
        # Prepare context with COMPLETE route data
        context = {
            'lang': lang,
            'routes': complete_dashboard_data.get('routes', []),  # NOW INCLUDES WAYPOINTS
            'route_count': complete_dashboard_data.get('total_routes', 0),
            'ports_list': complete_dashboard_data.get('ports_list', []),
            'unique_ports_count': complete_dashboard_data.get('unique_ports_count', 0),
            'total_waypoints': complete_dashboard_data.get('total_waypoints', 0),
            'cities_with_routes': complete_dashboard_data.get('cities_with_routes', 0),
            'dashboard_metadata': complete_dashboard_data.get('metadata', {}),
            'data_source': 'Norwegian Coastal Administration (NCA)',
            'data_format': 'Complete with waypoints',
            'data_timestamp': complete_dashboard_data.get('timestamp', datetime.now().isoformat())
        }
        
        # Log success with actual data details
        current_app.logger.info(
            f"✅ Maritime dashboard: {complete_dashboard_data.get('total_routes', 0)} routes, "
            f"{complete_dashboard_data.get('total_waypoints', 0)} waypoints, "
            f"{complete_dashboard_data.get('unique_ports_count', 0)} unique ports"
        )
        
        # Debug: Check if waypoints are present
        if complete_dashboard_data.get('routes'):
            sample_route = complete_dashboard_data['routes'][0]
            current_app.logger.debug(f"🔍 Sample route debug:")
            current_app.logger.debug(f"   Name: {sample_route.get('route_name')}")
            current_app.logger.debug(f"   Waypoint count: {sample_route.get('waypoint_count')}")
            current_app.logger.debug(f"   Has waypoints key: {'waypoints' in sample_route}")
            if 'waypoints' in sample_route:
                current_app.logger.debug(f"   Number of waypoints in array: {len(sample_route['waypoints'])}")
                if sample_route['waypoints']:
                    current_app.logger.debug(f"   First waypoint: {sample_route['waypoints'][0]}")
        
        # IMPORTANT: Use the correct template for the split dashboard
        # Change 'maritime/dashboard.html' to 'maritime_split/dashboard_base.html'
        return render_template('maritime_split/dashboard_base.html', **context)
        
    except Exception as e:
        current_app.logger.error(f"❌ Error in maritime dashboard: {e}")
        # Return a minimal but functional dashboard even if there's an error
        return render_template('maritime_split/dashboard_base.html', 
                             lang=get_current_language(),
                             routes=[],
                             route_count=0,
                             ports_list=[],
                             unique_ports_count=0,
                             error_message=str(e))

@maritime_bp.route('/api/ais-data', methods=['GET'])
def get_ais_data():
    """
    Main API endpoint for maritime dashboard data.
    Returns vessels, weather, ports, and RISK DATA.
    """
    try:
        data = maritime_service.get_maritime_dashboard_data()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@maritime_bp.route('/api/weather', methods=['GET'])
def get_weather():
    """API endpoint for weather data."""
    try:
        lat = request.args.get('lat', default=60.392, type=float)
        lon = request.args.get('lon', default=5.324, type=float)
        
        # This would use your actual weather service
        weather_data = {
            'location': {'lat': lat, 'lon': lon},
            'temperature': 8.5,
            'wind_speed': 5.2,
            'wind_direction': 45,
            'wave_height': 1.2,
            'forecast': 'Partly cloudy',
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(weather_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@maritime_bp.route('/api/rtz/empirical', methods=['GET'])
def get_empirical_rtz():
    """API endpoint for empirical RTZ route data."""
    try:
        empirical_data = route_service.get_empirical_count()
        
        return jsonify({
            'success': True,
            'empirical_count': empirical_data.get('empirical_count', 0),
            'routes': empirical_data.get('routes', []),
            'ports_count': empirical_data.get('ports_count', 0),
            'methodology': empirical_data.get('methodology', ''),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@maritime_bp.route('/api/rtz/complete', methods=['GET'])
def get_complete_rtz():
    """NEW API endpoint for COMPLETE RTZ route data including waypoints."""
    try:
        # Use the FixedRTZLoader to get complete data
        complete_dashboard_data = rtz_loader.get_dashboard_data()
        
        return jsonify({
            'success': True,
            'data': complete_dashboard_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_complete_rtz: {e}")
        return jsonify({'error': str(e)}), 400

@maritime_bp.route('/api/rtz/statistics', methods=['GET'])
def get_rtz_statistics():
    """API endpoint for RTZ route statistics."""
    try:
        stats = route_service.get_route_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@maritime_bp.route('/api/risks', methods=['GET'])
def get_risk_assessment():
    """API endpoint specifically for risk assessment."""
    try:
        mmsi = request.args.get('mmsi', type=str)
        
        if not mmsi:
            return jsonify({'error': 'MMSI parameter required'}), 400
        
        # Get data for specific vessel
        data = maritime_service.get_maritime_dashboard_data()
        vessel = next((v for v in data['vessels'] if v.get('mmsi') == mmsi), None)
        
        if not vessel:
            return jsonify({'error': 'Vessel not found'}), 404
        
        # Find risks for this vessel
        vessel_risks = next((r for r in data['risks'] if r.get('vessel_mmsi') == mmsi), None)
        
        return jsonify({
            'vessel': vessel,
            'risks': vessel_risks.get('risks', []) if vessel_risks else [],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@maritime_bp.route('/api/rtz/routes', methods=['GET'])
def get_all_rtz_routes():
    """Direct API endpoint to get ALL RTZ routes with waypoints - for debugging."""
    try:
        # Force reload all routes
        all_routes = rtz_loader.load_all_routes()
        
        # Add IDs if missing
        for i, route in enumerate(all_routes):
            if 'route_id' not in route:
                route['route_id'] = f"rtz_{i+1:03d}"
        
        return jsonify({
            'success': True,
            'count': len(all_routes),
            'routes': all_routes,
            'waypoints_present': all_routes and 'waypoints' in all_routes[0],
            'sample_route': all_routes[0] if all_routes else None,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_all_rtz_routes: {e}")
        return jsonify({'error': str(e)}), 400