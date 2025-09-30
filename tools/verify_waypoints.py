# tools/verify_waypoints.py
# Script to check all waypoint JSON files in the project
# Validates JSON, required fields, and notes missing info or approximate coordinates
# DOES NOT MODIFY FILES — only prints suggestions and warnings

import os
import json

# Root folder for waypoints relative to project root
WAYPOINTS_ROOT = "backend/assets/routeinfo_routes/waypoints"

# Expected fields
REQUIRED_FIELDS = ["name", "category", "coordinates"]
OPTIONAL_FIELDS = [
    "coordinates_approximate",
    "description",
    "related_ports",
    "accessibility",
    "family_suitability",
    "difficulty",
    "last_verified",
    "source",
    "operational_status",
    "nav_points",
    "sunrise_local",
    "sunset_local"
]

def check_waypoints():
    all_ok = True
    for subdir, _, files in os.walk(WAYPOINTS_ROOT):
        for file in files:
            if file.endswith(".json"):
                filepath = os.path.join(subdir, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"❌ {filepath} – invalid JSON: {e}")
                    all_ok = False
                    continue

                # Check required fields
                missing_required = [field for field in REQUIRED_FIELDS if field not in data]
                if missing_required:
                    print(f"⚠️ {filepath} – missing required fields: {missing_required}")
                    all_ok = False

                # Check optional fields and give guidance
                for field in OPTIONAL_FIELDS:
                    if field not in data:
                        print(f"⚠️ {filepath} – missing optional field: {field}")
                        all_ok = False

                if not missing_required and all(field in data for field in OPTIONAL_FIELDS):
                    print(f"✅ {filepath} – valid JSON with all recommended fields")
    return all_ok

if __name__ == "__main__":
    ok = check_waypoints()
    if not ok:
        exit(1)
