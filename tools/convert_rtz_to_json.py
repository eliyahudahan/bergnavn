import os
import json
import xml.etree.ElementTree as ET

# Root folder to scan for extracted RTZs
base_dir = "backend/assets/routeinfo_routes"

for root, dirs, files in os.walk(base_dir):
    # Skip master *_routes.rtz files in "raw" folder
    if "extracted" not in root:
        continue
    
    for file in files:
        if file.endswith(".rtz"):
            file_path = os.path.join(root, file)
            try:
                tree = ET.parse(file_path)
                root_elem = tree.getroot()

                waypoints = []
                for wp in root_elem.findall(".//{*}waypoint"):
                    name = wp.attrib.get("name")
                    pos = wp.find("{*}position")
                    if pos is not None:
                        lat = float(pos.attrib.get("lat", 0))
                        lon = float(pos.attrib.get("lon", 0))
                        waypoints.append({
                            "name": name,
                            "latitude": lat,
                            "longitude": lon
                        })

                if waypoints:
                    output_path = file_path.replace(".rtz", ".json")
                    with open(output_path, "w", encoding="utf-8") as out_f:
                        json.dump(waypoints, out_f, indent=2, ensure_ascii=False)
                    print(f"✅ Parsed {len(waypoints)} waypoints → {output_path}")
                else:
                    print(f"⚠️ No waypoints found in {file_path}")

            except Exception as e:
                print(f"❌ Failed to parse {file_path}: {e}")
