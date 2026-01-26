# backend/services/met_norway_service.py
"""
MET Norway Weather Service - Real-time weather data from Norwegian Meteorological Institute
Uses official MET Norway API with proper attribution
Uses environment variables from .env for configuration

API Documentation: https://api.met.no/weatherapi/locationforecast/2.0/documentation
Important: Must include proper User-Agent and follow rate limits
"""

import os
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json
import time

logger = logging.getLogger(__name__)

class METNorwayService:
    """
    Service for fetching real weather data from MET Norway API
    Official documentation: https://api.met.no/
    
    Environment variables required (from .env):
        - MET_USER_AGENT: User agent string for API requests (email required)
        - MET_LAT: Default latitude (e.g., 60.39 for Bergen)
        - MET_LON: Default longitude (e.g., 5.32 for Bergen)
    
    API Rate Limits: 8 requests per second, cache responses for at least 10 minutes
    """
    
    def __init__(self):
        """Initialize MET Norway service using environment variables."""
        
        # Get configuration from environment variables
        self.base_url = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
        self.user_agent = os.environ.get('MET_USER_AGENT', '')
        
        # Critical: MET Norway REQUIRES a valid User-Agent with contact info
        if not self.user_agent or len(self.user_agent.strip()) < 10:
            logger.error("❌ MET_USER_AGENT not properly set in environment variables")
            logger.error("   Format: 'AppName/Version (contact@email.com)'")
            # Fallback that follows guidelines but user should update .env
            self.user_agent = "BergNavnWeather/1.0 (contact@bergnavn.example.com)"
            logger.warning(f"   Using fallback: {self.user_agent}")
        else:
            logger.info(f"✅ MET_USER_AGENT configured: {self.user_agent[:50]}...")
        
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
            'Cache-Control': 'max-age=600'  # Cache for 10 minutes as per API guidelines
        }
        
        # Get coordinates from environment variables
        try:
            self.default_lat = float(os.environ.get('MET_LAT', '60.3913'))
            self.default_lon = float(os.environ.get('MET_LON', '5.3221'))
        except ValueError as e:
            logger.error(f"❌ Invalid MET_LAT or MET_LON in environment variables: {e}")
            self.default_lat = 60.3913  # Bergen fallback
            self.default_lon = 5.3221   # Bergen fallback
        
        # Cache for API responses (respect MET Norway's cache guidelines)
        self.cache = {}
        self.cache_duration = 600  # 10 minutes in seconds
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.125  # 8 requests per second max
        
        # Log configuration
        logger.info(f"🌤️ MET Norway Service initialized")
        logger.info(f"  • Default coordinates: {self.default_lat}, {self.default_lon}")
        logger.info(f"  • API endpoint: {self.base_url}")
        logger.info(f"  • Cache duration: {self.cache_duration} seconds")
        
        # Verify environment variables
        self._verify_env_config()
    
    def _verify_env_config(self):
        """Verify that required environment variables are properly configured."""
        required_vars = ['MET_USER_AGENT', 'MET_LAT', 'MET_LON']
        
        missing = []
        warnings = []
        
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing.append(var)
            elif var == 'MET_USER_AGENT' and '(' not in value:
                warnings.append(f"{var} should contain email in parentheses")
        
        if missing:
            logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
            logger.error("   Add these to your .env file")
        
        if warnings:
            for warning in warnings:
                logger.warning(f"⚠️ {warning}")
        
        if not missing and not warnings:
            logger.info("✅ All MET Norway environment variables properly configured")
    
    def _make_api_request(self, lat: float, lon: float, altitude: int = 0) -> Optional[Dict]:
        """
        Make actual API request to MET Norway with proper rate limiting and caching.
        
        Args:
            lat: Latitude
            lon: Longitude
            altitude: Altitude in meters (0 for sea level)
            
        Returns:
            API response as dictionary or None if failed
        """
        # Check cache first
        cache_key = f"{lat:.4f},{lon:.4f},{altitude}"
        current_time = time.time()
        
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if current_time - cached_time < self.cache_duration:
                logger.debug(f"📦 Using cached MET Norway data for {lat}, {lon}")
                return cached_data
        
        # Rate limiting: ensure we don't exceed 8 requests per second
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"⏱️ Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)
        
        try:
            # MET Norway API parameters
            params = {
                'lat': lat,
                'lon': lon,
                'altitude': altitude
            }
            
            logger.debug(f"🌐 MET Norway API request: {self.base_url}?lat={lat}&lon={lon}&altitude={altitude}")
            
            # Make the API request
            self.last_request_time = time.time()
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=15  # 15 second timeout for slow responses
            )
            
            # Handle response
            if response.status_code == 200:
                logger.info(f"✅ MET Norway API successful for {lat}, {lon}")
                data = response.json()
                
                # Cache the successful response
                self.cache[cache_key] = (time.time(), data)
                
                return data
                
            elif response.status_code == 400:
                logger.error(f"❌ MET Norway API: Bad request (400)")
                logger.error(f"   Parameters: lat={lat}, lon={lon}, altitude={altitude}")
                logger.error(f"   Response: {response.text[:200]}")
                
            elif response.status_code == 403:
                logger.error(f"❌ MET Norway API: Access forbidden (403)")
                logger.error(f"   Check your User-Agent: {self.user_agent[:80]}")
                logger.error(f"   It should contain contact email in parentheses")
                
            elif response.status_code == 404:
                logger.error(f"❌ MET Norway API: Not found (404)")
                logger.error(f"   Coordinates may be outside coverage area")
                
            elif response.status_code == 429:
                logger.error(f"❌ MET Norway API: Rate limit exceeded (429)")
                logger.error(f"   Wait before making more requests")
                
            else:
                logger.error(f"❌ MET Norway API error: HTTP {response.status_code}")
                logger.debug(f"   Response: {response.text[:200]}")
            
            return None
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ MET Norway API timeout for {lat}, {lon}")
            return None
            
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 MET Norway API connection error for {lat}, {lon}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 MET Norway API request failed: {e}")
            return None
            
        except Exception as e:
            logger.error(f"⚠️ Unexpected error in MET Norway API request: {e}")
            return None
    
    def get_current_weather(self, lat: float = None, lon: float = None) -> Optional[Dict[str, Any]]:
        """
        Get current weather data from MET Norway API
        
        Args:
            lat: Latitude (defaults to value from MET_LAT environment variable)
            lon: Longitude (defaults to value from MET_LON environment variable)
            
        Returns:
            Dictionary with weather data or None if API fails
        """
        try:
            # Use provided coordinates or environment defaults
            target_lat = lat if lat is not None else self.default_lat
            target_lon = lon if lon is not None else self.default_lon
            
            logger.info(f"🌤️ Fetching MET Norway weather for {target_lat}, {target_lon}")
            
            # Make API request
            api_data = self._make_api_request(target_lat, target_lon)
            
            if api_data:
                parsed_data = self._parse_weather_data(api_data, target_lat, target_lon)
                
                # Verify we got real data, not fallback
                if parsed_data.get('data_source') == 'met_norway_live':
                    logger.info(f"✅ Got live MET Norway data: {parsed_data.get('temperature_c')}°C, "
                              f"{parsed_data.get('wind_speed_ms')} m/s")
                    return parsed_data
                else:
                    logger.warning(f"⚠️ Got fallback data instead of live MET Norway data")
                    return parsed_data
            else:
                logger.error(f"❌ MET Norway API request failed for {target_lat}, {target_lon}")
                # Return empirical fallback
                return self._get_fallback_data(target_lat, target_lon, "API request failed")
                
        except Exception as e:
            logger.error(f"⚠️ Error in get_current_weather: {e}")
            # Return empirical fallback with error info
            lat_fallback = lat if lat is not None else self.default_lat
            lon_fallback = lon if lon is not None else self.default_lon
            return self._get_fallback_data(lat_fallback, lon_fallback, f"Exception: {str(e)[:100]}")
    
    def _parse_weather_data(self, api_data: Dict, lat: float, lon: float) -> Dict[str, Any]:
        """
        Parse MET Norway API response into standardized format
        
        Args:
            api_data: Raw API response from MET Norway
            lat: Latitude used in request
            lon: Longitude used in request
            
        Returns:
            Standardized weather data dictionary
        """
        try:
            # Check if API response has expected structure
            if 'properties' not in api_data:
                logger.error("Invalid MET Norway API response: missing 'properties'")
                raise ValueError("Invalid API response structure")
            
            properties = api_data['properties']
            timeseries = properties.get('timeseries', [])
            
            if not timeseries:
                logger.error("No timeseries data in MET Norway response")
                raise ValueError("No weather data in API response")
            
            # Get current data (first entry in timeseries)
            current = timeseries[0]
            current_time = current.get('time')
            data = current.get('data', {})
            instant = data.get('instant', {})
            details = instant.get('details', {})
            
            # Extract key weather parameters
            temperature_c = details.get('air_temperature')
            wind_speed_mps = details.get('wind_speed')
            wind_from_direction = details.get('wind_from_direction')
            humidity = details.get('relative_humidity')
            pressure = details.get('air_pressure_at_sea_level')
            cloud_area_fraction = details.get('cloud_area_fraction')
            
            # Try to get weather condition
            condition_code = 'clearsky'  # default
            condition_text = 'Clear Sky'
            
            # Check next 1 hour forecast for condition
            next_1h = data.get('next_1_hours', {})
            if next_1h:
                summary = next_1h.get('summary', {})
                condition_code = summary.get('symbol_code', 'clearsky')
                condition_text = self._get_condition_text(condition_code)
            
            # Convert wind direction to cardinal
            wind_direction = self._degrees_to_cardinal(wind_from_direction)
            
            # Get location name based on coordinates
            location_name = self._get_location_name(lat, lon)
            
            # Create comprehensive weather data structure
            weather_data = {
                # Core weather data
                'temperature_c': temperature_c,
                'wind_speed_ms': wind_speed_mps,
                'wind_direction_deg': wind_from_direction,
                'wind_direction': wind_direction,
                'condition': condition_text,
                'condition_code': condition_code,
                
                # Additional data if available
                'humidity_percent': humidity,
                'pressure_hpa': pressure,
                'cloud_cover_percent': cloud_area_fraction,
                
                # Location data
                'location': location_name,
                'city': location_name.split(',')[0] if ',' in location_name else 'Bergen',
                'coordinates': {'lat': lat, 'lon': lon},
                'country': 'Norway',
                
                # Metadata
                'timestamp': current_time,
                'data_source': 'met_norway_live',
                'source_url': 'https://api.met.no',
                'attribution': 'Data from Norwegian Meteorological Institute',
                'api_version': '2.0',
                
                # Display formatted data
                'display': {
                    'temperature': f"{round(temperature_c)}°C" if temperature_c is not None else 'N/A',
                    'wind': f"{round(wind_speed_mps)} m/s {wind_direction}" if wind_speed_mps is not None else 'N/A',
                    'condition': condition_text,
                    'location': location_name,
                    'time': current_time[:16].replace('T', ' ') if current_time else 'N/A'
                },
                
                # Units
                'units': {
                    'temperature': 'celsius',
                    'wind_speed': 'meters_per_second',
                    'wind_direction': 'degrees',
                    'pressure': 'hPa',
                    'humidity': 'percent'
                },
                
                # Diagnostics
                'environment_config': {
                    'lat_source': 'MET_LAT env var' if lat == self.default_lat else 'parameter',
                    'lon_source': 'MET_LON env var' if lon == self.default_lon else 'parameter',
                    'user_agent_configured': bool(self.user_agent)
                }
            }
            
            # Log successful parsing
            logger.debug(f"✅ Parsed MET Norway data for {location_name}")
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Failed to parse MET Norway data: {e}")
            logger.debug(f"API data keys: {list(api_data.keys()) if api_data else 'No data'}")
            
            # Return fallback data with error indication
            return self._get_fallback_data(lat, lon, f"Parse error: {str(e)[:100]}")
    
    def _degrees_to_cardinal(self, degrees: Optional[float]) -> str:
        """Convert wind direction in degrees to cardinal direction (N, NE, E, etc.)."""
        if degrees is None:
            return "N/A"
        
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _get_condition_text(self, symbol_code: str) -> str:
        """Convert MET Norway symbol code to human-readable weather condition."""
        if not symbol_code:
            return "Unknown"
        
        # Remove day/night suffix if present (day, night, polarday, polarnight)
        base_code = symbol_code
        for suffix in ['_day', '_night', '_polarday', '_polarnight']:
            if symbol_code.endswith(suffix):
                base_code = symbol_code.replace(suffix, '')
                break
        
        # MET Norway condition mapping (from official documentation)
        condition_map = {
            # Clear
            'clearsky': 'Clear Sky',
            'fair': 'Fair',
            
            # Cloudy
            'partlycloudy': 'Partly Cloudy',
            'cloudy': 'Cloudy',
            
            # Rain
            'lightrainshowers': 'Light Rain Showers',
            'rainshowers': 'Rain Showers',
            'heavyrainshowers': 'Heavy Rain Showers',
            'lightrain': 'Light Rain',
            'rain': 'Rain',
            'heavyrain': 'Heavy Rain',
            
            # Sleet
            'lightsleet': 'Light Sleet',
            'sleet': 'Sleet',
            'heavysleet': 'Heavy Sleet',
            'lightsleetshowers': 'Light Sleet Showers',
            'sleetshowers': 'Sleet Showers',
            'heavysleetshowers': 'Heavy Sleet Showers',
            
            # Snow
            'lightsnow': 'Light Snow',
            'snow': 'Snow',
            'heavysnow': 'Heavy Snow',
            'lightsnowshowers': 'Light Snow Showers',
            'snowshowers': 'Snow Showers',
            'heavysnowshowers': 'Heavy Snow Showers',
            
            # Thunder
            'lightrainshowersandthunder': 'Light Rain Showers and Thunder',
            'rainshowersandthunder': 'Rain Showers and Thunder',
            'heavyrainshowersandthunder': 'Heavy Rain Showers and Thunder',
            'lightrainandthunder': 'Light Rain and Thunder',
            'rainandthunder': 'Rain and Thunder',
            'heavyrainandthunder': 'Heavy Rain and Thunder',
            'lightsleetandthunder': 'Light Sleet and Thunder',
            'sleetandthunder': 'Sleet and Thunder',
            'heavysleetandthunder': 'Heavy Sleet and Thunder',
            'lightsnowandthunder': 'Light Snow and Thunder',
            'snowandthunder': 'Snow and Thunder',
            'heavysnowandthunder': 'Heavy Snow and Thunder',
            
            # Fog
            'fog': 'Fog'
        }
        
        return condition_map.get(base_code, base_code.replace('_', ' ').title())
    
    def _get_location_name(self, lat: float, lon: float) -> str:
        """Get approximate location name based on coordinates."""
        # Norwegian cities with their approximate coordinates
        norwegian_cities = [
            {'name': 'Bergen', 'lat': 60.3913, 'lon': 5.3221},
            {'name': 'Oslo', 'lat': 59.9139, 'lon': 10.7522},
            {'name': 'Stavanger', 'lat': 58.9699, 'lon': 5.7331},
            {'name': 'Trondheim', 'lat': 63.4305, 'lon': 10.3951},
            {'name': 'Ålesund', 'lat': 62.4722, 'lon': 6.1497},
            {'name': 'Tromsø', 'lat': 69.6496, 'lon': 18.9570},
            {'name': 'Bodø', 'lat': 67.2804, 'lon': 14.4049},
            {'name': 'Kristiansand', 'lat': 58.1467, 'lon': 7.9958},
            {'name': 'Drammen', 'lat': 59.7441, 'lon': 10.2045},
            {'name': 'Fredrikstad', 'lat': 59.2181, 'lon': 10.9298},
            {'name': 'Sandefjord', 'lat': 59.1312, 'lon': 10.2167},
            {'name': 'Åndalsnes', 'lat': 62.5675, 'lon': 7.6870},
            {'name': 'Flekkefjord', 'lat': 58.2970, 'lon': 6.6605}
        ]
        
        # Find closest city
        closest_city = None
        min_distance = float('inf')
        
        for city in norwegian_cities:
            # Simple distance calculation (good enough for city matching)
            distance = ((lat - city['lat']) ** 2 + (lon - city['lon']) ** 2) ** 0.5
            
            # Convert to approximate kilometers (1 degree ≈ 111 km)
            distance_km = distance * 111
            
            # If within 20 km of a known city, use it
            if distance_km < 20 and distance < min_distance:
                min_distance = distance
                closest_city = f"{city['name']}, Norway"
        
        return closest_city or f"Position ({lat:.4f}, {lon:.4f})"
    
    def _get_fallback_data(self, lat: float, lon: float, error: str = None) -> Dict[str, Any]:
        """
        Get fallback empirical weather data when MET Norway API fails.
        Uses location-based seasonal averages as fallback.
        """
        logger.warning(f"⚠️ Using fallback weather data: {error}")
        
        # Get location for empirical data
        location_name = self._get_location_name(lat, lon)
        city_name = location_name.split(',')[0].lower() if ',' in location_name else 'bergen'
        
        # Location-based empirical data (winter averages for Norway)
        # Based on historical averages for January
        empirical_data = {
            'bergen': {'temp': 8.5, 'wind': 5.2, 'condition': 'Rain Showers'},
            'oslo': {'temp': 2.5, 'wind': 3.5, 'condition': 'Partly Cloudy'},
            'stavanger': {'temp': 7.5, 'wind': 5.5, 'condition': 'Cloudy'},
            'trondheim': {'temp': 3.5, 'wind': 4.5, 'condition': 'Light Snow'},
            'ålesund': {'temp': 6.5, 'wind': 6.0, 'condition': 'Rain'},
            'tromsø': {'temp': -4.0, 'wind': 4.0, 'condition': 'Snow'},
            'bodø': {'temp': -1.5, 'wind': 5.5, 'condition': 'Snow Showers'},
            'kristiansand': {'temp': 5.0, 'wind': 4.5, 'condition': 'Light Rain'},
            'drammen': {'temp': 3.0, 'wind': 3.0, 'condition': 'Fair'},
            'fredrikstad': {'temp': 2.0, 'wind': 3.5, 'condition': 'Fair'},
            'sandefjord': {'temp': 4.5, 'wind': 4.0, 'condition': 'Light Rain'},
            'åndalsnes': {'temp': 5.5, 'wind': 4.0, 'condition': 'Rain'},
            'flekkefjord': {'temp': 6.0, 'wind': 5.0, 'condition': 'Rain'}
        }
        
        # Get empirical values for this location or use Bergen as default
        empirical = empirical_data.get(city_name, empirical_data['bergen'])
        
        # Determine wind direction based on location (simplified)
        wind_directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        wind_idx = hash(f"{lat}{lon}") % len(wind_directions)
        wind_direction = wind_directions[wind_idx]
        
        return {
            # Core weather data
            'temperature_c': empirical['temp'],
            'wind_speed_ms': empirical['wind'],
            'wind_direction': wind_direction,
            'condition': empirical['condition'],
            
            # Location data
            'location': location_name,
            'city': location_name.split(',')[0] if ',' in location_name else 'Bergen',
            'coordinates': {'lat': lat, 'lon': lon},
            'country': 'Norway',
            
            # Metadata
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_source': 'fallback_empirical',
            'fallback_reason': error or 'MET Norway API unavailable',
            'api_version': 'fallback',
            
            # Display formatted data
            'display': {
                'temperature': f"{round(empirical['temp'])}°C",
                'wind': f"{round(empirical['wind'])} m/s {wind_direction}",
                'condition': empirical['condition'],
                'location': location_name,
                'time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
            },
            
            # Units
            'units': {
                'temperature': 'celsius',
                'wind_speed': 'meters_per_second'
            },
            
            # Diagnostics
            'warning': 'Using fallback empirical data - MET Norway API may be unavailable'
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status and connectivity information.
        Useful for monitoring and debugging.
        """
        # Test API connectivity
        test_result = self.get_current_weather(self.default_lat, self.default_lon)
        
        # Check cache status
        cache_info = {
            'entries': len(self.cache),
            'max_age_seconds': self.cache_duration
        }
        
        # Determine connectivity status
        if test_result and test_result.get('data_source') == 'met_norway_live':
            connectivity = 'connected'
            data_quality = 'live'
        elif test_result:
            connectivity = 'degraded'
            data_quality = 'fallback'
        else:
            connectivity = 'disconnected'
            data_quality = 'none'
        
        # Safely format user agent for logging
        user_agent_safe = self.user_agent[:60] + "..." if len(self.user_agent) > 60 else self.user_agent
        
        status = {
            'service': 'met_norway_weather',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'api_url': self.base_url,
            'coordinates': {'lat': self.default_lat, 'lon': self.default_lon},
            'connectivity': connectivity,
            'data_quality': data_quality,
            
            'environment_variables': {
                'MET_USER_AGENT_set': bool(os.environ.get('MET_USER_AGENT')),
                'MET_LAT_set': bool(os.environ.get('MET_LAT')),
                'MET_LON_set': bool(os.environ.get('MET_LON')),
                'user_agent_preview': user_agent_safe
            },
            
            'configuration': {
                'cache_entries': cache_info['entries'],
                'cache_duration_seconds': cache_info['max_age_seconds'],
                'rate_limit_rps': 8,
                'min_request_interval': self.min_request_interval
            },
            
            'attribution': 'Norwegian Meteorological Institute (MET Norway)',
            'documentation': 'https://api.met.no/weatherapi/locationforecast/2.0/documentation',
            'license': 'Data licensed under Norwegian Licence for Open Government Data (NLOD)'
        }
        
        # Add test result if available
        if test_result:
            status['test_result'] = {
                'data_source': test_result.get('data_source'),
                'temperature_c': test_result.get('temperature_c'),
                'wind_speed_ms': test_result.get('wind_speed_ms'),
                'location': test_result.get('location'),
                'condition': test_result.get('condition')
            }
        
        # Add warnings if any
        warnings = []
        if not os.environ.get('MET_USER_AGENT'):
            warnings.append('MET_USER_AGENT not set in .env file')
        elif '(' not in os.environ.get('MET_USER_AGENT', ''):
            warnings.append('MET_USER_AGENT should contain email in parentheses')
        
        if warnings:
            status['warnings'] = warnings
        
        return status
    
    def clear_cache(self):
        """Clear the response cache."""
        self.cache.clear()
        logger.info("🧹 MET Norway cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache."""
        return {
            'entries': len(self.cache),
            'max_age_seconds': self.cache_duration,
            'keys': list(self.cache.keys())[:5] if self.cache else []
        }


# Create global service instance
# This instance will use environment variables from .env
met_norway_service = METNorwayService()