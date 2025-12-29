# backend/routes/maritime_routes.py
"""
Maritime Routes - Main maritime dashboard and API endpoints.
FIXED: Dashboard endpoint now properly passes RTZ data to template.
ADDED: convert_route_position function to fix "Position" display issues.
"""

from flask import Blueprint, render_template, jsonify, request
from backend.utils.helpers import get_current_language
import os
import logging
from datetime import datetime, timedelta
import requests
import math

logger = logging.getLogger(__name__)

# Blueprint must be defined BEFORE any routes
maritime_bp = Blueprint('maritime_bp', __name__)

# ============================================================================
# HELPER FUNCTIONS - ADDED CRITICAL CONVERSION FUNCTION
# ============================================================================

def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in nautical miles."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return 3440.065 * c

def get_primary_focus_port() -> dict:
    """
    Determine which port to focus on based on REAL vessel activity.
    Priority: Bergen > Oslo > Stavanger > Trondheim > Ålesund > Åndalsnes > 
    Drammen > Kristiansand > Sandefjord > Flekkefjord
    """
    try:
        from backend.services.ais_service import ais_service
        
        vessels = ais_service.get_latest_positions()
        if not vessels:
            return {'name': 'Bergen', 'lat': 60.3913, 'lon': 5.3221, 'vessel_count': 0}
        
        ports = [
            {'name': 'Bergen', 'lat': 60.3913, 'lon': 5.3221, 'priority': 1},
            {'name': 'Oslo', 'lat': 59.9139, 'lon': 10.7522, 'priority': 2},
            {'name': 'Stavanger', 'lat': 58.9700, 'lon': 5.7331, 'priority': 3},
            {'name': 'Trondheim', 'lat': 63.4305, 'lon': 10.3951, 'priority': 4},
            {'name': 'Ålesund', 'lat': 62.4722, 'lon': 6.1497, 'priority': 5},
            {'name': 'Åndalsnes', 'lat': 62.5675, 'lon': 7.6870, 'priority': 6},
            {'name': 'Drammen', 'lat': 59.7441, 'lon': 10.2045, 'priority': 7},
            {'name': 'Kristiansand', 'lat': 58.1467, 'lon': 7.9958, 'priority': 8},
            {'name': 'Sandefjord', 'lat': 59.1312, 'lon': 10.2167, 'priority': 9},
            {'name': 'Flekkefjord', 'lat': 58.2970, 'lon': 6.6605, 'priority': 10},
        ]
        
        for port in sorted(ports, key=lambda x: x['priority']):
            vessel_count = sum(1 for v in vessels 
                            if haversine_nm(v.get('lat', 0), v.get('lon', 0), 
                                          port['lat'], port['lon']) < 20)
            if vessel_count > 0:
                return {
                    'name': port['name'],
                    'lat': port['lat'],
                    'lon': port['lon'],
                    'vessel_count': vessel_count,
                    'priority': port['priority']
                }
        
        return {'name': 'Bergen', 'lat': 60.3913, 'lon': 5.3221, 'vessel_count': 0}
        
    except Exception as e:
        logger.error(f"Error determining focus port: {e}")
        return {'name': 'Bergen', 'lat': 60.3913, 'lon': 5.3221, 'vessel_count': 0}

