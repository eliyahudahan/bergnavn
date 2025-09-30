# tools/patch_waypoint.py
import json, sys, os
from datetime import datetime

if len(sys.argv) < 2:
    print("Usage: python tools/patch_waypoint.py <path-to-json>")
    sys.exit(1)

path = sys.argv[1]
if not os.path.exists(path):
    print("❌ File does not exist:", path)
    sys.exit(1)

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# default values to ensure schema
defaults = {
  "coordinates_approximate": True,
  "operational_status": "ACTIVE",
  "nav_points": [],
  "family_suitability": "unknown",
  "difficulty": "unknown",
  "last_verified": None,
  "source": "user-entry",
  "sunrise_local": None,
  "sunset_local": None
}

for k,v in defaults.items():
    if k not in data:
        data[k] = v

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Patched:", path)
