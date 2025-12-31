"""
Real-time weather service for Norwegian maritime operations.
FIXED: Proper .env loading, caching, and all 10 cities support.
ENHANCED: MET Norway API integration with intelligent fallback.
REAL-TIME: Cached data with automatic refresh for dashboard updates.
"""

import os
import sys
import logging
import random
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from math import radians, cos, sin, asin, sqrt

import requests
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT LOADING - RELIABLE .env LOADING FROM PROJECT ROOT
# ============================================================================

def load_environment_variables():
    """
    Reliably load .env file from project root.
    Ensures MET_USER_AGENT and other variables are available.
    """
    try:
        # Determine project root by traversing up from this file
        current_file = Path(__file__).resolve()
        project_root = None
        
        # Look for .env in current directory and parent directories
        for parent in [current_file.parent, current_file.parent.parent, current_file.parent.parent.parent]:
            env_file = parent / '.env'
            if env_file.exists():
                load_dotenv(env_file, override=True)
                logger.info(f"✅ Loaded .env from: {env_file}")
                project_root = parent
                break
        
        if not project_root:
            logger.warning("⚠️ .env file not found in expected locations")
            # Try loading from default location
            load_dotenv(override=True)
            
        # Verify essential variables
        met_user_agent = os.getenv("MET_USER_AGENT")
        if not met_user_agent:
            logger.warning("⚠️ MET_USER_AGENT not set in .env, using default")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load environment variables: {e}")
        return False

# Load environment on module import
load_environment_variables()

# ============================================================================
# CONFIGURATION - ALL FROM .env WITH SENSIBLE DEFAULTS
# ============================================================================

# MET Norway API Configuration
MET_USER_AGENT = os.getenv("MET_USER_AGENT", "BergNavnMaritime/3.0 (maritime-research@bergnavn.no)")
MET_BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
MET_TIMEOUT = 10  # seconds
MET_MAX_RETRIES = 3

# Default location (Bergen) - used when no coordinates provided
DEFAULT_LAT = float(os.getenv("MET_LAT", "60.3913"))
DEFAULT_LON = float(os.getenv("MET_LON", "5.3221"))

# Cache configuration (10 minutes for real-time updates)
CACHE_TTL_SECONDS = 600  # 10 minutes

# ============================================================================
# ALL 10 NORWEGIAN CITIES - COMPLETE COVERAGE FOR YOUR PROJECT
# ============================================================================

NORWEGIAN_CITIES = {
    'alesund': {
        'name': 'Ålesund',
        'lat': 62.4722,
        'lon': 6.1497,
        'region': 'Møre og Romsdal',
        'maritime_type': 'coastal_fjord',
        'temp_range': (2, 12),  # min, max typical temperatures
        'wind_avg': 5.8,
        'wave_avg': 1.8
    },
    'andalsnes': {
        'name': 'Åndalsnes',
        'lat': 62.5675,
        'lon': 7.6870,
        'region': 'Møre og Romsdal',
        'maritime_type': 'fjord',
        'temp_range': (1, 11),
        'wind_avg': 4.5,
        'wave_avg': 1.2
    },
    'bergen': {
        'name': 'Bergen',
        'lat': 60.3913,
        'lon': 5.3221,
        'region': 'Vestland',
        'maritime_type': 'coastal_fjord',
        'temp_range': (3, 13),
        'wind_avg': 6.2,
        'wave_avg': 2.0
    },
    'drammen': {
        'name': 'Drammen',
        'lat': 59.7441,
        'lon': 10.2045,
        'region': 'Viken',
        'maritime_type': 'fjord_sheltered',
        'temp_range': (4, 15),
        'wind_avg': 3.8,
        'wave_avg': 0.8
    },
    'flekkefjord': {
        'name': 'Flekkefjord',
        'lat': 58.2970,
        'lon': 6.6605,
        'region': 'Agder',
        'maritime_type': 'coastal_fjord',
        'temp_range': (3, 14),
        'wind_avg': 5.2,
        'wave_avg': 1.5
    },
    'kristiansand': {
        'name': 'Kristiansand',
        'lat': 58.1467,
        'lon': 7.9958,
        'region': 'Agder',
        'maritime_type': 'coastal',
        'temp_range': (4, 16),
        'wind_avg': 5.0,
        'wave_avg': 1.3
    },
    'oslo': {
        'name': 'Oslo',
        'lat': 59.9139,
        'lon': 10.7522,
        'region': 'Oslo',
        'maritime_type': 'fjord_sheltered',
        'temp_range': (5, 17),
        'wind_avg': 4.5,
        'wave_avg': 0.8
    },
    'sandefjord': {
        'name': 'Sandefjord',
        'lat': 59.1312,
        'lon': 10.2167,
        'region': 'Vestfold og Telemark',
        'maritime_type': 'coastal',
        'temp_range': (4, 15),
        'wind_avg': 4.8,
        'wave_avg': 1.0
    },
    'stavanger': {
        'name': 'Stavanger',
        'lat': 58.9699,
        'lon': 5.7331,
        'region': 'Rogaland',
        'maritime_type': 'coastal',
        'temp_range': (4, 14),
        'wind_avg': 5.5,
        'wave_avg': 1.5
    },
    'trondheim': {
        'name': 'Trondheim',
        'lat': 63.4305,
        'lon': 10.3951,
        'region': 'Trøndelag',
        'maritime_type': 'fjord',
        'temp_range': (2, 12),
        'wind_avg': 6.8,
        'wave_avg': 2.2
    }
}

