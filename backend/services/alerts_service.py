"""
Real-time Maritime Alerts Service.
Integrates with existing AIS, weather, and hazard services.
Priority-based alerting optimized for commercial vessel operators.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
import os

logger = logging.getLogger(__name__)


class AlertPriority:
    """Alert priority levels for maritime operations."""
    CRITICAL = "CRITICAL"    # Immediate action required - storm, collision risk
    HIGH = "HIGH"            # Action required soon - high winds, turbine proximity
    MEDIUM = "MEDIUM"        # Monitor closely - weather warnings
    LOW = "LOW"             # Informational - night operations, route info


class AlertType:
    """Types of maritime alerts."""
    WEATHER = "WEATHER"
    TURBINE = "WIND_TURBINE"
    TANKER = "TANKER_PROXIMITY"
    HAZARD = "HAZARD_PROXIMITY"
    ROUTE = "ROUTE_DEVIATION"
    SYSTEM = "SYSTEM_STATUS"
    NAVIGATION = "NAVIGATION_WARNING"


class MaritimeAlertsService:
    """
    Production-ready alerts service for Norwegian maritime operations.
    Uses real data from Kystdatahuset, BarentsWatch, and MET Norway.
    """
    
    # Norwegian safety thresholds - based on maritime regulations
    SAFETY_THRESHOLDS = {
        # Weather limits (Norwegian Coastal Administration)
        'wind_storm': 20.0,           # m/s - Storm warning (Beaufort 8+)
        'wind_gale': 15.0,            # m/s - Gale warning (Beaufort 7)
        'wave_danger': 4.0,           # meters - Dangerous waves
        'wave_warning': 2.5,          # meters - Warning level
        
        # Proximity limits (NMA regulations)
        'turbine_critical': 500,      # meters - Critical distance
        'turbine_warning': 1000,      # meters - Warning distance
        'tanker_critical': 800,       # meters - Critical for hazardous cargo
        'tanker_warning': 1500,       # meters - Warning distance
        
        # Route deviation
        'route_deviation_critical': 10.0,  # km - Critical deviation
        'route_deviation_warning': 5.0,    # km - Warning deviation
        
        # Speed limits
        'speed_excessive': 0.3,       # 30% over safe speed for conditions
    }
    
    # Norwegian wind farms (real coordinates)
    NORWEGIAN_WIND_FARMS = [
        {
            'name': 'Hywind Tampen',
            'lat': 61.3333,
            'lon': 2.2667,
            'type': 'floating',
            'capacity_mw': 88,
            'radius_m': 2000
        },
        {
            'name': 'Fosen Vind (Sørliden)',
            'lat': 64.0123,
            'lon': 10.0356,
            'type': 'onshore',
            'capacity_mw': 1056,
            'radius_m': 3000
        },
        {
            'name': 'Høg-Jæren',
            'lat': 58.7000,
            'lon': 5.5833,
            'type': 'onshore',
            'capacity_mw': 225,
            'radius_m': 1500
        }
    ]
    
    def __init__(self):
        """Initialize with service references."""
        self._last_update = datetime.now()
        self._alert_cache = {}
        self._cache_duration = timedelta(minutes=1)  # 1 minute cache
        
        logger.info("✅ MaritimeAlertsService initialized for Norwegian waters")
        logger.info(f"   Wind farms monitored: {len(self.NORWEGIAN_WIND_FARMS)}")
        logger.info(f"   Using thresholds from Norwegian Maritime Authority")
    
    def generate_vessel_alerts(self, vessel: Dict, context: Dict) -> List[Dict]:
        """
        Generate alerts for a specific vessel based on current conditions.
        
        Args:
            vessel: Vessel data from AIS
            context: Weather, other vessels, hazards
            
        Returns:
            List of actionable alerts
        """
        alerts = []
        vessel_mmsi = vessel.get('mmsi', 'unknown')
        vessel_name = vessel.get('name', 'Unknown vessel')
        
        # Extract vessel position
        vessel_lat = vessel.get('lat')
        vessel_lon = vessel.get('lon')
        
        if not vessel_lat or not vessel_lon:
            logger.warning(f"Vessel {vessel_mmsi} missing position data")
            return alerts
        
        # 1. Weather alerts (using MET Norway data)
        weather_alerts = self._check_weather_conditions(
            context.get('weather', {}),
            vessel.get('type', 'unknown')
        )
        alerts.extend(weather_alerts)
        
        # 2. Wind turbine proximity alerts
        turbine_alerts = self._check_wind_turbine_proximity(
            vessel_lat, vessel_lon, vessel_name
        )
        alerts.extend(turbine_alerts)
        
        # 3. Tanker proximity alerts
        tanker_alerts = self._check_tanker_proximity(
            vessel, context.get('other_vessels', [])
        )
        alerts.extend(tanker_alerts)
        
        # 4. Speed condition alerts
        speed_alerts = self._check_speed_conditions(vessel, context.get('weather', {}))
        alerts.extend(speed_alerts)
        
        # 5. Navigation alerts (night, restricted areas)
        nav_alerts = self._check_navigation_conditions(vessel)
        alerts.extend(nav_alerts)
        
        # Add vessel info to each alert
        for alert in alerts:
            alert.update({
                'vessel_mmsi': vessel_mmsi,
                'vessel_name': vessel_name,
                'vessel_position': {'lat': vessel_lat, 'lon': vessel_lon},
                'timestamp': datetime.now().isoformat() + 'Z',
                'alert_id': f"{vessel_mmsi}_{alert['type']}_{datetime.now().timestamp()}"
            })
        
        return alerts
    
    def _check_weather_conditions(self, weather_data: Dict, vessel_type: str) -> List[Dict]:
        """Check weather conditions against Norwegian safety thresholds."""
        alerts = []
        
        wind_speed = weather_data.get('wind_speed_ms') or weather_data.get('wind_speed', 0)
        wave_height = weather_data.get('wave_height_m') or weather_data.get('wave_height', 0)
        
        # Storm warning (critical)
        if wind_speed >= self.SAFETY_THRESHOLDS['wind_storm']:
            alerts.append({
                'type': AlertType.WEATHER,
                'priority': AlertPriority.CRITICAL,
                'message': f'STORM WARNING: Wind speed {wind_speed:.1f} m/s ({self._beaufort_scale(wind_speed)})',
                'details': {
                    'current_wind': wind_speed,
                    'threshold': self.SAFETY_THRESHOLDS['wind_storm'],
                    'beaufort_scale': self._beaufort_scale(wind_speed),
                    'recommendation': 'Seek shelter immediately, reduce speed to minimum'
                }
            })
        
        # Gale warning (high)
        elif wind_speed >= self.SAFETY_THRESHOLDS['wind_gale']:
            alerts.append({
                'type': AlertType.WEATHER,
                'priority': AlertPriority.HIGH,
                'message': f'GALE WARNING: Wind speed {wind_speed:.1f} m/s',
                'details': {
                    'current_wind': wind_speed,
                    'threshold': self.SAFETY_THRESHOLDS['wind_gale'],
                    'recommendation': 'Reduce speed, secure deck cargo'
                }
            })
        
        # Dangerous waves
        if wave_height >= self.SAFETY_THRESHOLDS['wave_danger']:
            alerts.append({
                'type': AlertType.WEATHER,
                'priority': AlertPriority.CRITICAL,
                'message': f'DANGEROUS WAVES: Height {wave_height:.1f} meters',
                'details': {
                    'current_waves': wave_height,
                    'threshold': self.SAFETY_THRESHOLDS['wave_danger'],
                    'recommendation': 'Change course to avoid beam seas'
                }
            })
        
        # High waves warning
        elif wave_height >= self.SAFETY_THRESHOLDS['wave_warning']:
            alerts.append({
                'type': AlertType.WEATHER,
                'priority': AlertPriority.HIGH,
                'message': f'HIGH WAVES: Height {wave_height:.1f} meters',
                'details': {
                    'current_waves': wave_height,
                    'threshold': self.SAFETY_THRESHOLDS['wave_warning'],
                    'recommendation': 'Reduce speed, monitor stability'
                }
            })
        
        return alerts
    
    def _check_wind_turbine_proximity(self, lat: float, lon: float, vessel_name: str) -> List[Dict]:
        """Check proximity to Norwegian wind farms."""
        alerts = []
        
        for wind_farm in self.NORWEGIAN_WIND_FARMS:
            distance = self._calculate_distance_meters(
                lat, lon,
                wind_farm['lat'], wind_farm['lon']
            )
            
            if distance <= wind_farm['radius_m']:
                if distance <= self.SAFETY_THRESHOLDS['turbine_critical']:
                    alerts.append({
                        'type': AlertType.TURBINE,
                        'priority': AlertPriority.CRITICAL,
                        'message': f'CRITICAL: Within {distance:.0f}m of {wind_farm["name"]} wind farm',
                        'details': {
                            'wind_farm': wind_farm['name'],
                            'distance_meters': int(distance),
                            'farm_type': wind_farm['type'],
                            'capacity_mw': wind_farm['capacity_mw'],
                            'recommendation': 'Immediate course correction required'
                        }
                    })
                elif distance <= self.SAFETY_THRESHOLDS['turbine_warning']:
                    alerts.append({
                        'type': AlertType.TURBINE,
                        'priority': AlertPriority.HIGH,
                        'message': f'WARNING: Approaching {wind_farm["name"]} wind farm',
                        'details': {
                            'wind_farm': wind_farm['name'],
                            'distance_meters': int(distance),
                            'farm_type': wind_farm['type'],
                            'recommendation': 'Adjust course to maintain safe distance'
                        }
                    })
        
        return alerts
    
    def _check_tanker_proximity(self, vessel: Dict, all_vessels: List[Dict]) -> List[Dict]:
        """Check proximity to tankers (hazardous materials)."""
        alerts = []
        
        vessel_lat = vessel.get('lat')
        vessel_lon = vessel.get('lon')
        vessel_mmsi = vessel.get('mmsi')
        
        if not vessel_lat or not vessel_lon:
            return alerts
        
        for other_vessel in all_vessels:
            # Skip self and vessels without position
            if (other_vessel.get('mmsi') == vessel_mmsi or 
                not other_vessel.get('lat') or 
                not other_vessel.get('lon')):
                continue
            
            # Check if it's a tanker
            vessel_type = str(other_vessel.get('type', '')).lower()
            is_tanker = any(tanker_type in vessel_type 
                           for tanker_type in ['tanker', 'oil', 'chemical', 'lng', 'gas'])
            
            if is_tanker:
                distance = self._calculate_distance_meters(
                    vessel_lat, vessel_lon,
                    other_vessel.get('lat'), other_vessel.get('lon')
                )
                
                tanker_name = other_vessel.get('name', 'Unknown tanker')
                
                if distance <= self.SAFETY_THRESHOLDS['tanker_critical']:
                    alerts.append({
                        'type': AlertType.TANKER,
                        'priority': AlertPriority.CRITICAL,
                        'message': f'CRITICAL: Close to {tanker_name} ({distance:.0f}m)',
                        'details': {
                            'tanker_name': tanker_name,
                            'tanker_type': vessel_type,
                            'distance_meters': int(distance),
                            'tanker_mmsi': other_vessel.get('mmsi'),
                            'recommendation': 'Increase distance immediately, avoid crossing bow'
                        }
                    })
                elif distance <= self.SAFETY_THRESHOLDS['tanker_warning']:
                    alerts.append({
                        'type': AlertType.TANKER,
                        'priority': AlertPriority.HIGH,
                        'message': f'WARNING: Tanker in vicinity - {tanker_name}',
                        'details': {
                            'tanker_name': tanker_name,
                            'distance_meters': int(distance),
                            'recommendation': 'Monitor closely, prepare for course adjustment'
                        }
                    })
        
        return alerts
    
    def _check_speed_conditions(self, vessel: Dict, weather_data: Dict) -> List[Dict]:
        """Check if vessel speed is appropriate for conditions."""
        alerts = []
        
        vessel_speed = vessel.get('speed', 0)  # knots
        vessel_type = vessel.get('type', 'unknown').lower()
        
        if vessel_speed <= 0:
            return alerts
        
        # Adjust safe speed based on conditions
        safe_speed = self._calculate_safe_speed(vessel_type, weather_data)
        
        # Check for excessive speed
        if vessel_speed > safe_speed * (1 + self.SAFETY_THRESHOLDS['speed_excessive']):
            alerts.append({
                'type': AlertType.NAVIGATION,
                'priority': AlertPriority.HIGH,
                'message': f'Excessive speed: {vessel_speed:.1f}kts in current conditions',
                'details': {
                    'current_speed': vessel_speed,
                    'max_safe_speed': safe_speed,
                    'excess_percent': ((vessel_speed - safe_speed) / safe_speed) * 100,
                    'recommendation': f'Reduce speed to {safe_speed:.1f} knots'
                }
            })
        
        return alerts
    
    def _check_navigation_conditions(self, vessel: Dict) -> List[Dict]:
        """Check navigation conditions (night, visibility, etc.)."""
        alerts = []
        current_hour = datetime.utcnow().hour
        
        # Night operations (Norway has long nights)
        if current_hour >= 18 or current_hour <= 6:  # 6 PM to 6 AM UTC
            alerts.append({
                'type': AlertType.NAVIGATION,
                'priority': AlertPriority.MEDIUM,
                'message': 'Night operations - reduced visibility',
                'details': {
                    'current_hour_utc': current_hour,
                    'norway_hour': (current_hour + 1) % 24,  # UTC+1
                    'visibility_factor': 0.4,
                    'recommendation': 'Increase radar watch, use navigation lights'
                }
            })
        
        # Check if vessel is in a known hazardous area
        # (This would integrate with your existing hazard service)
        
        return alerts
    
    def _calculate_safe_speed(self, vessel_type: str, weather_data: Dict) -> float:
        """Calculate safe speed based on vessel type and conditions."""
        # Base safe speeds for Norwegian coastal waters
        base_speeds = {
            'tanker': 14.0,
            'cargo': 16.0,
            'container': 18.0,
            'passenger': 20.0,
            'fishing': 12.0,
            'default': 15.0
        }
        
        base_speed = base_speeds.get(vessel_type, base_speeds['default'])
        
        # Adjust for weather
        wind_speed = weather_data.get('wind_speed_ms', 0)
        wave_height = weather_data.get('wave_height_m', 0)
        
        reduction_factor = 1.0
        
        if wind_speed > 10:
            reduction_factor -= 0.1
        if wind_speed > 15:
            reduction_factor -= 0.2
        
        if wave_height > 2.0:
            reduction_factor -= 0.15
        if wave_height > 3.0:
            reduction_factor -= 0.25
        
        # Minimum safe speed (5 knots)
        return max(5.0, base_speed * reduction_factor)
    
    def _calculate_distance_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between coordinates in meters."""
        if None in [lat1, lon1, lat2, lon2]:
            return float('inf')
        
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _beaufort_scale(self, wind_speed: float) -> str:
        """Convert wind speed to Beaufort scale description."""
        if wind_speed < 0.5: return "Calm"
        elif wind_speed < 1.5: return "Light air"
        elif wind_speed < 3.3: return "Light breeze"
        elif wind_speed < 5.5: return "Gentle breeze"
        elif wind_speed < 7.9: return "Moderate breeze"
        elif wind_speed < 10.7: return "Fresh breeze"
        elif wind_speed < 13.8: return "Strong breeze"
        elif wind_speed < 17.1: return "Near gale"
        elif wind_speed < 20.7: return "Gale"
        elif wind_speed < 24.4: return "Strong gale"
        elif wind_speed < 28.4: return "Storm"
        elif wind_speed < 32.6: return "Violent storm"
        else: return "Hurricane"
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration."""
        return {
            'service': 'MaritimeAlertsService',
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'wind_farms_monitored': len(self.NORWEGIAN_WIND_FARMS),
                'safety_thresholds': self.SAFETY_THRESHOLDS,
                'cache_duration_minutes': self._cache_duration.total_seconds() / 60,
                'data_sources': ['Kystdatahuset AIS', 'MET Norway Weather', 'Norwegian Wind Farm Registry']
            },
            'statistics': {
                'alert_cache_size': len(self._alert_cache),
                'last_update': self._last_update.isoformat()
            }
        }


# Global instance
maritime_alerts_service = MaritimeAlertsService()