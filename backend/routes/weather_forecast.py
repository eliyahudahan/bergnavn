from flask import Blueprint, jsonify
import numpy as np
import joblib
import os

weather_forecast_bp = Blueprint("weather_forecast", __name__)

MODEL_PATH = "models/weather_lstm.h5"
SCALER_PATH = "models/weather_scaler.pkl"

@weather_forecast_bp.route("/maritime/api/weather-forecast")
def weather_forecast():

    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return jsonify({"error": "Forecast model not found"}), 500

    from keras.models import load_model
    model = load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    # dummy last window (בפועל אתה תיקח מה-MET, לא חשוב כרגע)
    last_window = np.zeros((1, 24, 3))  # temp, wind, gust
    forecast_scaled = model.predict(last_window)
    forecast = scaler.inverse_transform(forecast_scaled)[0]

    result = []
    lat, lon = 60.0, 5.0  

    for i, temp in enumerate(forecast):
        result.append({
            "hour": i,
            "lat": lat,
            "lon": lon,
            "temp": float(temp[0]),
        })

    return jsonify(result), 200