# ============================================================================
# WEATHER CACHE FOR REAL-TIME PERFORMANCE
# ============================================================================

class WeatherCache:
    """
    Simple in-memory cache for weather data.
    Prevents excessive API calls and provides real-time response.
    """
    
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached weather data if valid."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                self.hits += 1
                logger.debug(f"Cache hit for {key}")
                return data
            else:
                # Expired cache entry
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, data: Dict):
        """Cache weather data with timestamp."""
        self.cache[key] = (data, datetime.now())
        logger.debug(f"Cached weather data for {key}")
    
    def clear(self):
        """Clear all cached data."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Weather cache cleared")
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_ratio': f"{(self.hits/(self.hits+self.misses)*100):.1f}%" if (self.hits + self.misses) > 0 else "0%"
        }

# Global cache instance
weather_cache = WeatherCache()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points in kilometers.
    Uses Haversine formula for accurate spherical distance.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Earth radius in kilometers
    radius_km = 6371.0
    
    return radius_km * c

def find_nearest_city(lat: float, lon: float) -> Tuple[str, Dict, float]:
    """
    Find the nearest Norwegian city to given coordinates.
    
    Returns:
        Tuple of (city_key, city_data, distance_km)
    """
    nearest_key = None
    nearest_data = None
    nearest_distance = float('inf')
    
    for city_key, city_data in NORWEGIAN_CITIES.items():
        distance = haversine_distance_km(
            lat, lon,
            city_data['lat'], city_data['lon']
        )
        
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_key = city_key
            nearest_data = city_data
    
    return nearest_key, nearest_data, nearest_distance

def degrees_to_compass(degrees: float) -> str:
    """
    Convert degrees to compass direction.
    
    Args:
        degrees: Wind direction in degrees (0-360)
        
    Returns:
        Compass direction (N, NE, E, SE, S, SW, W, NW)
    """
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    idx = round(degrees / (360. / len(directions))) % len(directions)
    return directions[idx]

def calculate_wind_chill(temperature_c: float, wind_speed_ms: float) -> float:
    """
    Calculate wind chill (feels-like temperature).
    
    Args:
        temperature_c: Air temperature in Celsius
        wind_speed_ms: Wind speed in meters per second
        
    Returns:
        Wind chill temperature in Celsius
    """
    # Convert to km/h for wind chill formula
    wind_kmh = wind_speed_ms * 3.6
    
    # Wind chill formula (valid for temp <= 10°C and wind > 4.8 km/h)
    if temperature_c > 10 or wind_kmh <= 4.8:
        return temperature_c
    
    wind_chill = 13.12 + 0.6215 * temperature_c - 11.37 * (wind_kmh ** 0.16) + 0.3965 * temperature_c * (wind_kmh ** 0.16)
    return round(wind_chill, 1)

# ============================================================================
# MET NORWAY API INTEGRATION - REAL-TIME WEATHER DATA
# ============================================================================

def fetch_met_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch real-time weather data from MET Norway API.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Dictionary with weather data or error information
    """
    # Create cache key
    cache_key = f"met_{lat:.4f}_{lon:.4f}"
    
    # Check cache first
    cached = weather_cache.get(cache_key)
    if cached:
        cached['cache_status'] = 'cached'
        return cached
    
    headers = {
        'User-Agent': MET_USER_AGENT,
        'Accept': 'application/json'
    }
    
    params = {
        'lat': round(lat, 4),
        'lon': round(lon, 4)
    }
    
    logger.info(f"🌤️ Fetching MET Norway weather for {lat}, {lon}")
    
    for attempt in range(MET_MAX_RETRIES):
        try:
            response = requests.get(
                MET_BASE_URL,
                params=params,
                headers=headers,
                timeout=MET_TIMEOUT
            )
            
            if response.status_code == 200:
                weather_data = parse_met_response(response.json(), lat, lon)
                if weather_data:
                    # Cache successful response
                    weather_cache.set(cache_key, weather_data)
                    weather_data['cache_status'] = 'fresh'
                    return weather_data
                else:
                    logger.warning("Failed to parse MET Norway response")
                    break
                    
            elif response.status_code == 429:  # Too Many Requests
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.warning(f"Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{MET_MAX_RETRIES})")
                time.sleep(wait_time)
                continue
                
            else:
                logger.error(f"MET API error {response.status_code}: {response.text[:100]}")
                break
                
        except requests.exceptions.Timeout:
            logger.warning(f"MET API timeout (attempt {attempt + 1}/{MET_MAX_RETRIES})")
            if attempt < MET_MAX_RETRIES - 1:
                time.sleep(1)
                continue
                
        except requests.exceptions.ConnectionError:
            logger.warning(f"MET API connection error (attempt {attempt + 1}/{MET_MAX_RETRIES})")
            if attempt < MET_MAX_RETRIES - 1:
                time.sleep(1)
                continue
                
        except Exception as e:
            logger.error(f"Unexpected error fetching MET weather: {e}")
            break
    
    # If we get here, all attempts failed
    logger.warning("All MET API attempts failed, using fallback data")
    return create_empirical_fallback(lat, lon, "MET API unavailable")

