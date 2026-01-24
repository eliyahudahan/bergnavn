"""
Norwegian Wind Turbine Real-Time API Handler
Performs QUICK but REAL search for turbine data from Norwegian sources
Priority: Real-time API → Empirical fallback
Maximum search time: 5 seconds total
"""

import os
import time
import json
import requests
from flask import Blueprint, jsonify, current_app
from datetime import datetime, timedelta
from functools import lru_cache
import concurrent.futures

turbine_bp = Blueprint('turbine_api', __name__)

# Norwegian wind turbine data sources (ordered by priority)
TURBINE_DATA_SOURCES = [
    {
        'name': 'kystdatahuset',
        'url': 'https://api.kystdatahuset.no/api/v1/wind-turbines',
        'method': 'GET',
        'headers': {
            'User-Agent': os.getenv('KYSTDATAHUSET_USER_AGENT', 'BergNavn-Maritime/1.0'),
            'Accept': 'application/json'
        },
        'timeout': 3,  # 3 seconds max
        'enabled': os.getenv('USE_KYSTDATAHUSET_AIS', 'true').lower() == 'true'
    },
    {
        'name': 'nve_wind_power',
        'url': 'https://api.nve.no/hydrology/regobs/v2.0.0/api/WindPower/Stations',
        'method': 'GET',
        'headers': {
            'User-Agent': 'BergNavn-Maritime/1.0',
            'Accept': 'application/json'
        },
        'timeout': 2,  # 2 seconds max
        'enabled': True
    },
    {
        'name': 'statnett_grid',
        'url': 'https://api.statnett.no/api/v1/windfarms',
        'method': 'GET',
        'headers': {
            'Accept': 'application/json'
        },
        'timeout': 2,
        'enabled': True
    }
]

# Empirical Norwegian wind farms (fallback data)
EMPIRICAL_TURBINES = [
    {
        "id": "utsira_nord",
        "name": "Utsira Nord",
        "latitude": 59.5,
        "longitude": 4.0,
        "buffer_meters": 1000,
        "capacity_mw": 1500,
        "status": "planned",
        "turbine_count": 50,
        "operator": "Equinor",
        "data_source": "empirical_fallback",
        "last_updated": datetime.utcnow().isoformat()
    },
    {
        "id": "sorlige_nordsjo_ii",
        "name": "Sørlige Nordsjø II",
        "latitude": 57.5,
        "longitude": 6.8,
        "buffer_meters": 1500,
        "capacity_mw": 3000,
        "status": "planning",
        "turbine_count": 100,
        "operator": "Statkraft",
        "data_source": "empirical_fallback",
        "last_updated": datetime.utcnow().isoformat()
    },
    {
        "id": "bergen_coastal_test",
        "name": "Bergen Coastal Test",
        "latitude": 60.8,
        "longitude": 4.8,
        "buffer_meters": 800,
        "capacity_mw": 200,
        "status": "operational",
        "turbine_count": 5,
        "operator": "University of Bergen",
        "data_source": "empirical_fallback",
        "last_updated": datetime.utcnow().isoformat()
    }
]

def check_single_api_source(source_config):
    """
    Check a single API source for turbine data
    Returns: (success, data, response_time_ms, error_message)
    """
    if not source_config.get('enabled', True):
        return False, None, 0, "Source disabled"
    
    start_time = time.time()
    try:
        response = requests.request(
            method=source_config['method'],
            url=source_config['url'],
            headers=source_config['headers'],
            timeout=source_config['timeout']
        )
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            data = response.json()
            return True, data, response_time, None
        else:
            return False, None, response_time, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        response_time = (time.time() - start_time) * 1000
        return False, None, response_time, "Timeout"
    except requests.exceptions.ConnectionError:
        response_time = (time.time() - start_time) * 1000
        return False, None, response_time, "Connection error"
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return False, None, response_time, str(e)

@turbine_bp.route('/api/turbines/search', methods=['GET'])
def search_turbines():
    """
    Perform REAL search for Norwegian wind turbine data
    Quick search with timeout, returns empirical if no real-time data
    """
    search_start = time.time()
    search_results = []
    found_turbines = []
    
    current_app.logger.info("🔍 Starting REAL turbine API search (max 5s)")
    
    # Try each API source with thread pool for parallel search
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_source = {
            executor.submit(check_single_api_source, source): source
            for source in TURBINE_DATA_SOURCES
        }
        
        for future in concurrent.futures.as_completed(future_to_source, timeout=5):
            source = future_to_source[future]
            try:
                success, data, response_time, error = future.result(timeout=1)
                
                result = {
                    'source': source['name'],
                    'success': success,
                    'response_time_ms': round(response_time, 1),
                    'error': error,
                    'turbines_found': 0,
                    'data_available': bool(data)
                }
                
                if success and data:
                    # Count actual turbines if data structure known
                    turbines = extract_turbines_from_data(data, source['name'])
                    if turbines:
                        found_turbines.extend(turbines)
                        result['turbines_found'] = len(turbines)
                
                search_results.append(result)
                current_app.logger.info(
                    f"  [{source['name']}] {'✅' if success else '❌'} "
                    f"{response_time:.1f}ms - {error or 'Success'}"
                )
                
            except concurrent.futures.TimeoutError:
                search_results.append({
                    'source': source['name'],
                    'success': False,
                    'response_time_ms': source['timeout'] * 1000,
                    'error': 'Thread timeout',
                    'turbines_found': 0,
                    'data_available': False
                })
    
    total_search_time = time.time() - search_start
    
    # Determine data source
    if found_turbines:
        data_source = 'realtime_api'
        turbines_to_return = found_turbines
        current_app.logger.info(f"✅ Found {len(found_turbines)} real-time turbines")
    else:
        data_source = 'empirical_fallback'
        turbines_to_return = EMPIRICAL_TURBINES
        current_app.logger.info(f"📊 Using empirical data: {len(EMPIRICAL_TURBINES)} turbines")
    
    return jsonify({
        'status': 'success',
        'search_performed': True,
        'total_search_time_seconds': round(total_search_time, 2),
        'data_source': data_source,
        'search_results': search_results,
        'turbines': turbines_to_return,
        'turbine_count': len(turbines_to_return),
        'search_timestamp': datetime.utcnow().isoformat(),
        'search_summary': generate_search_summary(search_results, data_source)
    })

