# backend/services/weather_service.py
# MET raw weather service
import os
import requests
from dotenv import load_dotenv

load_dotenv()

LAT = os.getenv("MET_LAT")
LON = os.getenv("MET_LON")
USER_AGENT = os.getenv("MET_USER_AGENT")

URL = (
    f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
    f"?lat={LAT}&lon={LON}"
)

HEADERS = {"User-Agent": USER_AGENT}

def get_met_current_weather():
    """Return current MET air temperature"""
    r = requests.get(URL, headers=HEADERS)
    if r.status_code != 200:
        return {"error": f"MET HTTP {r.status_code}"}

    data = r.json()
    ts = data.get("properties", {}).get("timeseries", [])

    if not ts:
        return {"error": "No MET data"}

    first = ts[0]  # closest time block
    details = first["data"]["instant"]["details"]

    return {
        "time": first["time"],
        "temp": details.get("air_temperature"),
    }