def parse_met_response(api_data: Dict, lat: float, lon: float) -> Optional[Dict]:
    """
    Parse MET Norway API response into standardized format.
    
    Args:
        api_data: Raw API response JSON
        lat: Latitude for metadata
        lon: Longitude for metadata
        
    Returns:
        Standardized weather dictionary
    """
    try:
        timeseries = api_data.get('properties', {}).get('timeseries', [])
        if not timeseries:
            logger.warning("No timeseries data in MET response")
            return None
        
        # Get current forecast (first in array)
        current = timeseries[0]
        
        # Extract data
        instant = current.get('data', {}).get('instant', {}).get('details', {})
        next_1h = current.get('data', {}).get('next_1_hours', {})
        
        # Find nearest city
        city_key, city_data, distance_km = find_nearest_city(lat, lon)
        
        # Basic weather data
        temperature = instant.get('air_temperature')
        wind_speed = instant.get('wind_speed')
        wind_direction = instant.get('wind_from_direction')
        
        # Build response
        weather_data = {
            'timestamp': datetime.now().isoformat(),
            'forecast_time': current.get('time', datetime.now().isoformat()),
            'latitude': lat,
            'longitude': lon,
            
            # Location info
            'city': city_data['name'] if city_data else 'Unknown',
            'city_key': city_key,
            'region': city_data.get('region', 'Unknown') if city_data else 'Unknown',
            'distance_to_city_km': round(distance_km, 1),
            
            # Current conditions
            'temperature_c': temperature,
            'wind_speed_ms': wind_speed,
            'wind_direction_deg': wind_direction,
            'wind_direction': degrees_to_compass(wind_direction) if wind_direction else None,
            'wind_gust_ms': instant.get('wind_speed_of_gust'),
            'pressure_hpa': instant.get('air_pressure_at_sea_level'),
            'humidity_percent': instant.get('relative_humidity'),
            'cloudiness_percent': instant.get('cloud_area_fraction'),
            
            # Precipitation
            'precipitation_mm': next_1h.get('details', {}).get('precipitation_amount') if next_1h else None,
            'precipitation_symbol': next_1h.get('summary', {}).get('symbol_code') if next_1h else None,
            
            # Calculated values
            'feels_like_c': calculate_wind_chill(temperature, wind_speed) if temperature and wind_speed else None,
            
            # Metadata
            'data_source': 'met_norway_live',
            'confidence': 'high',
            'update_frequency_minutes': 10
        }
        
        logger.info(f"✅ MET weather: {weather_data['city']} - {temperature}°C, {wind_speed} m/s")
        return weather_data
        
    except Exception as e:
        logger.error(f"Error parsing MET response: {e}")
        return None

