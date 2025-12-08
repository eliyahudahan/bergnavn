# backend/routes/maritime_routes.py
# English-only comments inside file as requested.
from flask import Blueprint, jsonify, request, render_template, current_app
from datetime import datetime
import logging
import math
import os
import requests
import asyncio

# services
from backend.services.fuel_optimizer_service import optimize_vessel_async
from backend.services.weather_service import get_best_weather
from backend.services.sea_depth_service import SeaDepthService

maritime_bp = Blueprint("maritime_bp", __name__)
logger = logging.getLogger(__name__)
_depth_service = SeaDepthService()

# ============================
# SAFE JSON RESPONSE (ENGLISH)
# ============================
def safe_response(data=None, message="", status="ok"):
    """Return consistent JSON payloads; never raise HTTP 500 from here."""
    return jsonify({
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "data": data or {},
        "message": message
    })

# ===========================================
# FRONTEND DASHBOARD ROUTE (fixes BuildError)
# ===========================================
@maritime_bp.route("/dashboard")
def maritime_dashboard():
    """
    Render the maritime dashboard page.
    This endpoint exists so url_for('maritime_bp.maritime_dashboard') works
    (base.html references this name).
    """
    lang = request.args.get("lang", "en")
    try:
        # prefer the split/dashboard template if present
        return render_template("maritime_split/dashboard_base.html", lang=lang)
    except Exception as e:
        logger.warning("[maritime_dashboard] template render failed: %s", e)
        # Fallback minimal page so app never 500s from missing template
        return (
            "<html><body><h1>Maritime Dashboard (fallback)</h1>"
            "<p>Template missing or render error — check templates.</p></body></html>",
            200,
        )

# ============================================
# WEATHER (HYBRID: MET Norway -> OpenWeather -> Empirical)
# ============================================
@maritime_bp.route("/api/weather-pro")
def get_weather():
    """
    Return consolidated weather data using MET Norway primary, then OpenWeather
    fallback, then empirical fallback (latitude+depth model).
    Always returns a safe JSON structure.
    Query params: lat, lon
    """
    try:
        lat = request.args.get("lat", type=float) or float(os.getenv("MET_LAT", 60.39))
        lon = request.args.get("lon", type=float) or float(os.getenv("MET_LON", 5.32))
        weather = get_best_weather(lat, lon)
        return safe_response(weather, status="success" if weather.get("source") != "empirical" else "fallback")
    except Exception:
        logger.exception("[get_weather] fallback")
        return safe_response({"message": "weather fallback"}, "weather fallback", "fallback")

# ============================================
# LIVE SHIPS (AIS) - SAFE REAL-TIME FEED
# ============================================
@maritime_bp.route("/api/ships-live")
def ships_live():
    """
    Return live ship positions.
    Uses attached ais_service if available; otherwise deterministic fallback.
    """
    try:
        app = current_app._get_current_object()
        ships = []
        try:
            ais_service = getattr(app, "ais_service", None)
            if ais_service and hasattr(ais_service, "get_recent_positions"):
                ships = ais_service.get_recent_positions()
        except Exception:
            logger.debug("[ships_live] ais_service present but failed to provide data", exc_info=True)
        if not ships:
            base_min = datetime.now().minute
            ships = [
                {
                    "mmsi": "257158400",
                    "name": "VICTORIA WILSON",
                    "type": "Cargo",
                    "lat": round(58.1467 + math.sin(base_min * 0.1) * 0.02, 6),
                    "lon": round(8.0980 + math.cos(base_min * 0.1) * 0.03, 6),
                    "sog": 12.5,
                    "cog": 45,
                    "heading": 50,
                    "destination": "OSLO",
                    "status": "Underway",
                    "timestamp": datetime.now().isoformat()
                }
            ]
        return safe_response({"ships": ships}, status="live")
    except Exception:
        logger.exception("[ships_live] fallback")
        return safe_response({"ships": []}, "ships fallback", "fallback")

