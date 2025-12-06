# system_check.py
# Quick diagnostic script for BergNavn Maritime stack

import os
import requests

BASE_URL = "http://127.0.0.1:5000/maritime/api"

ENDPOINTS = [
    "weather-pro",
    "ships-live",
    "analytics/fuel-optimization",
    "route/eta-enhanced",
    "alerts",
]

ROUTE_DIR = "backend/assets/routeinfo_routes"

def check_endpoint(name):
    """Test an API endpoint and return status code."""
    url = f"{BASE_URL}/{name}"
    try:
        r = requests.get(url, timeout=3)
        return r.status_code
    except Exception as e:
        return f"ERR ({e})"


def check_routes():
    """Count route files and detect malformed ones."""
    total = 0
    corrupted = 0
    for root, dirs, files in os.walk(ROUTE_DIR):
        for f in files:
            if f.lower().endswith((".rtz", ".xml", ".json", ".txt")):
                total += 1
                full = os.path.join(root, f)
                try:
                    with open(full, "r", encoding="utf-8") as fp:
                        fp.read()
                except:
                    corrupted += 1
    return total, corrupted


if __name__ == "__main__":
    print("=== BergNavn Maritime System Check ===")

    print("\n--- Checking API Endpoints ---")
    for ep in ENDPOINTS:
        status = check_endpoint(ep)
        print(f"  {ep:30} -> {status}")

    print("\n--- Checking Route Files ---")
    total, corrupted = check_routes()
    print(f"  Total route files: {total}")
    print(f"  Corrupted files:   {corrupted}")

    print("\n--- Summary ---")

    if corrupted == 0:
        print("  ✓ All route files valid")
    else:
        print("  ⚠ Some route files corrupted")

    if any(str(check_endpoint(ep)).startswith("5") for ep in ENDPOINTS):
        print("  ⚠ One or more API endpoints returned 500")
    else:
        print("  ✓ All tested API endpoints responded normally")

    print("\n=== Done ===")
