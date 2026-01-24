# backend/services/met_norway_service.py
"""
MET Norway Weather Service - Real-time weather data from Norwegian Meteorological Institute
Uses official MET Norway API with proper attribution
Uses environment variables from .env for configuration
"""

import os
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class METNorwayService:
    """
    Service for fetching real weather data from MET Norway API
    Official documentation: https://api.met.no/
    
    Environment variables required (from .env):
        - MET_USER_AGENT: User agent string for API requests
        - MET_LAT: Default latitude (e.g., 60.39 for Bergen)
        - MET_LON: Default longitude (e.g., 5.32 for Bergen)
    """
    
    def __init__(self):
        """Initialize MET Norway service using environment variables."""
        
        # Get configuration from environment variables
        self.base_url = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
        self.user_agent = os.environ.get('MET_USER_AGENT', '')
        
        if not self.user_agent:
            logger.warning("MET_USER_AGENT not set in environment variables")
            # Use a generic but compliant user agent
            self.user_agent = "BergNavnMaritimeDashboard/1.0 (contact via env MET_USER_AGENT)"
        
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json'
        }
        
        # Get coordinates from environment variables
        try:
            self.default_lat = float(os.environ.get('MET_LAT', '60.3913'))
            self.default_lon = float(os.environ.get('MET_LON', '5.3221'))
        except ValueError:
            logger.error("Invalid MET_LAT or MET_LON in environment variables")
            self.default_lat = 60.3913  # Bergen fallback
            self.default_lon = 5.3221   # Bergen fallback
        
        # Log configuration (safely, without exposing sensitive info)
        user_agent_safe = self.user_agent[:50] + "..." if len(self.user_agent) > 50 else self.user_agent
        logger.info(f"🌤️ MET Norway Service initialized")
        logger.info(f"  • Coordinates: {self.default_lat}, {self.default_lon}")
        logger.info(f"  • User-Agent: {user_agent_safe}")
        
        # Verify environment variables
        self._verify_env_config()
    
    def _verify_env_config(self):
        """Verify that required environment variables are properly configured."""
        env_checks = {
            'MET_USER_AGENT': os.environ.get('MET_USER_AGENT'),
            'MET_LAT': os.environ.get('MET_LAT'),
            'MET_LON': os.environ.get('MET_LON')
        }
        
        missing = [key for key, value in env_checks.items() if not value]
        if missing:
            logger.warning(f"Missing environment variables: {', '.join(missing)}")
            logger.warning("Using fallback values - update your .env file")
        else:
            logger.info("✅ All MET Norway environment variables configured")
    
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
            
            logger.info(f"🌤️ Fetching MET Norway weather for coordinates: {target_lat}, {target_lon}")
            
            # Make API request to MET Norway
            params = {
                'lat': target_lat,
                'lon': target_lon
            }
            
            # Log request details (without exposing full User-Agent)
            logger.debug(f"MET Norway API request: {self.base_url} with params {params}")
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10  # 10 second timeout
            )
            
            # Handle response
            if response.status_code == 200:
                logger.info("✅ MET Norway API response successful")
                data = response.json()
                return self._parse_weather_data(data, target_lat, target_lon)
            elif response.status_code == 403:
                logger.error("❌ MET Norway API: Access forbidden - check User-Agent in .env")
                logger.error(f"Current User-Agent starts with: {self.user_agent[:30]}...")
                return None
            elif response.status_code == 429:
                logger.error("❌ MET Norway API: Rate limit exceeded")
                return None
            else:
                logger.error(f"❌ MET Norway API error: HTTP {response.status_code}")
                logger.debug(f"Response text: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("⏱️ MET Norway API timeout (10 seconds)")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("🔌 MET Norway API connection error")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 MET Norway API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"⚠️ Unexpected error in MET Norway service: {e}")
            return None
    
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
            # Navigate the MET Norway JSON structure
            timeseries = api_data.get('properties', {}).get('timeseries', [])
            
            if not timeseries:
                logger.error("No timeseries data in MET Norway response")
                raise ValueError("No weather data in API response")
            
            # Get current data (first entry in timeseries)
            current = timeseries[0]
            data = current.get('data', {})
            instant = data.get('instant', {})
            details = instant.get('details', {})
            
            # Extract key weather parameters
            temperature_c = details.get('air_temperature')
            wind_speed_mps = details.get('wind_speed')
            wind_from_direction = details.get('wind_from_direction')
            
            # Get weather condition for next hour
            next_1h = data.get('next_1_hours', {}).get('summary', {}).get('symbol_code', '')
            
            # Convert wind direction to cardinal
            wind_direction = self._degrees_to_cardinal(wind_from_direction)
            
            # Get location name based on coordinates
            location_name = self._get_location_name(lat, lon)
            
            # Create standardized weather data structure
            weather_data = {
                'temperature_c': temperature_c,
                'temperature_display': f"{round(temperature_c)}°C" if temperature_c is not None else None,
                'wind_speed_ms': wind_speed_mps,
                'wind_display': f"{round(wind_speed_mps)} m/s" if wind_speed_mps is not None else None,
                'wind_direction_deg': wind_from_direction,
                'wind_direction': wind_direction,
                'condition': self._get_condition_text(next_1h),
                'condition_code': next_1h,
                'location': location_name,
                'city': location_name.split(',')[0] if location_name else 'Bergen',
                'coordinates': {'lat': lat, 'lon': lon},
                'timestamp': current.get('time'),
                'data_source': 'met_norway_live',
                'source_url': 'https://api.met.no',
                'attribution': 'Data from Norwegian Meteorological Institute',
                'units': {
                    'temperature': 'celsius',
                    'wind_speed': 'meters_per_second',
                    'wind_direction': 'degrees'
                },
                'environment_config': {
                    'lat_source': 'MET_LAT env var' if lat == self.default_lat else 'parameter',
                    'lon_source': 'MET_LON env var' if lon == self.default_lon else 'parameter'
                }
            }
            
            # Log successful data retrieval
            logger.info(f"✅ MET Norway data retrieved: {temperature_c}°C, {wind_speed_mps} m/s at {location_name}")
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Failed to parse MET Norway data: {e}")
            # Return fallback data with error indication
            return self._get_fallback_data(lat, lon, error=str(e))
    
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
        
        # Remove day/night suffix if present
        base_code = symbol_code.split('_')[0] if '_' in symbol_code else symbol_code
        
        # MET Norway condition mapping
        condition_map = {
            'clearsky': 'Clear Sky',
            'fair': 'Fair',
            'partlycloudy': 'Partly Cloudy',
            'cloudy': 'Cloudy',
            'lightrainshowers': 'Light Rain Showers',
            'rainshowers': 'Rain Showers',
            'heavyrainshowers': 'Heavy Rain Showers',
            'lightrain': 'Light Rain',
            'rain': 'Rain',
            'heavyrain': 'Heavy Rain',
            'lightsleet': 'Light Sleet',
            'sleet': 'Sleet',
            'heavysleet': 'Heavy Sleet',
            'lightsnow': 'Light Snow',
            'snow': 'Snow',
            'heavysnow': 'Heavy Snow',
            'fog': 'Fog',
            'snowthunder': 'Snow Thunder',
            'rainthunder': 'Rain Thunder'
        }
        
        return condition_map.get(base_code, base_code.replace('_', ' ').title())
    
    def _get_location_name(self, lat: float, lon: float) -> str:
        """Get approximate location name based on coordinates."""
        # Norwegian cities with their coordinates
        cities = {
            (60.3913, 5.3221): 'Bergen, Norway',
            (59.9139, 10.7522): 'Oslo, Norway',
            (58.9699, 5.7331): 'Stavanger, Norway',
            (63.4305, 10.3951): 'Trondheim, Norway',
            (62.4722, 6.1497): 'Ålesund, Norway',
            (62.5675, 7.6870): 'Åndalsnes, Norway',
            (59.7441, 10.2045): 'Drammen, Norway',
            (58.1467, 7.9958): 'Kristiansand, Norway',
            (59.1312, 10.2167): 'Sandefjord, Norway',
            (58.2970, 6.6605): 'Flekkefjord, Norway'
        }
        
        # Find closest city using simple distance calculation
        closest_city = None
        min_distance = float('inf')
        
        for city_coords, city_name in cities.items():
            distance = abs(lat - city_coords[0]) + abs(lon - city_coords[1])
            if distance < min_distance:
                min_distance = distance
                closest_city = city_name
        
        return closest_city or f"Position ({lat:.4f}, {lon:.4f})"
    
    def _get_fallback_data(self, lat: float, lon: float, error: str = None) -> Dict[str, Any]:
        """
        Get fallback empirical weather data when MET Norway API fails.
        Uses location-based seasonal averages as fallback.
        """
        logger.warning(f"⚠️ Using fallback weather data due to: {error}")
        
        # Location-based empirical data (winter averages for Norway)
        location_empirical = {
            'bergen': {'temp': 8.5, 'wind': 5.2},
            'oslo': {'temp': 2.5, 'wind': 3.5},
            'stavanger': {'temp': 7.5, 'wind': 5.5},
            'trondheim': {'temp': 3.5, 'wind': 4.5},
            'alesund': {'temp': 6.5, 'wind': 6.0},
            'andalsnes': {'temp': 5.5, 'wind': 4.0},
            'drammen': {'temp': 3.0, 'wind': 3.0},
            'kristiansand': {'temp': 5.0, 'wind': 4.5},
            'sandefjord': {'temp': 4.5, 'wind': 4.0},
            'flekkefjord': {'temp': 6.0, 'wind': 5.0}
        }
        
        # Get location name for fallback data
        location_name = self._get_location_name(lat, lon)
        city_key = location_name.split(',')[0].lower() if ',' in location_name else 'bergen'
        
        # Get empirical values for this location
        empirical = location_empirical.get(city_key, location_empirical['bergen'])
        
        return {
            'temperature_c': empirical['temp'],
            'temperature_display': f"{round(empirical['temp'])}°C",
            'wind_speed_ms': empirical['wind'],
            'wind_display': f"{round(empirical['wind'])} m/s",
            'wind_direction': 'NW',
            'location': location_name,
            'city': location_name.split(',')[0] if location_name else 'Bergen',
            'coordinates': {'lat': lat, 'lon': lon},
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_source': 'fallback_empirical',
            'fallback_reason': error or 'MET Norway API unavailable',
            'units': {
                'temperature': 'celsius',
                'wind_speed': 'meters_per_second'
            }
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status and connectivity information.
        Useful for monitoring and debugging.
        """
        # Test API connectivity
        test_result = self.get_current_weather(self.default_lat, self.default_lon)
        
        # Safely format user agent for logging
        user_agent_safe = self.user_agent[:40] + "..." if len(self.user_agent) > 40 else self.user_agent
        
        status = {
            'service': 'met_norway_weather',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'api_url': self.base_url,
            'coordinates': {'lat': self.default_lat, 'lon': self.default_lon},
            'connectivity': 'connected' if test_result and test_result.get('data_source') == 'met_norway_live' else 'disconnected',
            'environment_variables': {
                'MET_USER_AGENT_set': bool(os.environ.get('MET_USER_AGENT')),
                'MET_LAT_set': bool(os.environ.get('MET_LAT')),
                'MET_LON_set': bool(os.environ.get('MET_LON'))
            },
            'user_agent_preview': user_agent_safe,
            'attribution': 'Norwegian Meteorological Institute (MET Norway)'
        }
        
        # Add test result if available
        if test_result:
            status['test_result'] = {
                'data_source': test_result.get('data_source'),
                'temperature': test_result.get('temperature_c'),
                'wind_speed': test_result.get('wind_speed_ms'),
                'location': test_result.get('location')
            }
        
        return status


# Create global service instance
# This instance will use environment variables from .env
met_norway_service = METNorwayService()