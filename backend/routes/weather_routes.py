# backend/routes/weather_routes.py - FINAL FIX
from flask import Blueprint, render_template, request, jsonify
from backend.models import WeatherStatus, Route
from sqlalchemy import desc, and_, func
from backend.extensions import db
from backend.utils.helpers import get_current_language
import requests
import os
from datetime import datetime

weather_bp = Blueprint('weather', __name__, url_prefix='/weather')


@weather_bp.route('/')
def weather_dashboard():
    """Show latest active weather and active routes."""
    
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
    """

    try:
        lat = request.args.get("lat", 58.1467, type=float)
        lon = request.args.get("lon", 8.0980, type=float)

        # --- FINAL FIX: GET USER-AGENT FROM .env ---
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
