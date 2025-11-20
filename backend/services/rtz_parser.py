#!/usr/bin/env python3
"""
rtz_parser.py
Lightweight, defensive RTZ -> JSON parser.
- Attempts to parse common XML RTZ structures (route / leg / waypoint)
- Falls back to extracting lat,lon pairs via regex
- Computes distance in nautical miles per leg (haversine)
- Writes decoded JSON to a `decoded/` sibling folder

Usage:
  python backend/services/rtz_parser.py path/to/oslo_routes.rtz
"""
import os
import sys
import json
import math
import logging
import re
from datetime import datetime
from xml.etree import ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rtz_parser")

COORD_RE = re.compile(r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)')

def strip_ns(tag: str) -> str:
    return tag.split('}')[-1] if '}' in tag else tag

def haversine_nm(lat1, lon1, lat2, lon2):
    # returns nautical miles between two points
    R_km = 6371.0
    lat1r = math.radians(lat1)
    lat2r = math.radians(lat2)
    dlat = lat2r - lat1r
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1r)*math.cos(lat2r)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    dist_km = R_km * c
    return dist_km * 0.539956803  # km -> nautical miles

def find_coord_attrs(elem):
    # look for attributes named lat/lon variants
    lat = None; lon = None
    for key, val in elem.attrib.items():
        k = key.lower()
        if 'lat' in k and lat is None:
            lat = float(val)
        if 'lon' in k or 'lng' in k:
            lon = float(val)
    return lat, lon

def extract_coords_from_text(text):
    if not text:
        return []
    return [(float(m[0]), float(m[1])) for m in COORD_RE.findall(text)]

def parse_waypoint(elem):
    # try attributes
    lat, lon = find_coord_attrs(elem)
    name = elem.attrib.get('name') or elem.attrib.get('id') or None
    # try child tags
    if lat is None or lon is None:
        # look for children like lat/lon/latitude/longitude or position
        for child in elem:
            t = strip_ns(child.tag).lower()
            if 'lat' in t and lat is None:
                try:
                    lat = float((child.text or '').strip())
                except:
                    pass
            if 'lon' in t and lon is None:
                try:
                    lon = float((child.text or '').strip())
                except:
                    pass
            if 'position' in t and (lat is None or lon is None):
                # attempt to parse coordinates in position text
                pts = extract_coords_from_text(child.text)
                if pts:
                    lat, lon = pts[0][0], pts[0][1]
    # last resort: search full element text
    if lat is None or lon is None:
        pts = extract_coords_from_text(ET.tostring(elem, encoding='unicode', method='text'))
        if pts:
            lat, lon = pts[0][0], pts[0][1]
    if lat is None or lon is None:
        return None
    return {'name': name, 'lat': lat, 'lon': lon}

def parse_rtz(path):
    """
    Parse RTZ file and extract route information.
    
    Args:
        path: Path to the RTZ file
        
    Returns:
        List of route dictionaries with name and waypoints
        Returns empty list if file not found or parsing fails
    """
    logger.info("Parsing RTZ file: %s", path)
    
    # Check if file exists before attempting to parse
    if not os.path.exists(path):
        logger.warning(f"RTZ file not found: {path}")
        return []
    
    try:
        tree = ET.parse(path)
        root = tree.getroot()

        routes_data = []
        # try to find route elements
        route_elems = [e for e in root.iter() if 'route' in strip_ns(e.tag).lower() or 'rte' in strip_ns(e.tag).lower()]
        # if none found, try to find top-level 'gpx'/'trk' or collect waypoint lists
        if not route_elems:
            # collect top-level tracks or create synthetic route from waypoints
            # search for trk or gpx or rtept or wpt
            candidates = [e for e in root.iter() if strip_ns(e.tag).lower() in ('trk', 'gpx', 'rte', 'track')]
            if candidates:
                route_elems = candidates
            else:
                # fallback: treat whole file as a single route
                route_elems = [root]

        route_index = 0
        for r in route_elems:
            route_index += 1
            rtag = strip_ns(r.tag).lower()
            route_name = r.attrib.get('name') or r.findtext('name') or f'route_{route_index}'
            # gather waypoints under this route
            waypoints = []
            # common waypoint tags
            for wp_tag in ('waypoint', 'wpt', 'rtept', 'pt', 'trkpt', 'position'):
                for wp in r.findall('.//{}'.format(wp_tag)):
                    p = parse_waypoint(wp)
                    if p:
                        waypoints.append(p)
            # If none found using common tags, search all descendants for coordinate patterns
            if not waypoints:
                coords = []
                for elem in r.iter():
                    pts = extract_coords_from_text(ET.tostring(elem, encoding='unicode', method='text'))
                    for lat, lon in pts:
                        coords.append({'name': None, 'lat': lat, 'lon': lon})
                waypoints = coords

            # If still no coords, attempt global search in file
            if not waypoints:
                pts = extract_coords_from_text(ET.tostring(root, encoding='unicode', method='text'))
                waypoints = [{'name': None, 'lat': p[0], 'lon': p[1]} for p in pts]

            # build legs: consecutive waypoints -> 1 leg per pair
            legs = []
            total_route_nm = 0.0
            for i in range(len(waypoints) - 1):
                a = waypoints[i]; b = waypoints[i+1]
                dist_nm = haversine_nm(a['lat'], a['lon'], b['lat'], b['lon'])
                legs.append({
                    'leg_order': i+1,
                    'start': a,
                    'end': b,
                    'distance_nm': round(dist_nm, 3)
                })
                total_route_nm += dist_nm

            route_obj = {
                'route_name': route_name,
                'num_waypoints': len(waypoints),
                'total_distance_nm': round(total_route_nm, 3),
                'legs': legs,
                'parsed_at_utc': datetime.utcnow().isoformat() + 'Z',
                'source_file': os.path.abspath(path)
            }
            routes_data.append(route_obj)

        return routes_data
        
    except ET.ParseError as e:
        logger.error(f"XML parsing error in {path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing {path}: {e}")
        return []

def write_decoded_json(routes_data, src_path):
    decoded_dir = os.path.join(os.path.dirname(src_path), '..', 'decoded')
    decoded_dir = os.path.abspath(decoded_dir)
    os.makedirs(decoded_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src_path))[0]
    out_path = os.path.join(decoded_dir, f"{base}_decoded.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'routes': routes_data}, f, indent=2, ensure_ascii=False)
    logger.info("Wrote decoded JSON to %s", out_path)
    return out_path

# Placeholder: implement DB save using your SQLAlchemy models
def save_to_db_placeholder(routes_data):
    logger.info("save_to_db_placeholder called (%d routes) - implement your DB integration here", len(routes_data))
    # Example:
    # from backend.models.route import Route, VoyageLeg
    # session = get_db_session()
    # create Route + legs
    pass

def main(argv):
    if len(argv) < 2:
        print("Usage: rtz_parser.py path/to/file.rtz [--save-db]")
        return 2
    path = argv[1]
    save_db = '--save-db' in argv[2:]
    routes = parse_rtz(path)
    out = write_decoded_json(routes, path)
    print(f"Parsed {len(routes)} route(s). Decoded JSON: {out}")
    if save_db:
        save_to_db_placeholder(routes)
        print("DB save attempted (placeholder).")

if __name__ == "__main__":
    sys.exit(main(sys.argv))