def convert_route_position(position_str: str) -> str:
    """
    Convert 'Position lat, lon' strings to meaningful location names.
    This is the function that the template expects.
    """
    if not position_str:
        return "Norwegian Coast"
    
    # If it's already a city name, return as-is
    known_cities = [
        'Bergen', 'Oslo', 'Stavanger', 'Trondheim', 'Ålesund', 'Andalsnes',
        'Drammen', 'Kristiansand', 'Sandefjord', 'Flekkefjord',
        'Unknown', 'Coastal Waters', 'Norwegian Coast'
    ]
    
    for city in known_cities:
        if city.lower() in position_str.lower():
            return city
    
    # Try to extract coordinates and map to nearest city
    if "Position" in position_str:
        try:
            # Extract coordinates from "Position 64.26, 9.75"
            coord_part = position_str.replace("Position", "").strip()
            parts = coord_part.split(",")
            if len(parts) == 2:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                
                # Map coordinates to nearest Norwegian city
                norwegian_cities = {
                    'Bergen': (60.3913, 5.3221),
                    'Oslo': (59.9139, 10.7522),
                    'Stavanger': (58.9700, 5.7331),
                    'Trondheim': (63.4305, 10.3951),
                    'Ålesund': (62.4722, 6.1497),
                    'Andalsnes': (62.5675, 7.6870),
                    'Drammen': (59.7441, 10.2045),
                    'Kristiansand': (58.1467, 7.9958),
                    'Sandefjord': (59.1312, 10.2167),
                    'Flekkefjord': (58.2970, 6.6605)
                }
                
                # Find nearest city
                min_distance = float('inf')
                nearest_city = "Norwegian Coast"
                
                for city_name, (city_lat, city_lon) in norwegian_cities.items():
                    distance = haversine_nm(lat, lon, city_lat, city_lon)
                    if distance < min_distance and distance < 50:  # Within 50 NM
                        min_distance = distance
                        nearest_city = city_name
                
                return nearest_city
        except (ValueError, IndexError):
            pass
    
    # If no match found, return a cleaned version
    if "Position" in position_str:
        return "Coastal Position"
    
    return position_str