def extract_turbines_from_data(api_data, source_name):
    """
    Extract turbine data from different API response formats
    Returns list of standardized turbine objects
    """
    turbines = []
    
    try:
        if source_name == 'kystdatahuset' and isinstance(api_data, list):
            for item in api_data[:10]:  # Limit to first 10
                if 'latitude' in item and 'longitude' in item:
                    turbines.append({
                        'id': item.get('id', f"kdh_{len(turbines)}"),
                        'name': item.get('name', 'Unknown Turbine'),
                        'latitude': item['latitude'],
                        'longitude': item['longitude'],
                        'buffer_meters': item.get('safety_zone', 500),
                        'capacity_mw': item.get('capacity', 0),
                        'status': item.get('status', 'unknown'),
                        'data_source': 'kystdatahuset_realtime'
                    })
        
        elif source_name == 'nve_wind_power' and 'Stations' in api_data:
            for station in api_data['Stations'][:10]:
                turbines.append({
                    'id': station.get('StationId', f"nve_{len(turbines)}"),
                    'name': station.get('StationName', 'NVE Turbine'),
                    'latitude': station.get('Latitude'),
                    'longitude': station.get('Longitude'),
                    'buffer_meters': 500,  # Default safety zone
                    'capacity_mw': station.get('Effect', 0),
                    'status': 'operational',
                    'data_source': 'nve_realtime'
                })
    
    except Exception as e:
        current_app.logger.warning(f"Failed to parse {source_name} data: {e}")
    
    return turbines

def generate_search_summary(search_results, data_source):
    """
    Generate human-readable search summary
    """
    successful = [r for r in search_results if r['success']]
    failed = [r for r in search_results if not r['success']]
    
    summary = f"Real-time search: {len(successful)} succeeded, {len(failed)} failed. "
    
    if data_source == 'realtime_api':
        total_turbines = sum(r['turbines_found'] for r in search_results)
        summary += f"Found {total_turbines} real-time turbines."
    else:
        summary += "Using empirical fallback data."
    
    return summary

@turbine_bp.route('/api/turbines/proximity/<float:lat>/<float:lon>', methods=['GET'])
def check_turbine_proximity(lat, lon):
    """
    Check if a vessel is too close to any turbine
    Returns proximity warnings
    """
    # First try to get real-time data
    search_response = search_turbines().get_json()
    turbines = search_response['turbines']
    
    warnings = []
    
    for turbine in turbines:
        distance_km = calculate_distance_km(
            lat, lon,
            turbine['latitude'], turbine['longitude']
        )
        
        distance_m = distance_km * 1000
        buffer_zone = turbine.get('buffer_meters', 500)
        
        if distance_m < buffer_zone:
            warning_level = 'CRITICAL' if distance_m < buffer_zone * 0.3 else 'WARNING'
            
            warnings.append({
                'turbine_id': turbine['id'],
                'turbine_name': turbine['name'],
                'distance_meters': round(distance_m),
                'buffer_zone_meters': buffer_zone,
                'warning_level': warning_level,
                'severity': 'high' if warning_level == 'CRITICAL' else 'medium',
                'recommended_action': f"Change course to maintain {buffer_zone}m clearance",
                'data_source': turbine.get('data_source', 'unknown')
            })
    
    return jsonify({
        'status': 'success',
        'vessel_position': {'lat': lat, 'lon': lon},
        'turbines_checked': len(turbines),
        'proximity_warnings': warnings,
        'warning_count': len(warnings),
        'data_source': search_response['data_source'],
        'search_summary': search_response['search_summary']
    })

def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in km
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

@turbine_bp.route('/api/turbines/status', methods=['GET'])
def turbine_system_status():
    """
    Get detailed status of turbine alert system
    """
    return jsonify({
        'status': 'operational',
        'system': 'norwegian_wind_turbine_alerts',
        'description': 'Real-time turbine proximity warning system',
        'features': [
            'Real-time API search (max 5s)',
            'Empirical fallback data',
            'Proximity calculation',
            'Warning system',
            'Transparent search status'
        ],
        'data_sources': [
            {'name': s['name'], 'enabled': s['enabled'], 'timeout': s['timeout']}
            for s in TURBINE_DATA_SOURCES
        ],
        'empirical_turbines_count': len(EMPIRICAL_TURBINES),
        'api_endpoints': {
            'search': '/api/turbines/search',
            'proximity': '/api/turbines/proximity/<lat>/<lon>',
            'status': '/api/turbines/status'
        },
        'timestamp': datetime.utcnow().isoformat()
    })