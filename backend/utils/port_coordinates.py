"""
Port Coordinates Mapper
Converts RTZ position coordinates to actual port names
"""

PORT_COORDINATES = {
    # Bergen area
    (60.3913, 5.3221): "Bergen",
    (60.40, 5.28): "Bergen",
    
    # Oslo area  
    (59.90, 10.70): "Oslo",
    (59.88, 10.73): "Oslo",
    (59.73, 10.27): "Drammen",  # Near Oslo but actually Drammen
    
    # Stavanger area
    (58.98, 5.73): "Stavanger",
    
    # Trondheim area
    (63.45, 10.36): "Trondheim",
    
    # Ålesund area
    (62.49, 6.39): "Ålesund",
    (62.46, 6.34): "Ålesund",
    
    # Andalsnes area
    (62.56, 7.63): "Andalsnes",
    
    # Kristiansand area
    (58.15, 8.05): "Kristiansand",
    
    # Sandefjord area
    (59.11, 10.23): "Sandefjord",
    
    # Flekkefjord area
    (58.29, 6.66): "Flekkefjord",
    
    # Northern ports
    (68.22, 15.61): "Lodingen",
    (69.25, 19.37): "Bergeneset",
}

def get_port_name(lat, lon, default="Unknown"):
    """
    Convert coordinates to port name with fuzzy matching
    """
    if not lat or not lon:
        return default
    
    # Try exact match first
    for (port_lat, port_lon), port_name in PORT_COORDINATES.items():
        if abs(float(lat) - port_lat) < 0.01 and abs(float(lon) - port_lon) < 0.01:
            return port_name
    
    # Fuzzy match based on Norwegian coastal regions
    lat_f = float(lat)
    lon_f = float(lon)
    
    # Bergen region
    if 60.0 <= lat_f <= 61.0 and 4.0 <= lon_f <= 6.0:
        return "Bergen Area"
    
    # Oslo region
    elif 59.0 <= lat_f <= 60.0 and 10.0 <= lon_f <= 11.0:
        return "Oslofjord"
    
    # Trondheim region
    elif 63.0 <= lat_f <= 64.0 and 9.0 <= lon_f <= 11.0:
        return "Trondheim Area"
    
    # Stavanger region
    elif 58.5 <= lat_f <= 59.5 and 5.0 <= lon_f <= 6.5:
        return "Stavanger Area"
    
    return default

def extract_position_from_string(position_str):
    """
    Extract lat/lon from "Position 64.26, 9.75" format
    """
    if not position_str or "Position" not in position_str:
        return None, None
    
    try:
        # Remove "Position" and split
        coords = position_str.replace("Position", "").strip()
        lat_str, lon_str = coords.split(",")
        
        lat = float(lat_str.strip())
        lon = float(lon_str.strip())
        
        return lat, lon
    except:
        return None, None

def convert_route_position(position_str):
    """
    Convert "Position 64.26, 9.75" to "Trondheim" if possible
    """
    if not position_str or "Position" not in position_str:
        return position_str  # Already has a name
    
    lat, lon = extract_position_from_string(position_str)
    if lat and lon:
        port_name = get_port_name(lat, lon)
        if port_name != "Unknown":
            return port_name
    
    return position_str  # Return original if can't convert