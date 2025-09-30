# tools/verify_rtz_json.py
# Script to check all converted RTZ JSON files in the project
# Validates JSON, required fields, and optional fields
# DOES NOT MODIFY FILES — only prints suggestions/warnings

import os
import json

# Root folder for converted RTZ JSON files
RTZ_JSON_ROOT = "backend/assets/routeinfo_routes/rtz_json"

# Expected fields for RTZ JSON
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

for file in os.listdir(RTZ_JSON_ROOT):
    if file.endswith(".json"):
        filepath = os.path.join(RTZ_JSON_ROOT, file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ {filepath} – invalid JSON: {e}")
            continue

        missing_required = [field for field in REQUIRED_FIELDS if field not in data]
        if missing_required:
            print(f"⚠️ {filepath} – missing required fields: {missing_required}")

        missing_optional = [field for field in OPTIONAL_FIELDS if field not in data]
        for field in missing_optional:
            print(f"⚠️ {filepath} – missing optional field: {field}")

        if not missing_required and not missing_optional:
            print(f"✅ {filepath} – valid JSON with all recommended fields")
