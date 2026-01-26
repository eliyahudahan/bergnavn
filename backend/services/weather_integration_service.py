# backend/services/weather_integration_service.py
"""
Weather Integration Service - Smart aggregation of multiple weather sources
Intelligently combines MET Norway, BarentsWatch, OpenWeatherMap, and empirical data
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import json

# Add dotenv import for loading environment variables
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
def load_environment_variables():
    """Load environment variables from .env file if it exists."""
    try:
        # Try to find .env file in project root
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info("✅ Loaded environment variables from .env file")
            return True
        else:
            logger.warning("⚠️ .env file not found, using system environment variables")
            return False
    except Exception as e:
        logger.error(f"❌ Error loading .env file: {e}")
        return False

# Load environment variables when module is imported
load_environment_variables()

class WeatherIntegrationService:
    """
    Master weather service that intelligently combines multiple data sources
    with caching, rate limiting, and failover strategies
    """
    
    def __init__(self):
        logger.info("🌤️ Weather Integration Service Initializing...")
        
        # Initialize all available services
        self.services = {}
        self.service_status = {}
        
        # Try to initialize each service
        self._initialize_services()
        
        # Cache for weather data
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
        
        # Rate limiting tracking
        self.request_times = {}
        
        # Statistics tracking
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'service_failures': 0,
            'last_request': None
        }
        
        logger.info("✅ Weather Integration Service Ready")
    
    def _initialize_services(self):
        """Initialize all available weather services."""
        
        # 1. MET Norway (Highest priority - Norwegian official)
        try:
            from .met_norway_service import met_norway_service
            self.services['met_norway'] = {
                'service': met_norway_service,
                'priority': 1,
                'type': 'norwegian_official',
                'requires_auth': False,
                'rate_limit': 1.0,  # 1 request per second
                'cache_minutes': 15
            }
            logger.info("✅ MET Norway service loaded")
        except ImportError as e:
            logger.warning(f"❌ MET Norway service not available: {e}")
        
        # 2. BarentsWatch (Norwegian maritime - if available)
        try:
            from .barentswatch_service import barentswatch_service
            self.services['barentswatch'] = {
                'service': barentswatch_service,
                'priority': 2,
                'type': 'norwegian_maritime',
                'requires_auth': True,  # Needs API credentials
                'rate_limit': 2.0,  # 2 requests per second
                'cache_minutes': 10
            }
            logger.info("✅ BarentsWatch service loaded")
        except ImportError:
            logger.info("ℹ️ BarentsWatch service not configured")
        
        # 3. OpenWeatherMap (International - if configured)
        openweather_key = os.environ.get('OPENWEATHER_API_KEY')
        if openweather_key:
            try:
                from .openweather_service import openweather_service
                self.services['openweather'] = {
                    'service': openweather_service,
                    'priority': 3,
                    'type': 'international',
                    'requires_auth': True,
                    'rate_limit': 1.0,
                    'cache_minutes': 10
                }
                logger.info("✅ OpenWeatherMap service loaded")
            except ImportError:
                logger.info("ℹ️ OpenWeatherMap service module not found")
        else:
            logger.info("ℹ️ OpenWeatherMap API key not configured")
        
        # 4. Empirical (Always available - fallback)
        try:
            from .empirical_weather import empirical_weather_service
            self.services['empirical'] = {
                'service': empirical_weather_service,
                'priority': 4,
                'type': 'fallback',
                'requires_auth': False,
                'rate_limit': 0,  # No rate limit
                'cache_minutes': 60
            }
            logger.info("✅ Empirical service loaded")
        except ImportError as e:
            logger.error(f"❌ Critical: Empirical service not available: {e}")
    
    def get_weather_for_dashboard(self, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Get comprehensive weather data for dashboard display
        Uses intelligent source selection with caching and fallback
        
        Args:
            lat: Latitude (defaults to MET_LAT from env)
            lon: Longitude (defaults to MET_LON from env)
            
        Returns:
            Comprehensive weather data with source information
        """
        # Update statistics
        self.stats['total_requests'] += 1
        self.stats['last_request'] = datetime.now(timezone.utc)
        
        # Use default coordinates if not provided
        if lat is None:
            lat = float(os.environ.get('MET_LAT', '60.3913'))
        if lon is None:
            lon = float(os.environ.get('MET_LON', '5.3221'))
        
        logger.info(f"🌤️ Requesting dashboard weather for {lat}, {lon}")
        
        # Check cache first
        cache_key = f"{lat:.4f},{lon:.4f}"
        cached = self._get_cached_weather(cache_key)
        if cached:
            self.stats['cache_hits'] += 1
            logger.info("✅ Using cached weather data")
            return cached
        
        # Try services in priority order
        weather_data = None
        used_service = None
        errors = []
        
        # Sort services by priority (1 = highest)
        sorted_services = sorted(
            self.services.items(),
            key=lambda x: x[1]['priority']
        )
        
        for service_name, service_info in sorted_services:
            if service_name == 'empirical' and len(errors) < 3:
                # Try empirical only if we have errors from other services
                continue
                
            try:
                logger.info(f"🔍 Trying {service_name} (priority {service_info['priority']})")
                
                # Check rate limiting
                if not self._check_rate_limit(service_name, service_info['rate_limit']):
                    logger.warning(f"⚠️ Rate limit exceeded for {service_name}, skipping")
                    continue
                
                # Get weather from service
                if service_name == 'met_norway':
                    weather_data = service_info['service'].get_current_weather(lat, lon)
                elif service_name == 'empirical':
                    weather_data = service_info['service'].get_marine_weather(lat, lon)
                else:
                    # For other services, try to find appropriate method
                    if hasattr(service_info['service'], 'get_current_weather'):
                        weather_data = service_info['service'].get_current_weather(lat, lon)
                    elif hasattr(service_info['service'], 'get_weather'):
                        weather_data = service_info['service'].get_weather(lat, lon)
                
                if weather_data and self._is_valid_weather_data(weather_data):
                    used_service = service_name
                    logger.info(f"✅ Got valid data from {service_name}")
                    break
                else:
                    logger.warning(f"⚠️ {service_name} returned invalid data")
                    
            except Exception as e:
                error_msg = f"{service_name}: {str(e)[:100]}"
                errors.append(error_msg)
                logger.error(f"❌ Error from {service_name}: {e}")
        
        # If no service worked, use empirical as last resort
        if not weather_data and 'empirical' in self.services:
            logger.warning("⚠️ All primary services failed, using empirical fallback")
            try:
                weather_data = self.services['empirical']['service'].get_marine_weather(lat, lon)
                used_service = 'empirical'
            except Exception as e:
                logger.error(f"❌ Even empirical failed: {e}")
                # Create emergency fallback
                weather_data = self._create_emergency_fallback(lat, lon, errors)
                used_service = 'emergency'
        
        # Enhance data with additional information
        enhanced_data = self._enhance_weather_data(weather_data, used_service, errors)
        
        # Cache the result
        self._cache_weather(cache_key, enhanced_data)
        
        return enhanced_data
    
    def _is_valid_weather_data(self, data: Dict) -> bool:
        """Validate that weather data contains essential information."""
        if not data:
            return False
        
        # Check for temperature or wind data
        has_temp = data.get('temperature_c') is not None or data.get('temperature') is not None
        has_wind = data.get('wind_speed_ms') is not None or data.get('wind_speed') is not None
        
        # Also check for reasonable values
        if has_temp:
            temp = data.get('temperature_c') or data.get('temperature')
            if temp is not None and (-50 < temp < 50):  # Reasonable temperature range
                return True
        
        if has_wind:
            wind = data.get('wind_speed_ms') or data.get('wind_speed')
            if wind is not None and (0 <= wind < 100):  # Reasonable wind range
                return True
        
        return has_temp or has_wind
    
    def _enhance_weather_data(self, data: Dict, source: str, errors: List[str]) -> Dict[str, Any]:
        """Enhance weather data with additional dashboard-specific information."""
        
        # Base structure
        enhanced = data.copy() if data else {}
        
        # Add source information
        enhanced['data_source'] = source
        enhanced['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add service status
        enhanced['service_status'] = {
            'source': source,
            'errors_encountered': errors,
            'available_sources': list(self.services.keys()),
            'source_priority': self._get_source_priority(source)
        }
        
        # Add display information for dashboard
        if 'temperature_c' in enhanced:
            temp = enhanced['temperature_c']
            wind = enhanced.get('wind_speed_ms', 0)
            condition = enhanced.get('condition', 'Unknown')
            location = enhanced.get('location', enhanced.get('city', 'Unknown'))
            
            enhanced['display'] = {
                'temperature': f"{round(temp)}°C",
                'wind': f"{round(wind)} m/s",
                'condition': condition,
                'location': location,
                'icon': self._get_weather_icon(condition),
                'source_badge': self._get_source_badge(source)
            }
            
            # Add weather icon based on condition
            enhanced['icon'] = self._get_weather_icon(condition)
        
        # Add forecast if available (placeholder for now)
        if source == 'met_norway' and data and 'forecast' not in data:
            enhanced['forecast'] = self._generate_simple_forecast(data)
        
        return enhanced
    
    def _get_weather_icon(self, condition: str) -> str:
        """Get appropriate weather icon based on condition."""
        condition_lower = condition.lower()
        
        if 'clear' in condition_lower or 'fair' in condition_lower:
            return 'sun'
        elif 'cloud' in condition_lower:
            return 'cloud'
        elif 'rain' in condition_lower:
            return 'cloud-rain'
        elif 'snow' in condition_lower:
            return 'snow'
        elif 'fog' in condition_lower or 'mist' in condition_lower:
            return 'cloud-fog'
        else:
            return 'cloud-sun'
    
    def _get_source_badge(self, source: str) -> str:
        """Get a display badge for the data source."""
        badges = {
            'met_norway': '🇳🇴 MET Norway',
            'barentswatch': '🌊 BarentsWatch',
            'openweather': '🌍 OpenWeatherMap',
            'empirical': '📊 Empirical',
            'emergency': '🚨 Emergency'
        }
        return badges.get(source, source)
    
    def _get_source_priority(self, source: str) -> int:
        """Get priority level of a source."""
        if source in self.services:
            return self.services[source]['priority']
        return 99  # Lowest priority
    
    def _check_rate_limit(self, service_name: str, limit_per_second: float) -> bool:
        """Check if we're within rate limits for a service."""
        if limit_per_second == 0:  # No rate limit
            return True
        
        now = datetime.now(timezone.utc)
        
        if service_name not in self.request_times:
            self.request_times[service_name] = []
        
        # Remove old request times (older than 1 second)
        self.request_times[service_name] = [
            t for t in self.request_times[service_name]
            if (now - t).total_seconds() < 1.0
        ]
        
        # Check if we can make another request
        if len(self.request_times[service_name]) < limit_per_second:
            self.request_times[service_name].append(now)
            return True
        
        return False
    
    def _get_cached_weather(self, cache_key: str) -> Optional[Dict]:
        """Get weather data from cache if valid."""
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            cache_age = datetime.now(timezone.utc) - cached_time
            
            # Get cache duration for this data source
            source = cached_data.get('data_source', 'empirical')
            cache_minutes = self.services.get(source, {}).get('cache_minutes', 15)
            
            if cache_age < timedelta(minutes=cache_minutes):
                return cached_data
            else:
                # Remove expired cache
                del self.cache[cache_key]
        
        return None
    
    def _cache_weather(self, cache_key: str, data: Dict):
        """Cache weather data."""
        self.cache[cache_key] = (datetime.now(timezone.utc), data)
        
        # Limit cache size
        if len(self.cache) > 100:  # Keep only 100 entries
            # Remove oldest
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
    
    def _generate_simple_forecast(self, current_data: Dict) -> Dict[str, Any]:
        """Generate a simple 24-hour forecast based on current conditions."""
        # This is a simplified forecast - in production, get from API
        temp = current_data.get('temperature_c', 8.5)
        wind = current_data.get('wind_speed_ms', 5.2)
        
        # Mock forecast data
        return {
            'next_24_hours': [
                {'hour': 0, 'temp': temp, 'wind': wind, 'condition': 'Similar'},
                {'hour': 6, 'temp': temp - 2, 'wind': wind + 1, 'condition': 'Cooler'},
                {'hour': 12, 'temp': temp + 1, 'wind': wind - 1, 'condition': 'Warmer'},
                {'hour': 18, 'temp': temp, 'wind': wind, 'condition': 'Similar'},
            ],
            'summary': 'Stable maritime conditions expected',
            'source': 'simulated_based_on_current'
        }
    
    def _create_emergency_fallback(self, lat: float, lon: float, errors: List[str]) -> Dict[str, Any]:
        """Create emergency fallback data when all services fail."""
        logger.critical("🚨 All weather services failed, using emergency fallback")
        
        # Very basic empirical data
        return {
            'temperature_c': 8.5,
            'wind_speed_ms': 5.2,
            'wind_direction': 'NW',
            'condition': 'Unknown',
            'location': f"Emergency Data ({lat:.2f}, {lon:.2f})",
            'city': 'Bergen',
            'data_source': 'emergency_fallback',
            'errors': errors,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'warning': 'ALL SERVICES UNAVAILABLE - Using emergency data'
        }
    
    def get_service_summary(self) -> Dict[str, Any]:
        """Get summary of all weather services and their status."""
        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'services': {},
            'cache_size': len(self.cache),
            'overall_status': 'unknown'
        }
        
        # Check each service
        working_services = 0
        total_services = len(self.services)
        
        for service_name, service_info in self.services.items():
            status = {
                'priority': service_info['priority'],
                'type': service_info['type'],
                'requires_auth': service_info['requires_auth'],
                'rate_limit': service_info['rate_limit'],
                'cache_minutes': service_info['cache_minutes']
            }
            
            # Try to get status from service if available
            try:
                if hasattr(service_info['service'], 'get_service_status'):
                    service_status = service_info['service'].get_service_status()
                    status.update(service_status)
                    if 'connectivity' in service_status and service_status['connectivity'] == 'connected':
                        working_services += 1
            except Exception as e:
                status['error'] = str(e)
            
            summary['services'][service_name] = status
        
        # Determine overall status
        if working_services == total_services:
            summary['overall_status'] = 'excellent'
        elif working_services >= total_services / 2:
            summary['overall_status'] = 'good'
        elif working_services > 0:
            summary['overall_status'] = 'degraded'
        else:
            summary['overall_status'] = 'critical'
        
        summary['working_services'] = working_services
        summary['total_services'] = total_services
        
        return summary

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        stats = self.stats.copy()
        stats['cache_size'] = len(self.cache)
        stats['services_count'] = len(self.services)
        
        if stats['total_requests'] > 0:
            stats['cache_hit_percentage'] = f"{(stats['cache_hits'] / stats['total_requests'] * 100):.1f}%"
            stats['failure_rate'] = f"{(stats['service_failures'] / stats['total_requests'] * 100):.1f}%"
        else:
            stats['cache_hit_percentage'] = "0%"
            stats['failure_rate'] = "0%"
        
        return stats


# Create global instance
weather_integration_service = WeatherIntegrationService()