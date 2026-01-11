# backend/controllers/maritime_controller.py
"""
Controller for maritime operations - UPDATED with empirical route counting.
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from datetime import datetime
from backend.services.maritime_service import maritime_service
from backend.services.route_service import route_service
from backend.utils.helpers import get_current_language

# Blueprint for maritime routes
maritime_bp = Blueprint('maritime', __name__, url_prefix='/maritime')

@maritime_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Render the maritime dashboard with empirical route count."""
    try:
        lang = get_current_language()
        
        # Get empirical route data
        empirical_data = route_service.get_empirical_count()
        
        # Prepare context
        context = {
            'lang': lang,
            'routes': empirical_data.get('routes', []),
            'route_count': empirical_data.get('empirical_count', 0),
            'ports_count': empirical_data.get('ports_count', 0),
            'empirical_verification': {
                'methodology': empirical_data.get('methodology', ''),
                'status': empirical_data.get('status', '')
            }
        }
        
        current_app.logger.info(
            f"Maritime dashboard: {empirical_data.get('empirical_count', 0)} routes, "
            f"{empirical_data.get('ports_count', 0)} ports"
        )
        
        return render_template('maritime/dashboard.html', **context)
        
    except Exception as e:
        current_app.logger.error(f"Error in maritime dashboard: {e}")
        return jsonify({'error': str(e)}), 500

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