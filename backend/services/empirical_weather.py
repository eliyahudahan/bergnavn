"""
Empirical weather service using MET Norway API.
Real, verifiable weather data for Norwegian coastal waters.
"""

import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EmpiricalWeatherService:
    """
    Empirical weather service using MET Norway's open API.
    Provides real weather data for maritime operations.
    """
    
    MET_API_BASE = "https://api.met.no/weatherapi"
    
    def __init__(self):
        """Initialize empirical weather service."""
        logger.info("🌤️ Empirical Weather Service initialized")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BergNavnMaritimeResearch/1.0 (framgangsrik747@gmail.com)',
            'Accept': 'application/json'
        })
        
        self.api_calls = 0
    
    def get_marine_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get empirical marine weather data for coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Empirical weather data or None
        """
        try:
            # Ocean forecast (waves, currents)
            ocean_url = f"{self.MET_API_BASE}/oceanforecast/2.0/complete"
            params = {'lat': lat, 'lon': lon}
            
            response = self.session.get(ocean_url, params=params, timeout=10)
            self.api_calls += 1
            
            if response.status_code == 200:
                ocean_data = response.json()
                
                # Location forecast (wind, temperature)
                location_url = f"{self.MET_API_BASE}/locationforecast/2.0/compact"
                location_response = self.session.get(location_url, params=params, timeout=10)
                self.api_calls += 1
                
                location_data = location_response.json() if location_response.status_code == 200 else {}
                
                return self._parse_weather_data(ocean_data, location_data, lat, lon)
            else:
                logger.error(f"MET API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return None
    
    def _parse_weather_data(self, ocean_data: Dict, location_data: Dict, lat: float, lon: float) -> Dict[str, Any]:
        """Parse MET Norway API responses to standardized format."""
        weather = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'coordinates': {'lat': lat, 'lon': lon},
            'data_source': 'MET Norway API',
            'is_empirical': True,
            'verification_url': 'https://api.met.no'
        }
        
        # Extract ocean data
        if 'properties' in ocean_data and 'timeseries' in ocean_data['properties']:
            try:
                current = ocean_data['properties']['timeseries'][0]
                wave_data = current['data'].get('wave', {})
                
                weather.update({
                    'wave_height_m': wave_data.get('significantHeight', {}).get('value'),
                    'wave_direction_deg': wave_data.get('meanDirection', {}).get('value'),
                    'wave_period_s': wave_data.get('meanPeriod', {}).get('value'),
                    'current_speed_mps': current['data'].get('currentSpeed', {}).get('value'),
                    'current_direction_deg': current['data'].get('currentDirection', {}).get('value'),
                    'water_temperature_c': current['data'].get('seaTemperature', {}).get('value')
                })
            except (KeyError, IndexError) as e:
                logger.debug(f"Ocean data parsing error: {e}")
        
        # Extract location/weather data
        if 'properties' in location_data and 'timeseries' in location_data['properties']:
            try:
                current = location_data['properties']['timeseries'][0]['data']['instant']['details']
                
                weather.update({
                    'wind_speed_mps': current.get('wind_speed'),
                    'wind_direction_deg': current.get('wind_from_direction'),
                    'temperature_c': current.get('air_temperature'),
                    'pressure_hpa': current.get('air_pressure_at_sea_level'),
                    'humidity_percent': current.get('relative_humidity'),
                    'cloudiness_percent': current.get('cloud_area_fraction'),
                    'visibility_km': current.get('visibility', {}).get('value') if isinstance(current.get('visibility'), dict) else current.get('visibility')
                })
            except (KeyError, IndexError) as e:
                logger.debug(f"Location data parsing error: {e}")
        
        return weather
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get weather service status."""
        return {
            'service': 'empirical_weather',
            'source': 'MET Norway API',
            'api_calls': self.api_calls,
            'status': 'active',
            'url': 'https://api.met.no'
        }


# Global weather service instance
empirical_weather_service = EmpiricalWeatherService()