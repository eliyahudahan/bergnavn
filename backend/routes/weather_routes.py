# backend/routes/weather_routes.py - UPDATED VERSION
"""
Weather Routes - API endpoints for weather data from MET Norway and OpenWeatherMap
Includes both dashboard display and JSON API endpoints.
"""

from flask import Blueprint, render_template, request, jsonify, session
from backend.models import WeatherStatus, Route
from sqlalchemy import desc, and_, func, text
from backend.extensions import db
from backend.utils.helpers import get_current_language
import requests
import os
from datetime import datetime

# Initialize blueprint - CHANGED FROM 'weather' TO 'weather_bp'
weather_bp = Blueprint('weather_bp', __name__, url_prefix='/weather')


@weather_bp.route('/')
def weather_dashboard():
    """
    Show latest active weather and active routes.
    
    Returns:
        Rendered template with weather and route data
    """
    # Subquery: latest record per port
    subquery = (
        db.session.query(
            WeatherStatus.port_id,
            func.max(WeatherStatus.datetime).label('max_dt')
        )
        .filter(WeatherStatus.is_active == True)
        .group_by(WeatherStatus.port_id)
        .subquery()
    )

    latest_statuses = (
        db.session.query(WeatherStatus)
        .join(
            subquery,
            and_(
                WeatherStatus.port_id == subquery.c.port_id,
                WeatherStatus.datetime == subquery.c.max_dt
            )
        )
        .all()
    )

    routes = (
        Route.query
        .filter(Route.is_active == True)
        .order_by(Route.id)
        .all()
    )

    for route in routes:
        route.legs.sort(key=lambda leg: leg.leg_order)

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
    MET Norway Maritime Weather API (with .env User-Agent)
    
    Returns:
        JSON response with current weather data
    """
    try:
        lat = request.args.get("lat", 58.1467, type=float)
        lon = request.args.get("lon", 8.0980, type=float)

        # Get User-Agent from environment variable
        met_user_agent = os.getenv("MET_USER_AGENT", "BergNavnMaritime/Default (contact@domain.com)")

        met_headers = {
            "User-Agent": met_user_agent,
            "Accept": "application/json"
        }

        url = (
            "https://api.met.no/weatherapi/locationforecast/2.0/compact"
            f"?lat={lat}&lon={lon}"
        )

        try:
            response = requests.get(url, headers=met_headers, timeout=8)

            if response.status_code == 200:
                data = response.json()
                instant = data['properties']['timeseries'][0]['data']['instant']['details']

                return jsonify({
                    "status": "success",
                    "source": "MET Norway",
                    "data": {
                        "temperature": instant.get("air_temperature", 0),
                        "wind_speed": instant.get("wind_speed", 0),
                        "wind_direction": instant.get("wind_direction", 0),
                        "wind_gust": instant.get("wind_speed_of_gust", 0),
                        "humidity": instant.get("relative_humidity", 0),
                        "pressure": instant.get("air_pressure_at_sea_level", 0),
                        "location": f"{lat}, {lon}",
                        "timestamp": datetime.now().isoformat(),
                        "data_quality": "high"
                    }
                })

        except Exception as met_err:
            print("⚠️ MET Norway unavailable → fallback used:", met_err)

        # Fallback if MET fails
        return jsonify({
            "status": "fallback",
            "source": "System DB",
            "message": "MET Norway unavailable – using internal system data",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@weather_bp.route('/api/forecast')
def get_weather_forecast():
    """
    Get weather forecast for multiple locations.
    
    Returns:
        JSON response with weather forecast data
    """
    try:
        locations = [
            {"name": "Bergen", "lat": 60.3913, "lon": 5.3221},
            {"name": "Oslo", "lat": 59.9139, "lon": 10.7522},
            {"name": "Stavanger", "lat": 58.9699, "lon": 5.7331},
            {"name": "Trondheim", "lat": 63.4305, "lon": 10.3951},
        ]
        
        forecast_data = []
        met_user_agent = os.getenv("MET_USER_AGENT", "BergNavnMaritime/Default")
        headers = {"User-Agent": met_user_agent}
        
        for location in locations[:2]:  # Limit to 2 locations to avoid rate limiting
            try:
                url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={location['lat']}&lon={location['lon']}"
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    instant = data['properties']['timeseries'][0]['data']['instant']['details']
                    
                    forecast_data.append({
                        "location": location["name"],
                        "temperature": instant.get("air_temperature", 0),
                        "wind_speed": instant.get("wind_speed", 0),
                        "wind_direction": instant.get("wind_direction", 0),
                        "updated": datetime.now().isoformat()
                    })
            except Exception as loc_error:
                print(f"Error fetching forecast for {location['name']}: {loc_error}")
                continue
        
        return jsonify({
            "status": "success",
            "forecast": forecast_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@weather_bp.route('/api/status')
def weather_service_status():
    """
    Check weather service status and configuration.
    
    Returns:
        JSON response with service status
    """
    try:
        met_configured = bool(os.getenv("MET_USER_AGENT"))
        openweather_configured = bool(os.getenv("OPENWEATHER_API_KEY"))
        
        # Test MET Norway connectivity
        met_working = False
        if met_configured:
            try:
                headers = {"User-Agent": os.getenv("MET_USER_AGENT")}
                response = requests.get(
                    "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.39&lon=5.32",
                    headers=headers,
                    timeout=5
                )
                met_working = response.status_code == 200
            except:
                met_working = False
        
        return jsonify({
            "status": "success",
            "configuration": {
                "met_norway_configured": met_configured,
                "openweather_configured": openweather_configured,
                "primary_source": "MET Norway" if met_configured else "OpenWeatherMap" if openweather_configured else "none"
            },
            "connectivity": {
                "met_norway_working": met_working,
                "overall_status": "operational" if (met_configured and met_working) or openweather_configured else "degraded"
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@weather_bp.route('/api/test')
def weather_test():
    """
    Simple test endpoint to verify weather API is working.
    
    Returns:
        JSON response with test status
    """
    try:
        return jsonify({
            "status": "success",
            "message": "Weather API is working",
            "endpoints": {
                "dashboard": "/weather/",
                "maritime_weather": "/weather/api/maritime-weather",
                "forecast": "/weather/api/forecast",
                "status": "/weather/api/status"
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500