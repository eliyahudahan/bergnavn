# backend/services/weather_service.py
# English-only comments inside file.

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from math import radians, cos, sin, asin, sqrt

#############################################
# Ensure .env is always loaded BEFORE config
#############################################
# Force re-load .env regardless of import order
load_dotenv(override=True)

# Debug print (appears once at startup only)
print("🌤 MET_USER_AGENT Loaded =", os.getenv("MET_USER_AGENT"))

# --- MET configuration ---
MET_USER_AGENT = os.getenv("MET_USER_AGENT", "BergNavnMaritime/DefaultUA")
DEFAULT_LAT = float(os.getenv("MET_LAT", 60.39))
DEFAULT_LON = float(os.getenv("MET_LON", 5.32))

MET_BASE = "https://api.met.no/weatherapi/locationforecast/2.0/compact"


##############################
# City empirical fallback
##############################
_CITY_STATS = {
    "bergen": {
        "latlon": (60.39, 5.32),
        "type": "fjord/coastal",
        "temp_avg": 6.0, "wind_avg": 6.2, "wave_avg": 2.0,
        "confidence": "medium"
    },
    "oslo": {
        "latlon": (59.91, 10.75),
        "type": "fjord/sheltered",
        "temp_avg": 7.0, "wind_avg": 4.5, "wave_avg": 0.8,
        "confidence": "medium"
    },
    "stavanger": {
        "latlon": (58.97, 5.73),
        "type": "coastal",
        "temp_avg": 7.0, "wind_avg": 5.5, "wave_avg": 1.5,
        "confidence": "medium"
    },
    "trondheim": {
        "latlon": (63.43, 10.40),
        "type": "coastal/deeper",
        "temp_avg": 4.0, "wind_avg": 6.8, "wave_avg": 2.2,
        "confidence": "medium"
    }
}


#########################
# Helpers
#########################
def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def _nearest_city(lat, lon):
    best = None
    best_dist = 1e9
    for c, info in _CITY_STATS.items():
        clat, clon = info["latlon"]
        d = _haversine_km(lat, lon, clat, clon)
        if d < best_dist:
            best_dist = d
            best = c
    return best, best_dist


#########################
# MET Norway fetch
#########################
def _fetch_met(lat, lon, timeout=5):

    headers = {"User-Agent": MET_USER_AGENT}
    params = {"lat": lat, "lon": lon}

    try:
        r = requests.get(MET_BASE, params=params, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return {"error": f"MET HTTP {r.status_code}"}

        payload = r.json()
        ts = payload.get("properties", {}).get("timeseries", [])
        if not ts:
            return {"error": "MET no timeseries"}

        first = ts[0]
        inst = first.get("data", {}).get("instant", {}).get("details", {})
        next_1h = first.get("data", {}).get("next_1_hours", {}) or {}
        precip = next_1h.get("summary", {}).get("symbol_code")

        return {
            "time": first.get("time"),
            "temperature": inst.get("air_temperature"),
            "wind_speed": inst.get("wind_speed"),
            "wind_dir": inst.get("wind_from_direction"),
            "pressure": inst.get("air_pressure_at_sea_level"),
            "humidity": inst.get("relative_humidity"),
            "precip_symbol": precip,
            "source": "met_norway_live",
            "confidence": "high",
        }

    except Exception as e:
        return {"error": str(e)}


#########################
# Empirical fallback
#########################
def _empirical_fallback(lat, lon):
    city, dist = _nearest_city(lat, lon)
    s = _CITY_STATS[city]

    return {
        "time": datetime.utcnow().isoformat(),
        "temperature": s["temp_avg"],
        "wind_speed": s["wind_avg"],
        "wave_height": s["wave_avg"],
        "wind_dir": None,
        "pressure": None,
        "humidity": None,
        "source": "empirical_historical",
        "city": city,
        "confidence": s["confidence"],
        "notes": f"empirical_nearest_city={city}, dist_km={round(dist,1)}"
    }


#########################
# Public function
#########################
def get_best_weather(lat=None, lon=None):

    if lat is None: lat = DEFAULT_LAT
    if lon is None: lon = DEFAULT_LON

    # 1) Try MET
    met = _fetch_met(lat, lon)
    if met and "error" not in met:
        city, _ = _nearest_city(lat, lon)
        met["city"] = city
        return met

    # 2) Fallback
    return _empirical_fallback(lat, lon)