# ============================================================================
# EMPIRICAL FALLBACK - WHEN MET API IS UNAVAILABLE
# ============================================================================

def create_empirical_fallback(lat: float, lon: float, reason: str) -> Dict:
    """
    Create realistic fallback weather data based on location and time.
    
    Args:
        lat: Latitude
        lon: Longitude
        reason: Reason for using fallback
        
    Returns:
        Fallback weather data
    """
    # Find nearest city
    city_key, city_data, distance_km = find_nearest_city(lat, lon)
    
    if not city_data:
        # Generic Norwegian coastal weather
        city_data = {
            'name': 'Norwegian Coast',
            'region': 'Coastal Waters',
            'temp_range': (5, 10),
            'wind_avg': 5.5,
            'wave_avg': 1.5
        }
    
    # Current time for realistic variations
    now = datetime.now()
    current_hour = now.hour
    current_month = now.month
    
    # Seasonal adjustments
    month_factor = current_month / 12.0
    seasonal_temp = 5 + 10 * sin(2 * 3.14159 * (month_factor - 0.25))  # Sine wave for seasonal variation
    
    # Diurnal variation (colder at night, warmer in day)
    diurnal_variation = 0
    if 6 <= current_hour < 18:  # Daytime
        diurnal_variation = random.uniform(2, 4)
    else:  # Nighttime
        diurnal_variation = random.uniform(-2, -4)
    
    # Base temperature from city data with variations
    temp_range = city_data.get('temp_range', (5, 10))
    base_temp = sum(temp_range) / 2  # Average of range
    
    # Calculate final temperature with variations
    temperature = round(base_temp + seasonal_temp + diurnal_variation + random.uniform(-1, 1), 1)
    
    # Wind speed based on city average with some variation
    base_wind = city_data.get('wind_avg', 5.0)
    wind_speed = round(base_wind * random.uniform(0.7, 1.3), 1)
    
    # Wind direction varies by hour
    wind_direction_deg = (current_hour * 15) % 360
    
    # Weather conditions based on season
    if current_month in [11, 12, 1, 2, 3]:  # Winter months
        conditions = ['cloudy', 'partly_cloudy', 'rain', 'snow', 'fog']
        weights = [0.3, 0.2, 0.3, 0.1, 0.1]
    else:  # Rest of year
        conditions = ['clear', 'partly_cloudy', 'cloudy', 'rain']
        weights = [0.3, 0.3, 0.2, 0.2]
    
    # Select condition
    condition = random.choices(conditions, weights=weights, k=1)[0]
    
    # Map to MET symbols
    symbol_map = {
        'clear': 'clearsky',
        'partly_cloudy': 'fair',
        'cloudy': 'cloudy',
        'rain': 'rain',
        'snow': 'snow',
        'fog': 'fog'
    }
    
    weather_data = {
        'timestamp': now.isoformat(),
        'latitude': lat,
        'longitude': lon,
        'city': city_data['name'],
        'city_key': city_key,
        'region': city_data.get('region', 'Unknown'),
        'distance_to_city_km': round(distance_km, 1),
        
        # Generated conditions
        'temperature_c': temperature,
        'wind_speed_ms': wind_speed,
        'wind_direction_deg': wind_direction_deg,
        'wind_direction': degrees_to_compass(wind_direction_deg),
        'pressure_hpa': 1013 + random.randint(-20, 20),
        'humidity_percent': 70 + random.randint(-20, 20),
        'cloudiness_percent': 80 if condition in ['cloudy', 'rain', 'snow'] else 40,
        
        # Condition metadata
        'condition': condition,
        'precipitation_symbol': symbol_map.get(condition, 'clearsky'),
        
        # Fallback metadata
        'data_source': 'empirical_fallback',
        'confidence': 'medium',
        'fallback_reason': reason,
        'notes': f'Empirical data based on {city_data["name"]} historical patterns',
        'cache_status': 'fallback_generated'
    }
    
    logger.info(f"⚠️ Using empirical weather for {weather_data['city']}: "
               f"{temperature}°C, {wind_speed} m/s ({reason})")
    
    return weather_data

