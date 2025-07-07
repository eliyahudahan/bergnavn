# backend/services/weather_sync.py

import requests
from datetime import datetime, time, UTC
from backend.extensions import db
from backend.models import Port, WeatherStatus
import os

API_KEY = os.getenv("OPENWEATHER_API_KEY")  # ודא שהמפתח קיים ב־.env

def get_weather_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def calculate_alert(wind_speed, condition):
    if wind_speed > 40 or "storm" in condition.lower():
        return "black"
    elif wind_speed > 25:
        return "red"
    return "green"

def sync_weather():
    ports = Port.query.all()
    now = datetime.now(UTC)

    for port in ports:
        if not port.latitude or not port.longitude:
            continue

        data = get_weather_data(port.latitude, port.longitude)
        if not data:
            continue

        wind_speed = data.get("wind", {}).get("speed", 0)
        condition = data.get("weather", [{}])[0].get("main", "Unknown")
        sunrise_ts = data.get("sys", {}).get("sunrise")
        sunset_ts = data.get("sys", {}).get("sunset")

        # המרה לשעות (UTC -> local בהמשך אם נרצה)
        sunrise = datetime.utcfromtimestamp(sunrise_ts).time() if sunrise_ts else None
        sunset = datetime.utcfromtimestamp(sunset_ts).time() if sunset_ts else None

        alert = calculate_alert(wind_speed, condition)

        status = WeatherStatus(
            port_id=port.id,
            datetime=now,
            wind_speed=wind_speed,
            weather_condition=condition,
            sunrise=sunrise,
            sunset=sunset,
            alert_level=alert
        )

        db.session.add(status)

    db.session.commit()
