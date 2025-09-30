# tools/convert_and_patch_rtz.py
# Converts all .rtz files in subfolders to JSON and applies waypoint defaults
# Works recursively for multiple cities
import os, json
from datetime import datetime

# Folder containing raw .rtz files (input)
RAW_ROOT = "backend/assets/routeinfo_routes"
# Folder to output patched JSON files
JSON_ROOT = os.path.join(RAW_ROOT, "rtz_json")

# Ensure output folder exists
os.makedirs(JSON_ROOT, exist_ok=True)

# Default fields for patching
DEFAULTS = {
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

def convert_rtz_file(rtz_path, json_path):
    """Converts a single .rtz file to JSON."""
    try:
        with open(rtz_path, 'r', encoding='utf-8', errors='ignore') as f:
            nav_points = []
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                        nav_points.append([lat, lon])
                    except ValueError:
                        continue
    except Exception as e:
        print(f"❌ Failed to read {rtz_path}: {e}")
        return False

    data = {
        "name": os.path.splitext(os.path.basename(rtz_path))[0],
        "category": "harbor",
        "coordinates": nav_points[0] if nav_points else [0.0, 0.0],
        "nav_points": nav_points
    }
    # Apply defaults for missing fields
    for k, v in DEFAULTS.items():
        if k not in data:
            data[k] = v

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Converted {rtz_path} → {json_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to write {json_path}: {e}")
        return False

# Walk recursively through RAW_ROOT
for subdir, dirs, files in os.walk(RAW_ROOT):
    for file in files:
        if file.endswith(".rtz"):
            rtz_path = os.path.join(subdir, file)
            json_filename = os.path.splitext(file)[0] + ".json"
            json_path = os.path.join(JSON_ROOT, json_filename)
            convert_rtz_file(rtz_path, json_path)
