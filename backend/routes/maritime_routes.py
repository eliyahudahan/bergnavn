# backend/routes/maritime_routes.py - Maritime routes for BergNavn application
from flask import Blueprint, render_template, request, jsonify
import requests
import os
from datetime import datetime
from backend.utils.translations import translate  # Translation utility

# Use unique blueprint name to avoid conflicts
maritime_bp = Blueprint('maritime_bp', __name__)

@maritime_bp.route('/')
def maritime_dashboard():
    """
    Maritime Dashboard - Real-time tracking for Kristiansand ↔ Oslo route
    """
    # Get language from request parameters or use default
    lang = request.args.get('lang', 'en')
    
    # Ensure valid language
    if lang not in ['en', 'no']:
        lang = 'en'
    
    return render_template('maritime_dashboard.html', lang=lang)

@maritime_bp.route('/api/weather')
def get_maritime_weather():
    """
    API endpoint for maritime weather data along Kristiansand-Oslo route
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        location_name = request.args.get('location', 'Unknown Location')
        
        if not lat or not lon:
            return jsonify({
                'status': 'error',
                'message': 'Latitude and longitude parameters are required'
            }), 400
        
        # Use OpenWeather API with environment variable
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'OpenWeather API key not configured in environment'
            }), 500
            
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            weather_info = {
                'status': 'success',
                'data': {
                    'temperature': data['main']['temp'],
                    'wind_speed': data['wind']['speed'],
                    'wind_direction': data['wind'].get('deg', 0),
                    'wind_gust': data['wind'].get('gust', data['wind']['speed'] * 1.3),
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'condition': data['weather'][0]['description'],
                    'icon': map_weather_icon(data['weather'][0]['main']),
                    'location': location_name,
                    'source': 'OpenWeather',
                    'timestamp': datetime.now().isoformat()
                }
            }
            return jsonify(weather_info)
        else:
            return jsonify({
                'status': 'error',
                'message': f'Weather API error: {response.status_code}'
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'Weather API request timeout'
        }), 504
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@maritime_bp.route('/api/route/eta')
def calculate_route_eta():
    """
    Calculate ETA for Kristiansand-Oslo route based on weather conditions
    """
    try:
        # Default route parameters for Kristiansand to Oslo
        base_distance = 250  # nautical miles
        base_speed = 12  # knots
        base_eta = base_distance / base_speed  # ~20.8 hours
        
        # Get weather data for route optimization
        route_points = [
            {'lat': 58.1467, 'lon': 8.0980, 'name': 'Kristiansand'},
            {'lat': 58.0667, 'lon': 8.0500, 'name': 'Oksøy Lighthouse'},
            {'lat': 59.9115, 'lon': 10.7570, 'name': 'Oslo Fjord'}
        ]
        
        # Calculate weather impact factor
        weather_factor = 1.0
        
        for point in route_points:
            # In a real implementation, you would fetch weather for each point
            # For now, using a simplified model
            weather_factor += 0.05  # Small adjustment per point
        
        adjusted_eta = base_eta * weather_factor
        
        return jsonify({
            'status': 'success',
            'data': {
                'base_eta': round(base_eta, 1),
                'adjusted_eta': round(adjusted_eta, 1),
                'distance': base_distance,
                'average_speed': base_speed,
                'weather_impact': round((weather_factor - 1.0) * 100, 1),
                'unit': 'hours'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'ETA calculation error: {str(e)}'
        }), 500

def map_weather_icon(condition):
    """
    Map OpenWeather condition to appropriate emoji icon
    """
    icon_map = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Fog': '🌫️',
        'Smoke': '💨',
        'Dust': '💨',
        'Sand': '💨',
        'Ash': '💨',
        'Squall': '💨',
        'Tornado': '🌪️'
    }
    return icon_map.get(condition, '🌡️')  # Default icon for unknown conditions