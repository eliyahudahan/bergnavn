# patch_rtz_json.py
# Adds optional fields with default values to all RTZ JSON files
# in backend/assets/routeinfo_routes/rtz_json/

import os
import json

RTZ_JSON_ROOT = "backend/assets/routeinfo_routes/rtz_json"

# Default values for missing optional fields
defaults = {
    "description": "No description provided",
    "related_ports": [],
    "accessibility": "unknown",
    "family_suitability": "unknown",
    "difficulty": "unknown",
    "last_verified": None,
    "source": "user-entry",
    "operational_status": "ACTIVE",
    "nav_points": [],
    "sunrise_local": None,
    "sunset_local": None
}

for file_name in os.listdir(RTZ_JSON_ROOT):
    if file_name.endswith(".json"):
        path = os.path.join(RTZ_JSON_ROOT, file_name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Patch missing keys
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Patched:", path)
