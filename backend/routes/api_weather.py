# backend/routes/api_weather.py
from flask import Blueprint, jsonify
from backend.services.weather_service import get_met_current_weather
from backend.services.weather_dl import predict_next_temperature

weather_bp = Blueprint("weather_bp", __name__)

@weather_bp.route("/weather-pro")
def weather_pro():
    """Return MET current + DL predicted temperature"""
    current = get_met_current_weather()

    try:
        predicted = predict_next_temperature()
    except Exception:
        predicted = None

    return jsonify({
        "current": current,
        "predicted_temp": predicted
    })
