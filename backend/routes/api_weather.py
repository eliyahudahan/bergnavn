# backend/routes/api_weather.py
# English-only comments.
from flask import Blueprint, jsonify, request
from backend.services.weather_service import get_best_weather

bp = Blueprint("api_weather_bp", __name__)

@bp.route("/weather-pro")
def weather_pro():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    w = get_best_weather(lat, lon)
    return jsonify(w)
