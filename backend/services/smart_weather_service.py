# backend/services/smart_weather_service.py
"""
Smart Weather Service - Uses MET Norway first, OpenWeatherMap as fallback
Provides accurate weather data for Norwegian coastal areas
"""

import os
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time

logger = logging.getLogger(__name__)

class SmartWeatherService:
    """
    Smart weather service for Norwegian maritime operations
    Priority: MET Norway → OpenWeatherMap → Empirical data
    """
    
    def __init__(self):
        # MET Norway configuration
        self.met_user_agent = os.getenv(
            "MET_USER_AGENT", 
            "BergNavnMaritimeDashboard/2.0 (https://berg-navn.no; contact@berg-navn.no)"
        )
        
        # OpenWeatherMap configuration
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY", "")
        
        # Default location (Bergen)
        self.default_lat = float(os.getenv("MET_LAT", "60.3913"))
        self.default_lon = float(os.getenv("MET_LON", "5.3221"))
        
        # Cache for weather data (10 minutes)
        self._cache = {}
        self._cache_duration = timedelta(minutes=10)
        
        logger.info("✅ SmartWeatherService initialized")
        logger.info(f"   MET Norway: {'✅ Ready' if self.met_user_agent else '⚠️ No User-Agent'}")
        logger.info(f"   OpenWeatherMap: {'✅ Ready' if self.openweather_api_key else '⚠️ No API Key'}")
    
    def get_weather_for_bergen(self) -> Dict:
        """
        Get weather data for Bergen using all available sources
        
        Returns:
            Dictionary with comprehensive weather data
        """
        cache_key = "bergen_weather"
        
        # Check cache first
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if datetime.now() - cached_time < self._cache_duration:
                logger.debug("📦 Using cached weather data")
                return cached_data
        
        # Try sources in order
        weather_data = None
        source = "unknown"
        
        # 1. Try MET Norway
        weather_data = self._try_met_norway(self.default_lat, self.default_lon)
        if weather_data:
            source = "met_norway"
            logger.info("🌤️ Got weather from MET Norway")
        
        # 2. Try OpenWeatherMap if MET Norway failed
        if not weather_data and self.openweather_api_key:
            weather_data = self._try_openweather(self.default_lat, self.default_lon)
            if weather_data:
                source = "openweather"
                logger.info("🌤️ Got weather from OpenWeatherMap")
        
        # 3. Fallback to empirical data
        if not weather_data:
            weather_data = self._get_empirical_weather()
            source = "empirical"
            logger.info("🌤️ Using empirical weather data")
        
        # Add metadata
        if weather_data:
            weather_data['source'] = source
            weather_data['timestamp'] = datetime.now().isoformat()
            weather_data['location'] = {
                'city': 'Bergen',
                'lat': self.default_lat,
                'lon': self.default_lon,
                'country': 'Norway'
            }
            
            # Cache the result
            self._cache[cache_key] = (datetime.now(), weather_data)
        
        return weather_data or {}
    
    def _try_met_norway(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Try to get weather data from MET Norway API
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Weather data dict or None if failed
        """
        try:
            # MET Norway Locationforecast API (compact format)
            url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
            
            headers = {
                'User-Agent': self.met_user_agent,
                'Accept': 'application/json'
            }
            
            params = {
                'lat': f"{lat:.4f}",
                'lon': f"{lon:.4f}"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract current weather from MET Norway response
                # MET Norway returns timeseries, get the first (current) entry
                if 'properties' in data and 'timeseries' in data['properties']:
                    timeseries = data['properties']['timeseries']
                    if timeseries and len(timeseries) > 0:
                        current = timeseries[0]['data']['instant']['details']
                        
                        # Convert to our standard format
                        weather_data = {
                            'temperature_c': current.get('air_temperature', 0),
                            'wind_speed_ms': current.get('wind_speed', 0),
                            'wind_direction': current.get('wind_from_direction', 0),
                            'air_pressure_hpa': current.get('air_pressure_at_sea_level', 1013),
                            'humidity_percent': current.get('relative_humidity', 50),
                            'cloud_area_fraction': current.get('cloud_area_fraction', 0)
                        }
                        
                        # Try to get precipitation if available
                        if 'next_1_hours' in timeseries[0]['data']:
                            precipitation = timeseries[0]['data']['next_1_hours']['details'].get('precipitation_amount', 0)
                            weather_data['precipitation_mm'] = precipitation
                        
                        return weather_data
            
            logger.debug(f"MET Norway API returned {response.status_code}")
            return None
            
        except Exception as e:
            logger.debug(f"MET Norway API error: {e}")
            return None
    
    def _try_openweather(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Try to get weather data from OpenWeatherMap API
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Weather data dict or None if failed
        """
        if not self.openweather_api_key:
            return None
            
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric'  # Celsius
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                weather_data = {
                    'temperature_c': data['main']['temp'],
                    'feels_like_c': data['main']['feels_like'],
                    'wind_speed_ms': data['wind']['speed'],
                    'wind_direction': data['wind'].get('deg', 0),
                    'air_pressure_hpa': data['main']['pressure'],
                    'humidity_percent': data['main']['humidity'],
                    'cloudiness_percent': data['clouds']['all'],
                    'weather_description': data['weather'][0]['description'],
                    'weather_icon': data['weather'][0]['icon']
                }
                
                # Add precipitation if available
                if 'rain' in data:
                    weather_data['precipitation_mm'] = data['rain'].get('1h', 0)
                
                return weather_data
            
            logger.debug(f"OpenWeatherMap API returned {response.status_code}")
            return None
            
        except Exception as e:
            logger.debug(f"OpenWeatherMap API error: {e}")
            return None
    
    def _get_empirical_weather(self) -> Dict:
        """
        Get empirical weather data based on season and time
        Uses realistic averages for Bergen, Norway
        """
        now = datetime.now()
        month = now.month
        hour = now.hour
        
        # Bergen climate data (averages)
        # Source: Norwegian Meteorological Institute
        monthly_averages = {
            1: {'temp': 1.3, 'precip': 190, 'wind': 4.5},   # January
            2: {'temp': 1.6, 'precip': 152, 'wind': 4.4},   # February
            3: {'temp': 3.5, 'precip': 114, 'wind': 4.3},   # March
            4: {'temp': 6.3, 'precip': 94,  'wind': 4.0},   # April
            5: {'temp': 10.4, 'precip': 86,  'wind': 3.7},  # May
            6: {'temp': 13.4, 'precip': 92,  'wind': 3.5},  # June
            7: {'temp': 15.2, 'precip': 132, 'wind': 3.4},  # July
            8: {'temp': 14.9, 'precip': 165, 'wind': 3.6},  # August
            9: {'temp': 11.9, 'precip': 220, 'wind': 4.0},  # September
            10: {'temp': 8.4, 'precip': 247, 'wind': 4.3},  # October
            11: {'temp': 4.7, 'precip': 234, 'wind': 4.4},  # November
            12: {'temp': 2.2, 'precip': 216, 'wind': 4.5}   # December
        }
        
        # Get base values for current month
        base = monthly_averages.get(month, {'temp': 8.0, 'precip': 150, 'wind': 4.0})
        
        # Add some realistic variation
        import random
        temp_variation = random.uniform(-3.0, 3.0)
        wind_variation = random.uniform(-1.0, 1.0)
        
        # Diurnal variation (colder at night)
        if 0 <= hour < 6:  # Night
            temp_variation -= 2.0
        elif 12 <= hour < 15:  # Afternoon
            temp_variation += 2.0
        
        current_temp = base['temp'] + temp_variation
        current_wind = max(0.5, base['wind'] + wind_variation)  # Minimum 0.5 m/s
        
        # Weather conditions based on precipitation
        precipitation_chance = base['precip'] / 300  # Normalize to 0-1
        
        if random.random() < precipitation_chance:
            condition = "Light rain" if base['precip'] < 150 else "Rain"
            precip_mm = random.uniform(0.1, 5.0)
        else:
            condition = "Partly cloudy" if random.random() < 0.7 else "Clear"
            precip_mm = 0.0
        
        return {
            'temperature_c': round(current_temp, 1),
            'wind_speed_ms': round(current_wind, 1),
            'wind_direction': random.randint(0, 360),
            'air_pressure_hpa': random.randint(990, 1020),
            'humidity_percent': random.randint(60, 95),
            'precipitation_mm': round(precip_mm, 1),
            'condition': condition,
            'is_empirical': True
        }
    
    def get_weather_display_data(self) -> Dict:
        """
        Get formatted weather data for dashboard display
        
        Returns:
            Formatted dictionary ready for frontend display
        """
        weather = self.get_weather_for_bergen()
        
        if not weather:
            return {
                'display': {
                    'temperature': '--°C',
                    'wind': '-- m/s',
                    'location': 'Bergen',
                    'condition': 'No data',
                    'icon': 'cloud'
                },
                'data_source': 'error',
                'timestamp': datetime.now().isoformat()
            }
        
        # Format for display
        display_data = {
            'display': {
                'temperature': f"{weather.get('temperature_c', 0):.0f}°C",
                'wind': f"{weather.get('wind_speed_ms', 0):.0f} m/s",
                'location': 'Bergen, Norway',
                'condition': weather.get('condition', 'Unknown'),
                'icon': self._get_weather_icon(weather)
            },
            'data': weather,
            'data_source': weather.get('source', 'unknown'),
            'timestamp': weather.get('timestamp', datetime.now().isoformat())
        }
        
        return display_data
    
    def _get_weather_icon(self, weather: Dict) -> str:
        """
        Convert weather data to icon name
        
        Args:
            weather: Weather data dictionary
            
        Returns:
            Icon name for display
        """
        condition = str(weather.get('condition', '')).lower()
        
        if 'rain' in condition:
            return 'rain'
        elif 'snow' in condition:
            return 'snow'
        elif 'clear' in condition or 'sun' in condition:
            return 'sun'
        elif 'cloud' in condition:
            return 'cloud'
        else:
            # Default based on temperature
            temp = weather.get('temperature_c', 10)
            if temp > 20:
                return 'sun'
            elif temp > 10:
                return 'cloud-sun'
            else:
                return 'cloud'

# Global instance
smart_weather_service = SmartWeatherService()