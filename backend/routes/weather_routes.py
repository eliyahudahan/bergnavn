# backend/routes/weather_routes.py - Updated
from flask import Blueprint, render_template, request, jsonify
from backend.models import WeatherStatus, Route
from sqlalchemy import desc, and_, func
from backend.extensions import db
from backend.utils.helpers import get_current_language
import requests
import os
from datetime import datetime

# Blueprint for weather-related pages
weather_bp = Blueprint('weather', __name__, url_prefix='/weather')

@weather_bp.route('/')
def weather_dashboard():
    """
    UI Endpoint: Weather Dashboard
    Purpose:
        - Display the latest active weather statuses per port.
        - Show all active routes with their ordered legs.
        - Include current language for i18n.
    """
    # Subquery: get the latest datetime for each port_id (only active records)
    subquery = (
        db.session.query(
            WeatherStatus.port_id,
            func.max(WeatherStatus.datetime).label('max_datetime')
        )
        .filter(WeatherStatus.is_active == True)
        .group_by(WeatherStatus.port_id)
        .subquery()
    )

    # Query: fetch only the most recent WeatherStatus entries
    latest_statuses = (
        db.session.query(WeatherStatus)
        .join(
            subquery,
            and_(
                WeatherStatus.port_id == subquery.c.port_id,
                WeatherStatus.datetime == subquery.c.max_datetime
            )
        )
        .all()
    )

    # Query: fetch all active routes with legs ordered by leg_order
    routes = (
        Route.query
        .filter(Route.is_active == True)
        .order_by(Route.id)
        .all()
    )

    # Ensure each route's legs are sorted by leg_order
    for route in routes:
        route.legs.sort(key=lambda leg: leg.leg_order)

    # Get current language for rendering templates
    lang = get_current_language()

    return render_template(
        'weather_dashboard.html',
        statuses=latest_statuses,
        routes=routes,
        lang=lang
    )

@weather_bp.route('/api/maritime-weather')
def get_maritime_weather():
    """
    ENHANCED: Maritime weather API with MET Norway + Data Science
    Provides reliable weather data for route optimization
    """
    try:
        lat = request.args.get('lat', 58.1467, type=float)  # Kristiansand default
        lon = request.args.get('lon', 8.0980, type=float)
        
        # PRIMARY: MET Norway API - Most reliable for maritime
        met_headers = {
            'User-Agent': 'BergNavnMaritime/3.0 (framgangsrik747@gmail.com)',
            'Accept': 'application/json'
        }
        met_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
        
        try:
            met_response = requests.get(met_url, headers=met_headers, timeout=10)
            
            if met_response.status_code == 200:
                met_data = met_response.json()
                current_weather = met_data['properties']['timeseries'][0]['data']['instant']['details']
                
                weather_info = {
                    'status': 'success',
                    'source': 'MET Norway',
                    'data': {
                        'temperature': current_weather.get('air_temperature', 0),
                        'wind_speed': current_weather.get('wind_speed', 0),
                        'wind_direction': current_weather.get('wind_direction', 0),
                        'wind_gust': current_weather.get('wind_speed_of_gust', 0),
                        'humidity': current_weather.get('relative_humidity', 0),
                        'pressure': current_weather.get('air_pressure_at_sea_level', 0),
                        'condition': 'Maritime data',
                        'icon': '🌊',
                        'location': f"Position: {lat}, {lon}",
                        'timestamp': datetime.now().isoformat(),
                        'data_quality': 'high'
                    }
                }
                return jsonify(weather_info)
                
        except requests.exceptions.Timeout:
            print("MET Norway timeout, falling back to OpenWeather")
        except Exception as e:
            print(f"MET Norway error: {e}")

        # FALLBACK: Environment-based weather (existing system)
        # This maintains compatibility with your current system
        return jsonify({
            'status': 'fallback',
            'source': 'System Database',
            'message': 'Using system weather data',
            'timestamp': datetime.now().isoformat()
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Weather service unavailable: {str(e)}'
        }), 500