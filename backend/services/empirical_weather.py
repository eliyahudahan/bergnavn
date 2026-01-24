# backend/services/empirical_weather.py
"""
Empirical Weather Service - Uses MET Norway as primary data source
Falls back to empirical data only when MET Norway is unavailable
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    # Try to import the new MET Norway service
    from .met_norway_service import met_norway_service
    MET_NORWAY_AVAILABLE = True
    logger.info("✅ MET Norway service available")
except ImportError as e:
    MET_NORWAY_AVAILABLE = False
    logger.warning(f"⚠️ MET Norway service not available: {e}")


class EmpiricalWeatherService:
    """
    Weather service that prioritizes MET Norway data
    Falls back to empirical data only when necessary
    """
    
    def __init__(self):
        logger.info("🌤️ Empirical Weather Service initialized")
        if MET_NORWAY_AVAILABLE:
            logger.info("  • Primary source: MET Norway (real-time)")
            logger.info("  • Fallback: Location-based empirical data")
        else:
            logger.warning("  • Primary source: Location-based empirical data only")
    
    def get_marine_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get marine weather data for specified coordinates
        
        Priority:
        1. MET Norway API (real-time data)
        2. Location-based empirical data (fallback)
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            
        Returns:
            Weather data dictionary with source indication
        """
        logger.info(f"🌤️ Requesting weather for coordinates: {lat}, {lon}")
        
        # Priority 1: Try MET Norway API
        if MET_NORWAY_AVAILABLE:
            try:
                weather = met_norway_service.get_current_weather(lat, lon)
                
                if weather and weather.get('data_source') == 'met_norway_live':
                    logger.info(f"✅ Using MET Norway live data")
                    return weather
                elif weather:
                    logger.info(f"⚠️ Using MET Norway fallback data")
                    return weather
                else:
                    logger.warning("MET Norway returned no data, using empirical fallback")
            except Exception as e:
                logger.error(f"MET Norway service error: {e}")
                logger.info("Falling back to empirical data")
        
        # Priority 2: Empirical fallback data
        return self._get_empirical_fallback(lat, lon)
    
    def _get_empirical_fallback(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get empirical weather data based on location and season
        Used only when MET Norway API is unavailable
        """
        logger.warning(f"⚠️ Using empirical fallback weather for coordinates: {lat}, {lon}")
        
        # Norwegian cities with seasonal average data
        city_data = {
            'bergen': {'name': 'Bergen', 'temp': 8.5, 'wind': 5.2, 'coastal': True},
            'oslo': {'name': 'Oslo', 'temp': 2.5, 'wind': 3.5, 'coastal': False},
            'stavanger': {'name': 'Stavanger', 'temp': 7.5, 'wind': 5.5, 'coastal': True},
            'trondheim': {'name': 'Trondheim', 'temp': 3.5, 'wind': 4.5, 'coastal': True},
            'alesund': {'name': 'Ålesund', 'temp': 6.5, 'wind': 6.0, 'coastal': True},
            'andalsnes': {'name': 'Åndalsnes', 'temp': 5.5, 'wind': 4.0, 'coastal': True},
            'drammen': {'name': 'Drammen', 'temp': 3.0, 'wind': 3.0, 'coastal': False},
            'kristiansand': {'name': 'Kristiansand', 'temp': 5.0, 'wind': 4.5, 'coastal': True},
            'sandefjord': {'name': 'Sandefjord', 'temp': 4.5, 'wind': 4.0, 'coastal': True},
            'flekkefjord': {'name': 'Flekkefjord', 'temp': 6.0, 'wind': 5.0, 'coastal': True}
        }
        
        # City coordinates for matching
        city_coords = {
            'bergen': (60.3913, 5.3221),
            'oslo': (59.9139, 10.7522),
            'stavanger': (58.9699, 5.7331),
            'trondheim': (63.4305, 10.3951),
            'alesund': (62.4722, 6.1497),
            'andalsnes': (62.5675, 7.6870),
            'drammen': (59.7441, 10.2045),
            'kristiansand': (58.1467, 7.9958),
            'sandefjord': (59.1312, 10.2167),
            'flekkefjord': (58.2970, 6.6605)
        }
        
        # Find closest city
        closest_city = 'bergen'
        min_distance = float('inf')
        
        for city_key, coords in city_coords.items():
            distance = abs(lat - coords[0]) + abs(lon - coords[1])
            if distance < min_distance:
                min_distance = distance
                closest_city = city_key
        
        # Get data for closest city
        city_info = city_data.get(closest_city, city_data['bergen'])
        
        # Determine wind direction (coastal cities tend to have NW winds in winter)
        wind_direction = 'NW' if city_info['coastal'] else 'Variable'
        
        return {
            'temperature_c': city_info['temp'],
            'temperature_display': f"{round(city_info['temp'])}°C",
            'wind_speed_ms': city_info['wind'],
            'wind_display': f"{round(city_info['wind'])} m/s",
            'wind_direction': wind_direction,
            'city': city_info['name'],
            'location': f"{city_info['name']}, Norway (empirical)",
            'coordinates': {'lat': lat, 'lon': lon},
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_source': 'fallback_empirical',
            'fallback_reason': 'MET Norway API unavailable',
            'notes': 'Based on seasonal averages for this location',
            'units': {
                'temperature': 'celsius',
                'wind_speed': 'meters_per_second'
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the weather service configuration."""
        info = {
            'service': 'empirical_weather',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'primary_source': 'MET Norway API' if MET_NORWAY_AVAILABLE else 'Empirical data only',
            'met_norway_available': MET_NORWAY_AVAILABLE,
            'fallback_strategy': 'Location-based seasonal averages'
        }
        
        if MET_NORWAY_AVAILABLE:
            try:
                met_status = met_norway_service.get_service_status()
                info['met_norway_status'] = met_status
            except Exception as e:
                info['met_norway_status'] = f"Error: {e}"
        
        return info


# Create global service instance
empirical_weather_service = EmpiricalWeatherService()