"""
Controller for maritime operations (AIS, RTZ routes, weather, risks).
Delegates all business logic to MaritimeService.
Follows the same pattern as cruise_controller.py.
"""

from flask import Blueprint, request, jsonify, render_template
from backend.services.maritime_service import maritime_service
from backend.utils.helpers import get_current_language

# Blueprint for maritime routes
maritime_bp = Blueprint('maritime', __name__, url_prefix='/maritime')

@maritime_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Render the main maritime dashboard."""
    try:
        lang = get_current_language()
        return render_template('maritime/dashboard.html', lang=lang)
    except Exception as e:
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

@maritime_bp.route('/api/rtz/simple', methods=['GET'])
def get_simple_rtz():
    """API endpoint for simple RTZ route data."""
    try:
        rtz_data = maritime_service.get_sample_rtz_routes()
        return jsonify(rtz_data), 200
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