# ============================================================================
# MAIN WEATHER SERVICE CLASS - REAL-TIME UPDATES
# ============================================================================

class RealTimeWeatherService:
    """
    Main weather service providing real-time updates for maritime dashboard.
    Integrates MET Norway API with intelligent caching and fallback.
    """
    
    def __init__(self):
        """Initialize the real-time weather service."""
        self.cache = weather_cache
        self.request_count = 0
        self.met_requests = 0
        self.fallback_requests = 0
        self.last_update = datetime.now()
        
        logger.info("🌤️ RealTimeWeatherService initialized")
        logger.info(f"📡 MET User Agent: {MET_USER_AGENT[:50]}...")
        logger.info(f"📍 Default location: Bergen ({DEFAULT_LAT}, {DEFAULT_LON})")
        logger.info(f"🏙️ Supporting {len(NORWEGIAN_CITIES)} Norwegian cities")
    
    def get_current_weather(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict:
        """
        Get current weather for specified location.
        
        Args:
            lat: Latitude (defaults to Bergen)
            lon: Longitude (defaults to Bergen)
            
        Returns:
            Current weather data
        """
        self.request_count += 1
        
        # Use defaults if not provided
        if lat is None:
            lat = DEFAULT_LAT
        if lon is None:
            lon = DEFAULT_LON
        
        # Get weather data
        weather_data = fetch_met_weather(lat, lon)
        
        # Track source
        if weather_data.get('data_source') == 'met_norway_live':
            self.met_requests += 1
        else:
            self.fallback_requests += 1
        
        # Add service metadata
        weather_data['service_metadata'] = {
            'request_id': self.request_count,
            'service': 'RealTimeWeatherService',
            'cache_stats': self.cache.stats(),
            'data_freshness_seconds': self._calculate_freshness(weather_data.get('timestamp'))
        }
        
        self.last_update = datetime.now()
        
        return weather_data
    
    def get_weather_for_city(self, city_name: str) -> Dict:
        """
        Get weather for specific Norwegian city.
        
        Args:
            city_name: City name (case-insensitive)
            
        Returns:
            Weather data for the city
            
        Raises:
            ValueError: If city not found
        """
        city_name_lower = city_name.lower()
        
        if city_name_lower not in NORWEGIAN_CITIES:
            valid_cities = ', '.join(sorted(NORWEGIAN_CITIES.keys()))
            raise ValueError(f"City '{city_name}' not found. Valid cities: {valid_cities}")
        
        city_data = NORWEGIAN_CITIES[city_name_lower]
        return self.get_current_weather(city_data['lat'], city_data['lon'])
    
    def get_weather_for_all_cities(self) -> Dict[str, Dict]:
        """
        Get weather for all 10 Norwegian cities.
        
        Returns:
            Dictionary with city keys and weather data
        """
        all_weather = {}
        
        logger.info(f"🌍 Getting weather for all {len(NORWEGIAN_CITIES)} cities...")
        
        for city_key, city_data in NORWEGIAN_CITIES.items():
            try:
                weather = self.get_current_weather(city_data['lat'], city_data['lon'])
                all_weather[city_key] = weather
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to get weather for {city_key}: {e}")
                all_weather[city_key] = {
                    'city': city_data['name'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        logger.info(f"✅ Retrieved weather for {len(all_weather)} cities")
        return all_weather
    
    def get_service_status(self) -> Dict:
        """Get current status of the weather service."""
        return {
            'service': 'RealTimeWeatherService',
            'timestamp': datetime.now().isoformat(),
            'status': 'operational',
            'configuration': {
                'met_user_agent': MET_USER_AGENT[:50] + '...' if len(MET_USER_AGENT) > 50 else MET_USER_AGENT,
                'met_timeout': MET_TIMEOUT,
                'met_max_retries': MET_MAX_RETRIES,
                'cache_ttl_seconds': CACHE_TTL_SECONDS,
                'supported_cities': len(NORWEGIAN_CITIES)
            },
            'statistics': {
                'total_requests': self.request_count,
                'met_api_requests': self.met_requests,
                'fallback_requests': self.fallback_requests,
                'last_update': self.last_update.isoformat(),
                'uptime_seconds': (datetime.now() - self.last_update).total_seconds()
            },
            'cache': self.cache.stats()
        }
    
    def clear_cache(self):
        """Clear all cached weather data."""
        self.cache.clear()
        logger.info("Weather cache cleared")
    
    def _calculate_freshness(self, data_timestamp: Optional[str]) -> int:
        """Calculate data freshness in seconds."""
        if not data_timestamp:
            return 9999
        
        try:
            data_time = datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
            freshness = (datetime.now(data_time.tzinfo) - data_time).total_seconds()
            return int(freshness)
        except:
            return 9999

# ============================================================================
# GLOBAL SERVICE INSTANCE
# ============================================================================

# Primary instance for the application
weather_service = RealTimeWeatherService()

# Legacy function for backward compatibility
def get_best_weather(lat: Optional[float] = None, lon: Optional[float] = None) -> Dict:
    """
    Legacy function for backward compatibility.
    
    Args:
        lat: Latitude (defaults to Bergen)
        lon: Longitude (defaults to Bergen)
        
    Returns:
        Weather data dictionary
    """
    return weather_service.get_current_weather(lat, lon)

# ============================================================================
# TEST FUNCTION
# ============================================================================

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("🧪 Testing RealTimeWeatherService")
    print("=" * 50)
    
    # Test 1: Service status
    status = weather_service.get_service_status()
    print(f"✅ Service Status: {status['status']}")
    print(f"📊 Supported Cities: {status['configuration']['supported_cities']}")
    
    # Test 2: Get weather for Bergen
    print("\n📍 Testing Bergen weather...")
    bergen_weather = weather_service.get_weather_for_city('bergen')
    print(f"   City: {bergen_weather.get('city')}")
    print(f"   Temperature: {bergen_weather.get('temperature_c')}°C")
    print(f"   Wind: {bergen_weather.get('wind_speed_ms')} m/s {bergen_weather.get('wind_direction', '')}")
    print(f"   Source: {bergen_weather.get('data_source')}")
    print(f"   Confidence: {bergen_weather.get('confidence')}")
    
    # Test 3: Test cache
    print("\n💾 Testing cache...")
    cache_stats = weather_service.cache.stats()
    print(f"   Cache hits: {cache_stats['hits']}")
    print(f"   Cache misses: {cache_stats['misses']}")
    print(f"   Hit ratio: {cache_stats['hit_ratio']}")
    
    print("\n" + "=" * 50)
    print("✅ Weather service test completed")