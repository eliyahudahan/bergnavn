# tools/convert_and_patch_rtz.py
# Converts all .rtz (ZIP/XML) route files in subfolders into structured JSON
# Extracts valid coordinates and metadata for each port route
# Non-destructive — existing JSON files are backed up if present
# Only writes JSON if at least one waypoint is found

import os
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

RAW_ROOT = "backend/assets/routeinfo_routes"
JSON_ROOT = os.path.join(RAW_ROOT, "rtz_json")
os.makedirs(JSON_ROOT, exist_ok=True)

DEFAULTS = {
    "coordinates_approximate": True,
    "operational_status": "ACTIVE",
    "nav_points": [],
    "family_suitability": "unknown",
    "difficulty": "unknown",
    "last_verified": None,
    "source": "routeinfo.no",
    "sunrise_local": None,
    "sunset_local": None,
    "description": "Imported from RTZ file",
    "related_ports": [],
    "accessibility": "unknown"
}


def extract_rtz_to_xml(rtz_path):
    """Extracts .xml content from inside .rtz ZIP archive."""
    try:
        with zipfile.ZipFile(rtz_path, "r") as zip_ref:
            for name in zip_ref.namelist():
                if name.endswith(".xml"):
                    with zip_ref.open(name) as xml_file:
                        return xml_file.read().decode("utf-8")
        print(f"⚠️ No XML found in {rtz_path}")
        return None
    except zipfile.BadZipFile:
        print(f"❌ Not a valid ZIP (RTZ) file: {rtz_path}")
        return None


def parse_rtz_xml(xml_content):
    """Parses XML and extracts route name + waypoints."""
    try:
        root = ET.fromstring(xml_content)
        ns = {"rtz": "https://cirm.org/rtz-xml-schemas"}

        route_info = root.find("rtz:routeInfo", ns)
        route_name = route_info.attrib.get("routeName", "Unknown Route") if route_info is not None else "Unnamed"

        waypoints = []
        for wp in root.findall("rtz:waypoints/rtz:waypoint", ns):
            pos = wp.find("rtz:position", ns)
            if pos is not None:
                try:
                    lat = float(pos.attrib.get("lat", "0"))
                    lon = float(pos.attrib.get("lon", "0"))
                except ValueError:
                    continue  # skip invalid coordinates
                name = wp.attrib.get("name", "Unnamed")
                waypoints.append({
                    "name": name,
                    "coordinates": [lat, lon]
                })
        return route_name, waypoints

    except ET.ParseError as e:
        print(f"❌ XML parse error: {e}")
        return "Invalid", []


def convert_rtz_file(rtz_path, json_path):
    """Converts one .rtz file into a structured JSON."""
    xml_content = extract_rtz_to_xml(rtz_path)
    if not xml_content:
        return False

    route_name, waypoints = parse_rtz_xml(xml_content)

    if not waypoints:
        print(f"⚠️ Skipping {os.path.basename(rtz_path)} — no valid waypoints")
        return False

    data = {
        "name": route_name,
        "category": "harbor",
        "coordinates": waypoints[0]["coordinates"],
        "nav_points": [wp["coordinates"] for wp in waypoints]
    }

    # Add defaults
    for k, v in DEFAULTS.items():
        if k not in data:
            data[k] = v

    # Backup old JSON if exists
    if os.path.exists(json_path):
        backup_path = json_path.replace(".json", f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak.json")
        os.rename(json_path, backup_path)
        print(f"🗂️ Backed up existing JSON to {backup_path}")

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Converted {os.path.basename(rtz_path)} → {os.path.basename(json_path)} ({len(waypoints)} waypoints)")
        return True
    except Exception as e:
        print(f"❌ Failed to write {json_path}: {e}")
        return False


# Walk recursively through backend/assets/routeinfo_routes
for subdir, _, files in os.walk(RAW_ROOT):
    for file in files:
        if file.endswith(".rtz"):
            rtz_path = os.path.join(subdir, file)
            json_filename = os.path.splitext(file)[0] + ".json"
            json_path = os.path.join(JSON_ROOT, json_filename)
            convert_rtz_file(rtz_path, json_path)
