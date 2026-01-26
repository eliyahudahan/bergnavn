# backend/routes/api_weather.py
from flask import Blueprint, jsonify, request
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

bp = Blueprint('api_weather', __name__)

@bp.route('/weather-pro')
def weather_pro():
    """Weather API endpoint using the new integration service"""
    try:
        # Import the weather service
        from services.weather_integration_service import weather_integration_service
        
        # Get parameters
        lat = request.args.get('lat', 60.39, type=float)
        lon = request.args.get('lon', 5.32, type=float)
        
        print(f"🌤️ Weather Pro API called for {lat}, {lon}")
        
        # Get weather data
        weather_data = weather_integration_service.get_weather_for_dashboard(lat, lon)
        
        # Ensure display object exists
        if 'display' not in weather_data:
            weather_data['display'] = {
                'temperature': f"{round(weather_data.get('temperature_c', 0))}°C",
                'wind': f"{round(weather_data.get('wind_speed_ms', 0))} m/s",
                'location': weather_data.get('location', 'Bergen'),
                'condition': weather_data.get('condition', 'Unknown'),
                'source_badge': get_source_badge(weather_data.get('data_source', 'unknown')),
                'icon': get_weather_icon(weather_data.get('condition', ''))
            }
        
        # Create response
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': weather_data,
            'api_version': '2.0'
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Weather Pro API error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/weather-sources')
def weather_sources():
    """Get information about weather data sources"""
    try:
        from services.weather_integration_service import weather_integration_service
        
        summary = weather_integration_service.get_service_summary()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/weather-test')
def weather_test():
    """Test endpoint to verify weather service is working"""
    try:
        from services.weather_integration_service import weather_integration_service
        
        # Test with Bergen coordinates
        weather_data = weather_integration_service.get_weather_for_dashboard(60.39, 5.32)
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'test_result': {
                'data_source': weather_data.get('data_source'),
                'temperature_c': weather_data.get('temperature_c'),
                'wind_speed_ms': weather_data.get('wind_speed_ms'),
                'location': weather_data.get('location'),
                'service_working': True
            },
            'message': 'Weather service test completed successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def get_source_badge(source):
    """Helper function to get source badge"""
    badges = {
        'met_norway': '🇳🇴 MET Norway',
        'met_norway_live': '🇳🇴 MET Norway',
        'barentswatch': '🌊 BarentsWatch',
        'openweather': '🌍 OpenWeatherMap',
        'empirical': '📊 Empirical',
        'fallback_empirical': '📊 Empirical',
        'emergency': '🚨 Emergency',
        'fallback': '📊 Fallback'
    }
    return badges.get(source, '📊 Weather')

def get_weather_icon(condition):
    """Helper function to get weather icon"""
    if not condition:
        return 'cloud'
    
    condition_lower = condition.lower()
    
    if 'clear' in condition_lower or 'fair' in condition_lower or 'sun' in condition_lower:
        return 'sun'
    elif 'cloud' in condition_lower:
        return 'cloud'
    elif 'rain' in condition_lower:
        return 'cloud-rain'
    elif 'snow' in condition_lower:
        return 'snow'
    elif 'fog' in condition_lower or 'mist' in condition_lower or 'haze' in condition_lower:
        return 'cloud-fog'
    elif 'thunder' in condition_lower or 'lightning' in condition_lower:
        return 'cloud-lightning'
    else:
        return 'cloud'