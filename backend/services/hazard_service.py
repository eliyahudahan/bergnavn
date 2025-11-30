# backend/services/hazard_service.py
"""
Hazard collection service:
- combines OpenInfraMap (windfarm footprints via OSM), OSM layers (TSS, fairways), and local hazard_zones table.
- This module only queries public open data (OSM / OpenInfraMap) and uses PostGIS to store polygons.
Notes:
 - Do NOT rely on this as an authoritative source for legal navigation decisions.
 - Use as a supplemental hazard overlay.
"""

import requests
import os
from typing import List, Dict, Any

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# OpenInfraMap provides tiles and separate datasets but for simplicity we'll query OSM tags (wind_turbine, offshore_windfarm)
def query_osm_hazards(bbox: List[float]) -> List[Dict[str, Any]]:
    """Query OSM for hazards inside bbox = [minlat, minlon, maxlat, maxlon]"""
    minlat, minlon, maxlat, maxlon = bbox
    # Example Overpass query: nodes and ways tagged as wind turbines, and maritime features
    q = f"""
    [out:json][timeout:25];
    (
      node["man_made"="windmill"]({minlat},{minlon},{maxlat},{maxlon});
      node["power"="wind_turbine"]({minlat},{minlon},{maxlat},{maxlon});
      way["separation"="traffic_separation_scheme"]({minlat},{minlon},{maxlat},{maxlon});
      way["fairway"]({minlat},{minlon},{maxlat},{maxlon});
    );
    out body;
    >;
    out skel qt;
    """
    r = requests.post(OVERPASS_URL, data=q, timeout=30)
    if r.status_code == 200:
        return r.json().get("elements", [])
    return []
