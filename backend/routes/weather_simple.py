# backend/routes/weather_simple.py
from flask import Blueprint, jsonify, request
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.weather_integration_service import weather_integration_service

bp = Blueprint('weather_simple', __name__)

@bp.route('/weather-simple')
def get_weather_simple():
    """Simple weather endpoint that definitely works"""
    try:
        print("🌤️ Weather API called!")
        
        # Get parameters or use defaults
        lat = request.args.get('lat', 60.39, type=float)
        lon = request.args.get('lon', 5.32, type=float)
        
        print(f"📍 Getting weather for {lat}, {lon}")
        
        # Get weather data
        weather_data = weather_integration_service.get_weather_for_dashboard(lat, lon)
        
        print(f"✅ Got weather data: {weather_data.get('display', {}).get('temperature', 'N/A')}")
        
        # Create response
        response = {
            'status': 'success',
            'timestamp': weather_data.get('timestamp'),
            'data': weather_data,
            'api_version': '1.0'
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Weather API error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__
        }), 500