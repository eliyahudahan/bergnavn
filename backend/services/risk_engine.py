"""
Empirical Risk Engine for Norwegian Maritime Operations.
Integrates with existing AIS and Weather services.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import math
import requests  # ADDED: For fetching weather data in risk assessment

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Core Risk Engine for maritime operations.
    Uses data from AIS, BarentsWatch, MET Norway, and RTZ routes.
    """

    def __init__(self):
        """Initialize with Norwegian safety regulations."""
        logger.info("✅ Risk Engine initialized")
        
        # Configuration for Norwegian regulations
        self.safety_parameters = {
            # Hazard distances (meters)
            'min_distance_turbine_m': 500,      # NMA regulation for wind turbines
            'min_distance_cable_m': 100,        # Industry standard for subsea cables
            'min_distance_aquaculture_m': 200,  # Norwegian Aquaculture Act
            
            # Weather limits
            'max_wave_height_m': 3.5,           # For coastal vessels
            'max_wind_speed_mps': 15.0,         # 29 knots
            
            # Navigation limits
            'night_speed_reduction_percent': 20,  # Common practice
            'max_route_deviation_km': 5.0,        # Maximum deviation from planned route
        }
        
        # Hazard data storage (loaded from BarentsWatch)
        self.hazard_data = {
            'aquaculture': [],   # Fish farms
            'cables': [],        # Subsea cables
            'installations': [], # Offshore turbines/platforms
            'protected_areas': [] # Environmental zones
        }
        
        # Cache for performance
        self._hazard_cache_timestamp = None
        self._hazard_cache_duration = 3600  # 1 hour in seconds
        
        # ADDED: Try to auto-load hazard data on startup
        self._try_load_hazards_on_startup()

    def _try_load_hazards_on_startup(self):
        """Attempt to load hazard data when engine starts."""
        try:
            # Try to import and load hazard data
            from backend.services.barentswatch_service import barentswatch_service
            
            aquaculture = barentswatch_service.get_aquaculture_facilities()
            cables = barentswatch_service.get_subsea_cables()
            installations = barentswatch_service.get_offshore_installations()
            
            if aquaculture or cables or installations:
                self.load_hazard_data(aquaculture, cables, installations)
                logger.info("Auto-loaded hazard data on startup")
            else:
                logger.info("No hazard data available on startup")
                
        except ImportError:
            logger.warning("BarentsWatch service not available for auto-load")
        except Exception as e:
            logger.error(f"Failed to auto-load hazards: {e}")

    def load_hazard_data(self, aquaculture_data: List[Dict], cables_data: List[Dict], 
                         installations_data: List[Dict], protected_areas: Optional[List[Dict]] = None):
        """
        Load hazard data fetched from BarentsWatch.
        
        Args:
            aquaculture_data: List of fish farm locations
            cables_data: List of subsea cable routes
            installations_data: List of offshore installations (turbines, platforms)
            protected_areas: Optional list of protected marine zones
        """
        self.hazard_data['aquaculture'] = aquaculture_data or []
        self.hazard_data['cables'] = cables_data or []
        self.hazard_data['installations'] = installations_data or []
        self.hazard_data['protected_areas'] = protected_areas or []
        
        self._hazard_cache_timestamp = datetime.now()
        
        logger.info(
            f"Loaded hazard data: "
            f"{len(aquaculture_data)} aquaculture, "
            f"{len(cables_data)} cables, "
            f"{len(installations_data)} installations, "
            f"{len(protected_areas or [])} protected areas"
        )

    def assess_vessel(self, vessel_data: Dict, weather_data: Optional[Dict] = None, 
                     route_data: Optional[Dict] = None) -> List[Dict]:
        """
        Comprehensive risk assessment for a single vessel.
        
        Args:
            vessel_data: Vessel information from AIS service
            weather_data: Weather information from MET Norway
            route_data: Planned route information (optional)
            
        Returns:
            List of risk dictionaries sorted by severity
        """
        risks = []
        
        # Validate input
        if not vessel_data or 'lat' not in vessel_data or 'lon' not in vessel_data:
            return risks
        
        vessel_lat = vessel_data.get('lat')
        vessel_lon = vessel_data.get('lon')
        vessel_mmsi = vessel_data.get('mmsi', 'unknown')
        vessel_name = vessel_data.get('name', 'unknown')
        vessel_type = vessel_data.get('type', 'unknown')
        
        logger.debug(f"Assessing risks for vessel {vessel_name} (MMSI: {vessel_mmsi})")
        
        # 1. Check proximity to all hazards
        hazard_risks = self._check_hazard_proximity(vessel_lat, vessel_lon, vessel_data)
        risks.extend(hazard_risks)
        
        # 2. Check weather conditions
        if weather_data:
            weather_risks = self._check_weather_conditions(vessel_data, weather_data)
            risks.extend(weather_risks)
        else:
            # ADDED: Try to fetch weather data if not provided
            try:
                weather_data_fallback = self._fetch_weather_for_location(vessel_lat, vessel_lon)
                if weather_data_fallback:
                    weather_risks = self._check_weather_conditions(vessel_data, weather_data_fallback)
                    risks.extend(weather_risks)
            except Exception as e:
                logger.debug(f"Could not fetch weather for risk assessment: {e}")
        
        # 3. Check route deviation (if route data available)
        if route_data and route_data.get('waypoints'):
            deviation_risk = self._check_route_deviation(vessel_lat, vessel_lon, route_data)
            if deviation_risk:
                risks.append(deviation_risk)
        
        # 4. Check time of day for night operations
        time_risk = self._check_night_operation()
        if time_risk:
            risks.append(time_risk)
        
        # 5. Check speed relative to conditions
        if weather_data:
            speed_risk = self._check_speed_conditions(vessel_data, weather_data)
            if speed_risk:
                risks.append(speed_risk)
        
        # Sort by severity (HIGH > MEDIUM > LOW)
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        risks.sort(key=lambda x: severity_order.get(x.get('severity', 'LOW'), 2))
        
        return risks

    def _fetch_weather_for_location(self, lat: float, lon: float) -> Optional[Dict]:
        """Fetch weather data for a specific location using MET Norway API."""
        try:
            met_user_agent = "BergNavnRiskEngine/1.0"
            headers = {'User-Agent': met_user_agent}
            url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
            
            response = requests.get(url, headers=headers, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if 'properties' in data and 'timeseries' in data['properties']:
                    current = data['properties']['timeseries'][0]['data']
                    instant = current['instant']['details']
                    
                    return {
                        'wind_speed': instant.get('wind_speed'),
                        'wind_direction': instant.get('wind_from_direction'),
                        'temperature': instant.get('air_temperature'),
                        'pressure': instant.get('air_pressure_at_sea_level'),
                        'humidity': instant.get('relative_humidity'),
                        'cloudiness': instant.get('cloud_area_fraction')
                    }
        except Exception as e:
            logger.debug(f"Weather fetch for location failed: {e}")
        
        return None

    def _check_hazard_proximity(self, lat: float, lon: float, vessel_data: Dict) -> List[Dict]:
        """Check proximity to all types of hazards."""
        risks = []
        
        # Define safe distances per hazard type
        safe_distances = {
            'aquaculture': self.safety_parameters['min_distance_aquaculture_m'],
            'cables': self.safety_parameters['min_distance_cable_m'],
            'installations': self.safety_parameters['min_distance_turbine_m'],
            'protected_areas': 0  # Any entry is a violation
        }
        
        # Check each hazard category
        for hazard_type, hazards in self.hazard_data.items():
            if not hazards:
                continue
                
            safe_distance = safe_distances.get(hazard_type, 100)
            
            for hazard in hazards:
                # Extract coordinates - ADAPT THIS TO YOUR BARENTSWATCH DATA STRUCTURE
                hazard_lat = hazard.get('latitude') or hazard.get('lat') or hazard.get('y')
                hazard_lon = hazard.get('longitude') or hazard.get('lon') or hazard.get('x')
                
                if not hazard_lat or not hazard_lon:
                    continue
                
                # Calculate distance
                distance = self._calculate_distance_meters(lat, lon, hazard_lat, hazard_lon)
                
                # Check if too close
                if distance < safe_distance:
                    hazard_name = hazard.get('name', hazard.get('id', f'Unknown {hazard_type}'))
                    
                    risk = {
                        'type': 'HAZARD_PROXIMITY',
                        'subtype': hazard_type.upper(),
                        'severity': 'HIGH' if distance < safe_distance * 0.5 else 'MEDIUM',
                        'message': f'Vessel within {int(distance)}m of {hazard_name} ({hazard_type})',
                        'details': {
                            'hazard_name': hazard_name,
                            'hazard_type': hazard_type,
                            'distance_meters': int(distance),
                            'safe_distance_meters': safe_distance,
                            'hazard_position': {'lat': hazard_lat, 'lon': hazard_lon},
                            'vessel_position': {'lat': lat, 'lon': lon}
                        },
                        'vessel_mmsi': vessel_data.get('mmsi'),
                        'vessel_name': vessel_data.get('name'),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    risks.append(risk)
        
        return risks

    def _check_weather_conditions(self, vessel_data: Dict, weather_data: Dict) -> List[Dict]:
        """Check weather conditions against vessel limits."""
        risks = []
        
        # Check wave height
        wave_height = weather_data.get('wave_height') or weather_data.get('waveHeight')
        if wave_height and wave_height > self.safety_parameters['max_wave_height_m']:
            risks.append({
                'type': 'HIGH_WAVES',
                'severity': 'MEDIUM',
                'message': f'Wave height {wave_height:.1f}m exceeds safe limit of {self.safety_parameters["max_wave_height_m"]}m',
                'details': {
                    'current_wave_height': wave_height,
                    'max_safe_wave_height': self.safety_parameters['max_wave_height_m'],
                    'vessel_type': vessel_data.get('type'),
                    'recommendation': 'Reduce speed, consider alternative route'
                },
                'vessel_mmsi': vessel_data.get('mmsi'),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        
        # Check wind speed
        wind_speed = weather_data.get('wind_speed') or weather_data.get('windSpeed')
        if wind_speed and wind_speed > self.safety_parameters['max_wind_speed_mps']:
            risks.append({
                'type': 'HIGH_WINDS',
                'severity': 'MEDIUM',
                'message': f'Wind speed {wind_speed:.1f}m/s exceeds safe limit of {self.safety_parameters["max_wind_speed_mps"]}m/s',
                'details': {
                    'current_wind_speed': wind_speed,
                    'max_safe_wind_speed': self.safety_parameters['max_wind_speed_mps'],
                    'vessel_type': vessel_data.get('type')
                },
                'vessel_mmsi': vessel_data.get('mmsi'),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        
        return risks

    def _check_route_deviation(self, lat: float, lon: float, route_data: Dict) -> Optional[Dict]:
        """Check if vessel is deviating from planned route."""
        waypoints = route_data.get('waypoints', [])
        if not waypoints:
            return None
        
        # Find nearest waypoint
        min_distance = float('inf')
        nearest_waypoint = None
        
        for waypoint in waypoints:
            wp_lat = waypoint.get('lat') or waypoint.get('latitude')
            wp_lon = waypoint.get('lon') or waypoint.get('longitude')
            
            if wp_lat and wp_lon:
                distance = self._calculate_distance_meters(lat, lon, wp_lat, wp_lon)
                if distance < min_distance:
                    min_distance = distance
                    nearest_waypoint = waypoint
        
        # Check if deviation exceeds limit
        if min_distance > self.safety_parameters['max_route_deviation_km'] * 1000:
            return {
                'type': 'ROUTE_DEVIATION',
                'severity': 'MEDIUM',
                'message': f'Vessel is {min_distance/1000:.1f}km from planned route',
                'details': {
                    'deviation_km': min_distance / 1000,
                    'max_allowed_deviation_km': self.safety_parameters['max_route_deviation_km'],
                    'nearest_waypoint': nearest_waypoint,
                    'current_position': {'lat': lat, 'lon': lon}
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        
        return None

    def _check_night_operation(self) -> Optional[Dict]:
        """Check if operating during night hours."""
        current_hour = datetime.utcnow().hour
        # Norway time (UTC+1), night roughly 21:00-06:00 local
        is_night = current_hour >= 20 or current_hour <= 5  # Adjust for UTC offset
        
        if is_night:
            return {
                'type': 'NIGHT_OPERATION',
                'severity': 'LOW',
                'message': 'Operating during night hours',
                'details': {
                    'current_utc_hour': current_hour,
                    'norway_hour': (current_hour + 1) % 24,
                    'recommendation': 'Increase vigilance, use navigation lights'
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        
        return None

    def _check_speed_conditions(self, vessel_data: Dict, weather_data: Dict) -> Optional[Dict]:
        """Check if vessel speed is appropriate for conditions."""
        vessel_speed = vessel_data.get('speed')
        if not vessel_speed:
            return None
        
        wave_height = weather_data.get('wave_height') or weather_data.get('waveHeight', 0)
        wind_speed = weather_data.get('wind_speed') or weather_data.get('windSpeed', 0)
        
        # Simple rule: reduce speed in adverse conditions
        base_max_speed = 20.0  # knots
        speed_reduction = wave_height * 2 + wind_speed * 0.5
        max_safe_speed = max(5.0, base_max_speed - speed_reduction)
        
        if vessel_speed > max_safe_speed:
            return {
                'type': 'EXCESSIVE_SPEED',
                'severity': 'MEDIUM',
                'message': f'Speed {vessel_speed:.1f}knots too high for conditions',
                'details': {
                    'current_speed': vessel_speed,
                    'max_safe_speed': max_safe_speed,
                    'wave_height': wave_height,
                    'wind_speed': wind_speed,
                    'recommendation': f'Reduce speed to {max_safe_speed:.1f} knots'
                },
                'vessel_mmsi': vessel_data.get('mmsi'),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        
        return None

    def _calculate_distance_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates in degrees
            lat2, lon2: Second point coordinates in degrees
            
        Returns:
            Distance in meters
        """
        # Earth radius in meters
        R = 6371000
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

    def get_risk_summary(self, risks: List[Dict]) -> Dict:
        """Generate summary statistics from risk list."""
        if not risks:
            return {
                'total_risks': 0,
                'by_severity': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'by_type': {},
                'highest_severity': 'NONE'
            }
        
        summary = {
            'total_risks': len(risks),
            'by_severity': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'by_type': {},
            'highest_severity': 'LOW'
        }
        
        severity_order = {'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}
        
        for risk in risks:
            # Count by severity
            severity = risk.get('severity', 'LOW')
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # Track highest severity
            if severity_order.get(severity, 0) > severity_order.get(summary['highest_severity'], 0):
                summary['highest_severity'] = severity
            
            # Count by type
            risk_type = risk.get('type', 'UNKNOWN')
            summary['by_type'][risk_type] = summary['by_type'].get(risk_type, 0) + 1
        
        return summary


# Global instance
risk_engine = RiskEngine()