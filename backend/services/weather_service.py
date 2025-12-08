# backend/services/weather_service.py
# Unified weather data service (MET → OpenWeather → Empirical fallback)
import os
import requests
from dotenv import load_dotenv
from statistics import mean

load_dotenv()

# MET Norway configuration
LAT = os.getenv("MET_LAT")
LON = os.getenv("MET_LON")
USER_AGENT = os.getenv("MET_USER_AGENT")

MET_URL = (
    f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
    f"?lat={LAT}&lon={LON}"
)
MET_HEADERS = {"User-Agent": USER_AGENT}

# OpenWeather configuration
OW_KEY = os.getenv("OPENWEATHER_KEY")
OW_URL = (
    f"https://api.openweathermap.org/data/2.5/weather"
    f"?lat={LAT}&lon={LON}&appid={OW_KEY}&units=metric"
)


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def get_weather():
    """
    Original unified weather fallback:
    1. MET Norway
    2. OpenWeather
    3. Empirical fallback
    """
    met = _get_met()
    if met and "error" not in met:
        return {"source": "met", **met}

    ow = _get_openweather()
    if ow and "error" not in ow:
        return {"source": "openweather", **ow}

    emp = _empirical_fallback()
    return {"source": "empirical_fallback", **emp}


def get_best_weather():
    """
    Alias wrapper for backward compatibility.
    Used by maritime_routes.py
    """
    return get_weather()


# ============================================================================
# MET Norway API
# ============================================================================

def _get_met():
    try:
        r = requests.get(MET_URL, headers=MET_HEADERS, timeout=5)
        if r.status_code != 200:
            return {"error": f"MET HTTP {r.status_code}"}

        data = r.json()
        ts = data.get("properties", {}).get("timeseries", [])
        if not ts:
            return {"error": "No MET data"}

        first = ts[0]
        details = first["data"]["instant"]["details"]

        return {
            "time": first["time"],
            "temp": details.get("air_temperature"),
            "wind": details.get("wind_speed"),
            "gust": details.get("wind_speed_of_gust"),
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# OpenWeather API
# ============================================================================

def _get_openweather():
    if not OW_KEY:
        return {"error": "No OpenWeather key"}

    try:
        r = requests.get(OW_URL, timeout=5)
        if r.status_code != 200:
            return {"error": f"OW HTTP {r.status_code}"}

        d = r.json()
        return {
            "time": d.get("dt"),
            "temp": d.get("main", {}).get("temp"),
            "wind": d.get("wind", {}).get("speed"),
            "gust": d.get("wind", {}).get("gust"),
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Empirical fallback (historical CSV)
# ============================================================================

def _empirical_fallback():
    import pandas as pd
    try:
        df = pd.read_csv("data/weather_history.csv")
        temps = df["temp"].astype(float).values

        avg_temp = round(mean(temps[-72:]), 2) if len(temps) >= 72 else mean(temps)

        return {
            "time": None,
            "temp": avg_temp,
            "wind": 3.1,
            "gust": 5.8
        }
    except Exception:
        return {
            "time": None,
            "temp": 8.0,
            "wind": 3.1,
            "gust": 5.8
        }