# ============================================
# ETA (ENHANCED) - uses weather effects
# ============================================
@maritime_bp.route("/api/route/eta-enhanced")
def eta():
    """
    ETA calculation that considers simple weather impact.
    Query params: distance_nm, speed_knots, wind_speed (optional)
    """
    try:
        base_dist = float(request.args.get("distance_nm", 250))
        base_speed = float(request.args.get("speed_knots", 12.0))
        wind_speed = float(request.args.get("wind_speed", 0.0))
        wind_impact = 0.0
        if wind_speed > 10:
            wind_impact = 0.08
        elif wind_speed > 5:
            wind_impact = 0.03
        adjusted_speed = max(6.0, base_speed * (1.0 - wind_impact))
        eta_hours = round(base_dist / adjusted_speed, 2)
        return safe_response({
            "base_eta_hours": round(base_dist / base_speed, 2),
            "adjusted_eta_hours": eta_hours,
            "distance_nautical_miles": base_dist,
            "average_speed_knots": base_speed,
            "weather_impact_percent": round(wind_impact * 100, 1),
        }, status="success")
    except Exception:
        logger.exception("[eta] fallback")
        return safe_response({"eta_hours": 999}, "eta fallback", "fallback")

# ============================================
# ALERTS - simple operational alerts
# ============================================
@maritime_bp.route("/api/alerts")
def get_system_alerts():
    """
    Return system alerts derived from ships and weather.
    Always returns a JSON response with graceful fallback.
    """
    try:
        ships_resp = ships_live()
        ships = ships_resp.get_json().get("data", {}).get("ships", [])
        weather_resp = get_weather()
        weather = weather_resp.get_json().get("data", {})
        alerts = []
        wind_speed = (weather.get("wind_speed") or 0) or 0
        if wind_speed and wind_speed > 15:
            alerts.append({
                "type": "weather_alert",
                "priority": "high",
                "message": f"Strong winds: {wind_speed} m/s - consider shelter",
                "timestamp": datetime.now().isoformat()
            })
        for s in ships:
            sog = s.get("sog", 0) or 0
            if sog < 3:
                alerts.append({
                    "type": "operational_alert",
                    "priority": "low",
                    "ship": s.get("name"),
                    "message": f"Very low speed: {sog} knots",
                    "timestamp": datetime.now().isoformat()
                })
        return safe_response({"alerts": alerts}, status="success")
    except Exception:
        logger.exception("[get_system_alerts] fallback")
        return safe_response({"alerts": []}, "alerts fallback", "fallback")

# ====================================================
# FUEL OPTIMIZATION ANALYTICS - calls async optimizer
# ====================================================
@maritime_bp.route("/api/analytics/fuel-optimization", methods=["POST", "GET"])
def fuel_optimization():
    """
    Endpoint to run fuel optimization for a given vessel.
    Accepts POST JSON with keys: ais, weather
    If called with GET returns a small sample using defaults.
    """
    try:
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            ais = payload.get("ais", {})
            weather = payload.get("weather", {})
        else:
            ais = {"sog": 12.5, "displacement_tons": 8000}
            weather = {"wind_speed": 5, "wind_direction": 90}
        try:
            result = asyncio.run(optimize_vessel_async(ais, weather))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(optimize_vessel_async(ais, weather))
            finally:
                loop.close()
        return safe_response({"optimization": result}, status="success")
    except Exception:
        logger.exception("[fuel_optimization] fallback")
        fallback = {
            "status": "fallback",
            "optimization": {
                "status": "fallback",
                "current_speed_knots": ais.get("sog", 0) if 'ais' in locals() else 0,
                "optimal_speed_knots": ais.get("sog", 0) if 'ais' in locals() else 0,
                "fuel_tons_current": 0,
                "fuel_tons_optimal": 0,
                "fuel_saving_percent": 0,
                "timestamp": datetime.now().isoformat(),
                "fallback_used": True
            }
        }
        return safe_response(fallback, "optimization fallback", "fallback")