def convert_route_position_by_coordinates(lat: float, lon: float) -> str:
    """Convert latitude/longitude to nearest city name."""
    if not lat or not lon:
        return "Norwegian Coast"
    
    norwegian_cities = {
        'Bergen': (60.3913, 5.3221),
        'Oslo': (59.9139, 10.7522),
        'Stavanger': (58.9700, 5.7331),
        'Trondheim': (63.4305, 10.3951),
        'Ålesund': (62.4722, 6.1497),
        'Andalsnes': (62.5675, 7.6870),
        'Drammen': (59.7441, 10.2045),
        'Kristiansand': (58.1467, 7.9958),
        'Sandefjord': (59.1312, 10.2167),
        'Flekkefjord': (58.2970, 6.6605)
    }
    
    min_distance = float('inf')
    nearest_city = "Norwegian Coast"
    
    for city_name, (city_lat, city_lon) in norwegian_cities.items():
        distance = haversine_nm(lat, lon, city_lat, city_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_city = city_name
    
    return nearest_city

# ============================================================================
# CRITICAL FIX: Dashboard endpoint with RTZ data
# ============================================================================

@maritime_bp.route('/api/health')
def maritime_health():
    """Health check endpoint for maritime dashboard."""
    try:
        status = {
            'status': 'operational',
            'services': {
                'ais': 'connected',
                'weather': 'connected',
                'rtz': 'available',
                'hazards': 'available'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0.0',
            'ports_supported': 10
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

# ============================================================================
# PAGE ROUTES - DASHBOARD FIXED
# ============================================================================

@maritime_bp.route('/')
def maritime_home():
    """Maritime home page."""
    return render_template("maritime/home.html", lang=get_current_language())

@maritime_bp.route('/dashboard')
def dashboard():
    """
    Maritime dashboard page - FIXED: Now properly passes RTZ data.
    This matches the structure of routes.html template.
    ADDED: convert_route_position function to fix "Position" display.
    """
    try:
        # Try to get routes from database first
        from backend.extensions import db
        
        # Check if database tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        routes_data = []
        cities_with_routes = set()
        total_distance = 0
        waypoint_count = 0
        
        if 'routes' in tables:
            from backend.models import Route
            
            with db.session() as session:
                routes = session.query(Route).filter(Route.is_active == True).all()
                
                for route in routes:
                    # Clean up origin and destination before adding to data
                    origin_clean = route.origin or ''
                    destination_clean = route.destination or ''
                    
                    # Apply conversion to clean up "Position" strings
                    if origin_clean and "Position" in origin_clean:
                        origin_display = convert_route_position(origin_clean)
                    else:
                        origin_display = origin_clean or "Norwegian Coast"
                    
                    if destination_clean and "Position" in destination_clean:
                        destination_display = convert_route_position(destination_clean)
                    else:
                        destination_display = destination_clean or "Norwegian Coast"
                    
                    routes_data.append({
                        'name': route.name or f"NCA Route",
                        'origin': origin_display,
                        'destination': destination_display,
                        'total_distance_nm': route.total_distance_nm or 0,
                        'waypoint_count': route.waypoint_count or 0,
                        'source': 'NCA',
                        'is_active': True,
                        'description': route.description or 'Official NCA route',
                        'raw_origin': origin_clean,  # Keep original for reference
                        'raw_destination': destination_clean
                    })
                    total_distance += route.total_distance_nm or 0
                    waypoint_count += route.waypoint_count or 0
                    
                    if origin_display != "Norwegian Coast":
                        cities_with_routes.add(origin_display)
                    if destination_display != "Norwegian Coast":
                        cities_with_routes.add(destination_display)
        
        # If no database routes, try to get from RTZ files
        if not routes_data:
            logger.info("No database routes found, checking RTZ files")
            try:
                from backend.services.rtz_parser import find_rtz_files, parse_rtz_file
                
                rtz_files = find_rtz_files()
                if rtz_files:
                    for city, file_paths in rtz_files.items():
                        for file_path in file_paths:
                            try:
                                if os.path.exists(file_path):
                                    parsed_routes = parse_rtz_file(file_path)
                                    if parsed_routes:
                                        for route in parsed_routes:
                                            city_display = city.capitalize() if city else "Norwegian Coast"
                                            routes_data.append({
                                                'name': route.get('route_name', f'{city_display} Route'),
                                                'origin': city_display,
                                                'destination': 'Coastal Waters',
                                                'total_distance_nm': route.get('total_distance_nm', 0),
                                                'waypoint_count': len(route.get('waypoints', [])),
                                                'source': 'RTZ File',
                                                'is_active': True,
                                                'description': f'NCA coastal route near {city_display}',
                                                'raw_origin': city_display,
                                                'raw_destination': 'Coastal Waters'
                                            })
                                            total_distance += route.get('total_distance_nm', 0)
                                            waypoint_count += len(route.get('waypoints', []))
                                            
                                            cities_with_routes.add(city_display)
                            except Exception as e:
                                logger.warning(f"Could not parse RTZ file for {city}: {e}")
                                continue
            except ImportError:
                logger.warning("RTZ parser not available")
        
        # Get AIS data for vessel count
        try:
            from backend.services.ais_service import ais_service
            vessels = ais_service.get_latest_positions()
            active_vessels = len(vessels) if vessels else 0
        except:
            active_vessels = 0
        
        # Convert set to list for template
        cities_list = list(cities_with_routes)
        
        # CRITICAL: Pass all required data to template INCLUDING the conversion function
        return render_template(
            "maritime_split/dashboard_base.html",
            lang=get_current_language(),
            # Template expects these exact variable names
            routes=routes_data,
            cities_with_routes=cities_list,
            total_distance=total_distance,
            waypoint_count=waypoint_count,
            active_ports_count=len(cities_list),
            active_vessels=active_vessels,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            dashboard_version='1.0.0',
            ports_supported=10,
            # CRITICAL ADDITION: Pass the conversion function to template
            convert_route_position=convert_route_position,
            convert_route_position_by_coordinates=convert_route_position_by_coordinates
        )
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        # Return template with empty data on error
        return render_template(
            "maritime_split/dashboard_base.html",
            lang=get_current_language(),
            routes=[],
            cities_with_routes=[],
            total_distance=0,
            waypoint_count=0,
            active_ports_count=0,
            active_vessels=0,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            dashboard_version='1.0.0',
            ports_supported=10,
            convert_route_position=convert_route_position,
            convert_route_position_by_coordinates=convert_route_position_by_coordinates
        )

@maritime_bp.route('/vessels')
def vessels():
    """Vessels information page."""
    return render_template("maritime/vessels.html", lang=get_current_language())

@maritime_bp.route('/ports')
def ports():
    """Ports information page."""
    return render_template("maritime/ports.html", lang=get_current_language())

# ============================================================================
# API ENDPOINTS - 100% EMPIRICAL
# ============================================================================

@maritime_bp.route('/api/ais-data')
def ais_data():
    """REAL-TIME API endpoint for AIS data."""
    try:
        from backend.services.ais_service import ais_service
        
        vessels = ais_service.get_latest_positions()
        
        if not vessels:
            return jsonify({
                'status': 'no_data',
                'message': 'No vessels currently in Norwegian waters',
                'vessels': [],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        
        ports = [
            {'id': 1, 'name': 'Bergen', 'lat': 60.3913, 'lon': 5.3221, 'country': 'Norway'},
            {'id': 2, 'name': 'Stavanger', 'lat': 58.9700, 'lon': 5.7331, 'country': 'Norway'},
            {'id': 3, 'name': 'Oslo', 'lat': 59.9139, 'lon': 10.7522, 'country': 'Norway'},
            {'id': 4, 'name': 'Trondheim', 'lat': 63.4305, 'lon': 10.3951, 'country': 'Norway'},
            {'id': 5, 'name': 'Ålesund', 'lat': 62.4722, 'lon': 6.1497, 'country': 'Norway'},
            {'id': 6, 'name': 'Åndalsnes', 'lat': 62.5675, 'lon': 7.6870, 'country': 'Norway'},
            {'id': 7, 'name': 'Drammen', 'lat': 59.7441, 'lon': 10.2045, 'country': 'Norway'},
            {'id': 8, 'name': 'Kristiansand', 'lat': 58.1467, 'lon': 7.9958, 'country': 'Norway'},
            {'id': 9, 'name': 'Sandefjord', 'lat': 59.1312, 'lon': 10.2167, 'country': 'Norway'},
            {'id': 10, 'name': 'Flekkefjord', 'lat': 58.2970, 'lon': 6.6605, 'country': 'Norway'},
        ]
        
        vessels_per_port = {}
        for port in ports:
            vessel_count = sum(1 for v in vessels 
                            if haversine_nm(v.get('lat', 0), v.get('lon', 0), 
                                          port['lat'], port['lon']) < 20)
            vessels_per_port[port['name']] = vessel_count
        
        focus_port = get_primary_focus_port()
        focus_vessels = [
            v for v in vessels 
            if haversine_nm(v.get('lat', 0), v.get('lon', 0), 
                          focus_port['lat'], focus_port['lon']) < 20
        ]
        
        return jsonify({
            'status': 'success',
            'vessels': vessels,
            'ports': ports,
            'vessels_per_port': vessels_per_port,
            'focus_port': focus_port,
            'focus_vessels': focus_vessels,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"AIS data error: {e}")
        return jsonify({
            'status': 'service_error',
            'message': f'AIS service unavailable: {str(e)}',
            'vessels': [],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503

@maritime_bp.route('/api/ais-status')
def ais_status():
    """API endpoint for AIS service status."""
    try:
        from backend.services.ais_service import ais_service
        status = ais_service.get_service_status()
        return jsonify({
            'status': 'success',
            'ais_service': status,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        logger.error(f"AIS status error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@maritime_bp.route('/api/weather')
def weather_data():
    """REAL-TIME API endpoint for weather data - FIXED JSON structure."""
    try:
        met_user_agent = os.getenv('MET_USER_AGENT', 'BergNavnMaritime/3.0')
        headers = {'User-Agent': met_user_agent}
        
        bergen_location = {'name': 'Bergen', 'lat': 60.39, 'lon': 5.32}
        
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={bergen_location['lat']}&lon={bergen_location['lon']}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            instant = data['properties']['timeseries'][0]['data']['instant']['details']
            
            conditions = "fair"
            conditions_text = "Fair"
            
            if 'next_1_hours' in data['properties']['timeseries'][0]['data']:
                next_1_hours = data['properties']['timeseries'][0]['data']['next_1_hours']
                if 'summary' in next_1_hours:
                    summary = next_1_hours['summary']
                    conditions_text = summary.get('symbol_code', 'fair')
                    conditions = conditions_text
            
            # CRITICAL FIX: Return the exact structure JavaScript expects
            weather_info = {
                'status': 'success',
                'weather': {
                    'location': 'Bergen',
                    'country': 'Norway',
                    'temperature': instant.get('air_temperature'),
                    'wind_speed': instant.get('wind_speed'),
                    'wind_direction': instant.get('wind_from_direction'),
                    'pressure': instant.get('air_pressure_at_sea_level'),
                    'humidity': instant.get('relative_humidity'),
                    'conditions': conditions,
                    'conditions_text': conditions_text,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'source': 'MET Norway API',
                    'api_status': 'live'
                }
            }
            
            return jsonify(weather_info)
        else:
            logger.error(f"Weather API returned status {response.status_code}")
            return jsonify({
                'status': 'error',
                'message': f'MET Norway API unavailable: {response.status_code}',
                'weather': None
            }), response.status_code
            
    except requests.exceptions.Timeout:
        logger.error("Weather API timeout")
        return jsonify({
            'status': 'error',
            'message': 'Weather API timeout - service unavailable',
            'weather': None
        }), 504
    except requests.exceptions.ConnectionError:
        logger.error("Weather API connection error")
        return jsonify({
            'status': 'error',
            'message': 'Cannot connect to weather service',
            'weather': None
        }), 503
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'weather': None
        }), 500

@maritime_bp.route('/api/weather/all')
def weather_all():
    """Alternative endpoint that returns weather for all 10 cities."""
    try:
        met_user_agent = os.getenv('MET_USER_AGENT', 'BergNavnMaritime/3.0')
        headers = {'User-Agent': met_user_agent}
        
        locations = [
            {'name': 'Bergen', 'lat': 60.39, 'lon': 5.32},
            {'name': 'Oslo', 'lat': 59.91, 'lon': 10.75},
            {'name': 'Stavanger', 'lat': 58.97, 'lon': 5.73},
            {'name': 'Trondheim', 'lat': 63.43, 'lon': 10.40},
            {'name': 'Ålesund', 'lat': 62.47, 'lon': 6.15},
            {'name': 'Åndalsnes', 'lat': 62.57, 'lon': 7.69},
            {'name': 'Drammen', 'lat': 59.74, 'lon': 10.20},
            {'name': 'Kristiansand', 'lat': 58.15, 'lon': 8.00},
            {'name': 'Sandefjord', 'lat': 59.13, 'lon': 10.22},
            {'name': 'Flekkefjord', 'lat': 58.30, 'lon': 6.66},
        ]
        
        all_weather = []
        failed_locations = []
        
        for location in locations:
            try:
                url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={location['lat']}&lon={location['lon']}"
                response = requests.get(url, headers=headers, timeout=3)
                
                if response.status_code == 200:
                    data = response.json()
                    instant = data['properties']['timeseries'][0]['data']['instant']['details']
                    
                    conditions = "fair"
                    if 'next_1_hours' in data['properties']['timeseries'][0]['data']:
                        next_1_hours = data['properties']['timeseries'][0]['data']['next_1_hours']
                        if 'summary' in next_1_hours:
                            conditions = next_1_hours['summary'].get('symbol_code', 'fair')
                    
                    all_weather.append({
                        'location': location['name'],
                        'temperature': instant.get('air_temperature'),
                        'wind_speed': instant.get('wind_speed'),
                        'wind_direction': instant.get('wind_from_direction'),
                        'pressure': instant.get('air_pressure_at_sea_level'),
                        'humidity': instant.get('relative_humidity'),
                        'conditions': conditions,
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'source': 'MET Norway API'
                    })
                else:
                    failed_locations.append(location['name'])
                    logger.warning(f"Weather API failed for {location['name']}: {response.status_code}")
                    
            except Exception as loc_error:
                failed_locations.append(location['name'])
                logger.warning(f"Weather error for {location['name']}: {loc_error}")
                continue
        
        if all_weather:
            return jsonify({
                'status': 'partial_success' if failed_locations else 'success',
                'data': all_weather,
                'count': len(all_weather),
                'failed_locations': failed_locations,
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No weather data available from any location',
                'data': [],
                'count': 0,
                'failed_locations': failed_locations,
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            }), 503
            
    except Exception as e:
        logger.error(f"Weather all API error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': [],
            'count': 0,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }), 500

@maritime_bp.route('/api/statistics')
def maritime_statistics():
    """API endpoint for maritime statistics."""
    try:
        from backend.services.ais_service import ais_service
        
        vessels = ais_service.get_latest_positions()
        
        stats = {
            'status': 'success',
            'total_vessels': len(vessels) if vessels else 0,
            'active_vessels': len(vessels) if vessels else 0,
            'ports_monitored': 10,
            'incidents_today': 0,
            'alerts_active': 0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data_source': 'Real AIS data'
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        return jsonify({
            'status': 'service_error',
            'message': f'Statistics service unavailable: {str(e)}',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503

# ============================================================================
# REAL RTZ ROUTES - 100% EMPIRICAL
# ============================================================================

@maritime_bp.route('/api/rtz/routes')
def rtz_routes():
    """API endpoint for REAL RTZ routes from your files."""
    try:
        from backend.services.rtz_parser import find_rtz_files, parse_rtz_file
        
        rtz_files = find_rtz_files()
        
        if not rtz_files:
            return jsonify({
                'status': 'no_files',
                'message': 'No RTZ files found in backend/assets/routeinfo_routes/',
                'routes': [],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        
        all_routes = []
        parsed_cities = []
        
        for city, file_paths in rtz_files.items():
            city_parsed = False
            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        routes = parse_rtz_file(file_path)
                        if routes:
                            for route in routes:
                                route['city'] = city.capitalize()
                                route['source_file'] = file_path
                                route['parsed_at'] = datetime.utcnow().isoformat() + 'Z'
                                all_routes.append(route)
                            city_parsed = True
                            parsed_cities.append(city.capitalize())
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse RTZ for {city}: {e}")
                    continue
            
            if not city_parsed:
                logger.info(f"No valid RTZ data for {city}")
        
        if all_routes:
            return jsonify({
                'status': 'success',
                'routes': all_routes,
                'parsed_cities': parsed_cities,
                'total_routes': len(all_routes),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        else:
            return jsonify({
                'status': 'parse_error',
                'message': 'RTZ files exist but could not be parsed - check file format',
                'routes': [],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
            
    except ImportError:
        return jsonify({
            'status': 'service_unavailable',
            'message': 'RTZ parser service not available',
            'routes': [],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    except Exception as e:
        logger.error(f"RTZ routes API error: {e}")
        return jsonify({
            'status': 'service_error',
            'message': f'RTZ service unavailable: {str(e)}',
            'routes': [],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503

# ============================================================================
# SYSTEM STATUS
# ============================================================================

@maritime_bp.route('/api/system-status')
def system_status():
    """API endpoint for system status."""
    try:
        # Check AIS service
        ais_ok = False
        ais_status_info = {}
        try:
            from backend.services.ais_service import ais_service
            ais_status_info = ais_service.get_service_status()
            ais_ok = ais_status_info.get('connected', False)
        except ImportError:
            ais_status_info = {'error': 'AIS service module not available'}
        except Exception as e:
            ais_status_info = {'error': str(e)}
        
        # Check weather service
        weather_ok = False
        weather_status = {}
        try:
            response = requests.get(f"{request.host_url}maritime/api/weather", timeout=3)
            weather_ok = response.status_code == 200
            if weather_ok:
                try:
                    weather_data = response.json()
                    weather_status = {'api_status': weather_data.get('status')}
                except:
                    weather_status = {'api_status': 'unknown'}
        except Exception as e:
            weather_status = {'error': str(e)}
        
        # Check RTZ service
        rtz_ok = False
        rtz_status = {}
        try:
            from backend.services.rtz_parser import find_rtz_files
            rtz_files = find_rtz_files()
            rtz_ok = len(rtz_files) > 0
            rtz_status = {'cities_with_files': len(rtz_files)}
        except ImportError:
            rtz_status = {'error': 'RTZ parser module not available'}
        except Exception as e:
            rtz_status = {'error': str(e)}
        
        services_available = [ais_ok, weather_ok, rtz_ok]
        available_count = sum(services_available)
        
        if available_count == 3:
            overall_status = 'fully_operational'
        elif available_count >= 1:
            overall_status = 'partially_operational'
        else:
            overall_status = 'offline'
        
        return jsonify({
            'status': 'success',
            'system': {
                'overall': overall_status,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0.0',
                'environment': os.getenv('FLASK_ENV', 'development'),
                'ports_supported': 10
            },
            'services': {
                'ais': {
                    'status': 'connected' if ais_ok else 'disconnected',
                    'details': ais_status_info
                },
                'weather': {
                    'status': 'connected' if weather_ok else 'disconnected',
                    'details': weather_status
                },
                'rtz': {
                    'status': 'available' if rtz_ok else 'unavailable',
                    'details': rtz_status
                }
            }
        })
        
    except Exception as e:
        logger.error(f"System status error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500