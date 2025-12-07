# scripts/download_weather_history.py
# Fetch hourly MET forecast time series and store as CSV.
import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

LAT = os.getenv("MET_LAT")
LON = os.getenv("MET_LON")
USER_AGENT = os.getenv("MET_USER_AGENT")

URL = (
    f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
    f"?lat={LAT}&lon={LON}"
)

HEADERS = {
    "User-Agent": USER_AGENT,
}

def fetch_met_forecast():
    """Download MET forecast hourly temperatures"""
    print("⏳ Fetching MET data...")

    r = requests.get(URL, headers=HEADERS)
    if r.status_code != 200:
        raise RuntimeError(f"MET API Error: {r.status_code}")

    data = r.json()

    timeseries = data.get("properties", {}).get("timeseries", [])
    if not timeseries:
        raise RuntimeError("❌ MET returned no time series data")

    records = []

    for entry in timeseries:
        time = entry.get("time")
        details = entry.get("data", {}).get("instant", {}).get("details", {})
        temp = details.get("air_temperature")

        if temp is not None:
            records.append({"time": time, "temp": temp})

    if not records:
        raise RuntimeError("❌ No usable temperature records found")

    df = pd.DataFrame(records)
    df.to_csv("data/weather_history.csv", index=False)
    print("✅ Saved data/weather_history.csv")

if __name__ == "__main__":
    fetch_met_forecast()
