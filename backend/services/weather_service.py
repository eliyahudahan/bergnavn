# backend/services/weather_service.py
"""
Weather service that prefers MET Norway (primary) and falls back to OpenWeatherMap.
Provides:
 - get_weather_for_coord(lat, lon) -> dict
 - sync_ports_weather() -> writes WeatherStatus records (if app context)
Notes:
 - MET Norway (api.met.no) requires a User-Agent header and polite usage. Provide user agent in env:
    MET_USER_AGENT
 - OpenWeather uses API key in env: OPENWEATHER_API_KEY
"""

import os
import requests
from typing import Dict, Any, Optional

MET_USER_AGENT = os.getenv("MET_USER_AGENT", "BergNavnApp/1.0 (contact: framgangsrik747@gmail.com)")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "")

def _fetch_met_weather(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Query MET Norway (locationforecast/2.0). This is the recommended primary source in Norway.
    """
    try:
        url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
        headers = {"User-Agent": MET_USER_AGENT}
        params = {"lat": lat, "lon": lon}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None

def _fetch_openweather(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Fallback to OpenWeather (current weather)."""
    if not OPENWEATHER_KEY:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_KEY, "units": "metric"}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None

def get_weather_for_coord(lat: float, lon: float) -> Dict[str, Any]:
    """Return a normalized weather payload using MET Norway primary, OpenWeather fallback."""
    payload = _fetch_met_weather(lat, lon)
    if payload:
        return {"source": "met", "data": payload}
    payload = _fetch_openweather(lat, lon)
    if payload:
        return {"source": "openweather", "data": payload}
    return {"source": "none", "data": {}}
