"""
Empirical Risk Engine for Norwegian Maritime Operations.
Integrates with existing AIS and Weather services.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import math
import requests  # For fetching weather data in risk assessment

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
        
        # NEW: Consolidated list for proximity checks
        self.hazard_locations = []
        
        # Cache for performance
        self._hazard_cache_timestamp = None
        self._hazard_cache_duration = 3600  # 1 hour in seconds
        
        # Try to auto-load hazard data on startup
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
        
        # NEW: Build consolidated hazard list for advanced risk assessment
        self.hazard_locations = []
        
        # Add aquaculture facilities
        for facility in self.hazard_data['aquaculture']:
            if 'latitude' in facility and 'longitude' in facility:
                self.hazard_locations.append({
                    'type': 'aquaculture',
                    'name': facility.get('name', 'Aquaculture Facility'),
                    'latitude': facility['latitude'],
                    'longitude': facility['longitude']
                })
        
        # Add cables
        for cable in self.hazard_data['cables']:
            if 'latitude' in cable and 'longitude' in cable:
                self.hazard_locations.append({
                    'type': 'cable',
                    'name': cable.get('name', 'Subsea Cable'),
                    'latitude': cable['latitude'],
                    'longitude': cable['longitude']
                })
        
        # Add installations
        for installation in self.hazard_data['installations']:
            if 'latitude' in installation and 'longitude' in installation:
                self.hazard_locations.append({
                    'type': 'installation',
                    'name': installation.get('name', 'Offshore Installation'),
                    'latitude': installation['latitude'],
                    'longitude': installation['longitude']
                })
        
        self._hazard_cache_timestamp = datetime.now()
        
        logger.info(
            f"Loaded hazard data: "
            f"{len(aquaculture_data)} aquaculture, "
            f"{len(cables_data)} cables, "
            f"{len(installations_data)} installations, "
            f"{len(protected_areas or [])} protected areas"
        )
        logger.info(f"Consolidated {len(self.hazard_locations)} hazard locations for proximity checks")

    def assess_vessel(self, vessel_data: Dict, weather_data: Optional[Dict] = None, 
                     route_data: Optional[Dict] = None) -> List[Dict]:
        """
        Comprehensive risk assessment for a single vessel.
        Now uses the advanced risk calculation as the primary method.
        
        Args:
            vessel_data: Vessel information from AIS service
            weather_data: Weather information from MET Norway
            route_data: Planned route information (optional)
            
        Returns:
            List of risk dictionaries sorted by severity
        """
        # FIX: Use the advanced risk calculation as primary method
        if weather_data:
            # Ensure wave_height exists in weather data
            weather_data_fixed = self._ensure_wave_height_data(weather_data)
            
            # Use advanced risk calculation
            risks = self._calculate_advanced_risks(vessel_data, weather_data_fixed)
            
            # Also run legacy checks for compatibility
            legacy_risks = self._run_legacy_checks(vessel_data, weather_data_fixed, route_data)
            
            # Combine risks, avoiding duplicates based on type
            combined_risks = self._combine_risk_lists(risks, legacy_risks)
            
        else:
            # Fallback to legacy checks only
            combined_risks = self._run_legacy_checks(vessel_data, weather_data, route_data)
        
        # Sort by severity (HIGH > MEDIUM > LOW)
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        combined_risks.sort(key=lambda x: severity_order.get(x.get('severity', 'LOW'), 2))
        
        logger.debug(f"Generated {len(combined_risks)} risks for vessel {vessel_data.get('name', 'unknown')}")
        return combined_risks

    def _calculate_advanced_risks(self, vessel_data: Dict, weather_data: Dict) -> List[Dict]:
        """
        Calculate comprehensive, data-driven maritime risks based on empirical thresholds.
        This is the core logic that transforms raw data into actionable risk assessments.
        """
        risks = []
        
        # Extract core parameters with safe defaults
        vessel_speed = vessel_data.get('speed', 0.0)
        vessel_lat = vessel_data.get('lat')
        vessel_lon = vessel_data.get('lon')
        vessel_type = str(vessel_data.get('type', '')).lower()
        vessel_draught = vessel_data.get('draught', 5.0)
        vessel_length = vessel_data.get('length', 100.0)  # Default to 100m
        
        wind_speed = weather_data.get('wind_speed', 0.0)
        wave_height = weather_data.get('wave_height', 0.0)
        
        # Empirical risk thresholds for Norwegian coastal waters
        # Based on operational guidelines and historical incident data
        SPEED_THRESHOLDS = {
            'cargo': 18.0, 'tanker': 16.0, 'passenger': 20.0,
            'fishing': 12.0, 'general cargo': 15.0, 'container': 19.0,
            'default': 15.0
        }
        
        WIND_THRESHOLDS = {'LOW': 10.0, 'MEDIUM': 15.0, 'HIGH': 20.0}  # m/s
        WAVE_THRESHOLDS = {'LOW': 2.0, 'MEDIUM': 3.5, 'HIGH': 5.0}    # meters
        
        # 1. EXCESSIVE SPEED RISK (Data-driven)
        speed_limit = SPEED_THRESHOLDS.get(vessel_type, SPEED_THRESHOLDS['default'])
        
        # Adjust safe speed for environmental conditions
        weather_adjustment = 1.0
        if wind_speed > WIND_THRESHOLDS['LOW']:
            weather_adjustment -= 0.15
        if wave_height > WAVE_THRESHOLDS['LOW']:
            weather_adjustment -= 0.20
        if vessel_draught > 10.0:  # Deep draught vessels
            weather_adjustment -= 0.10
        
        safe_speed = max(5.0, speed_limit * weather_adjustment)  # Minimum 5 knots
        
        if vessel_speed > safe_speed * 1.1:  # 10% over safe speed threshold
            severity = 'HIGH' if vessel_speed > safe_speed * 1.3 else 'MEDIUM'
            risks.append({
                'type': 'EXCESSIVE_SPEED',
                'severity': severity,
                'message': f'Vessel speed {vessel_speed:.1f} knots exceeds condition-adjusted safe speed of {safe_speed:.1f} knots',
                'details': {
                    'current_speed': vessel_speed,
                    'max_safe_speed': safe_speed,
                    'vessel_type': vessel_type,
                    'wind_speed': wind_speed,
                    'wave_height': wave_height,
                    'draught': vessel_draught,
                    'speed_excess_percent': ((vessel_speed - safe_speed) / safe_speed) * 100
                }
            })
        
        # 2. HIGH WIND RISK (Empirical)
        if wind_speed > WIND_THRESHOLDS['MEDIUM']:
            severity = 'HIGH' if wind_speed > WIND_THRESHOLDS['HIGH'] else 'MEDIUM'
            risks.append({
                'type': 'HIGH_WINDS',
                'severity': severity,
                'message': f'High wind conditions: {wind_speed:.1f} m/s ({self._beaufort_scale(wind_speed)})',
                'details': {
                    'current_wind_speed': wind_speed,
                    'max_safe_wind_speed': WIND_THRESHOLDS['MEDIUM'],
                    'beaufort_scale': self._beaufort_scale(wind_speed),
                    'vessel_type_risk_factor': self._wind_risk_factor(vessel_type)
                }
            })
        
        # 3. HIGH WAVE RISK (Empirical)
        if wave_height > WAVE_THRESHOLDS['MEDIUM']:
            severity = 'HIGH' if wave_height > WAVE_THRESHOLDS['HIGH'] else 'MEDIUM'
            risks.append({
                'type': 'HIGH_WAVES',
                'severity': severity,
                'message': f'High wave conditions: {wave_height:.1f} meters',
                'details': {
                    'current_wave_height': wave_height,
                    'max_safe_wave_height': WAVE_THRESHOLDS['MEDIUM'],
                    'wave_period_estimate': self._estimate_wave_period(wave_height),  # seconds
                    'vessel_size_factor': 'high_risk' if vessel_length < 80 else 'medium_risk'
                }
            })
        
        # 4. NIGHT OPERATION RISK
        current_hour = datetime.utcnow().hour
        # Long nights in Norway - extended night period
        if current_hour >= 18 or current_hour <= 6:  # 6 PM to 6 AM UTC
            risks.append({
                'type': 'NIGHT_OPERATION',
                'severity': 'LOW',
                'message': f'Night operation (UTC hour: {current_hour}) - reduced visibility',
                'details': {
                    'current_hour_utc': current_hour,
                    'visibility_factor': 0.4,
                    'recommended_action': 'Increase radar watch and reduce speed'
                }
            })
        
        # 5. PROXIMITY TO HAZARDS (Using real hazard data from cache)
        if vessel_lat and vessel_lon and self.hazard_locations:
            nearby_hazards = self._find_nearby_hazards(vessel_lat, vessel_lon, radius_km=2.0)
            for hazard in nearby_hazards:
                distance_km = hazard['distance_km']
                if distance_km < 0.5:  # Less than 500 meters
                    severity = 'HIGH'
                elif distance_km < 1.0:  # Less than 1 km
                    severity = 'MEDIUM'
                else:
                    continue  # Skip hazards further than 1 km
                
                risks.append({
                    'type': 'HAZARD_PROXIMITY',
                    'severity': severity,
                    'message': f'Close to {hazard["name"]} ({hazard["type"]}) - distance: {distance_km:.2f} km',
                    'details': {
                        'hazard_name': hazard['name'],
                        'hazard_type': hazard['type'],
                        'distance_km': distance_km,
                        'hazard_lat': hazard['latitude'],
                        'hazard_lon': hazard['longitude'],
                        'bearing_degrees': self._calculate_bearing(vessel_lat, vessel_lon, hazard['latitude'], hazard['longitude'])
                    }
                })
        
        # 6. ROUTE DEVIATION RISK (If we have planned route data)
        if 'route_deviation_km' in vessel_data:
            deviation = vessel_data['route_deviation_km']
            if deviation > 5.0:  # 5 km deviation threshold
                severity = 'MEDIUM' if deviation < 10.0 else 'HIGH'
                risks.append({
                    'type': 'ROUTE_DEVIATION',
                    'severity': severity,
                    'message': f'Significant route deviation: {deviation:.1f} km from planned route',
                    'details': {
                        'deviation_km': deviation,
                        'max_allowed_deviation': 5.0,
                        'deviation_percent': (deviation / 5.0) * 100 if deviation > 0 else 0
                    }
                })
        
        return risks

    def _run_legacy_checks(self, vessel_data: Dict, weather_data: Optional[Dict] = None, 
                          route_data: Optional[Dict] = None) -> List[Dict]:
        """Run legacy risk checks for backward compatibility."""
        risks = []
        
        # Validate input
        if not vessel_data or 'lat' not in vessel_data or 'lon' not in vessel_data:
            return risks
        
        vessel_lat = vessel_data.get('lat')
        vessel_lon = vessel_data.get('lon')
        vessel_mmsi = vessel_data.get('mmsi', 'unknown')
        vessel_name = vessel_data.get('name', 'unknown')
        
        logger.debug(f"Running legacy checks for vessel {vessel_name} (MMSI: {vessel_mmsi})")
        
        # 1. Check proximity to all hazards
        hazard_risks = self._check_hazard_proximity_legacy(vessel_lat, vessel_lon, vessel_data)
        risks.extend(hazard_risks)
        
        # 2. Check weather conditions
        if weather_data:
            weather_risks = self._check_weather_conditions_legacy(vessel_data, weather_data)
            risks.extend(weather_risks)
        
        # 3. Check route deviation (if route data available)
        if route_data and route_data.get('waypoints'):
            deviation_risk = self._check_route_deviation_legacy(vessel_lat, vessel_lon, route_data)
            if deviation_risk:
                risks.append(deviation_risk)
        
        # 4. Check time of day for night operations
        time_risk = self._check_night_operation_legacy()
        if time_risk:
            risks.append(time_risk)
        
        # 5. Check speed relative to conditions
        if weather_data:
            speed_risk = self._check_speed_conditions_legacy(vessel_data, weather_data)
            if speed_risk:
                risks.append(speed_risk)
        
        return risks

    def _combine_risk_lists(self, new_risks: List[Dict], legacy_risks: List[Dict]) -> List[Dict]:
        """Combine risk lists, avoiding duplicates based on risk type and severity."""
        combined = []
        seen_types = set()
        
        # First add advanced risks
        for risk in new_risks:
            risk_key = f"{risk.get('type')}_{risk.get('severity')}"
            if risk_key not in seen_types:
                combined.append(risk)
                seen_types.add(risk_key)
        
        # Then add legacy risks if not already covered
        for risk in legacy_risks:
            risk_key = f"{risk.get('type')}_{risk.get('severity')}"
            if risk_key not in seen_types:
                combined.append(risk)
                seen_types.add(risk_key)
        
        return combined

    # --- Supporting utility functions for the advanced risk engine ---
    
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
    
    def _wind_risk_factor(self, vessel_type: str) -> str:
        """Determine wind risk factor based on vessel type."""
        high_risk_types = ['fishing', 'pleasure craft', 'sailing']
        medium_risk_types = ['passenger', 'general cargo']
        low_risk_types = ['tanker', 'container', 'cargo']
        
        if vessel_type in high_risk_types: return "high"
        if vessel_type in medium_risk_types: return "medium"
        if vessel_type in low_risk_types: return "low"
        return "medium"  # default
    
    def _estimate_wave_period(self, wave_height: float) -> float:
        """Empirical relationship between wave height and period for Norwegian waters."""
        # T ≈ 3.85 * √H (empirical formula)
        return round(3.85 * (wave_height ** 0.5), 1)
    
    def _find_nearby_hazards(self, lat: float, lon: float, radius_km: float) -> List[Dict]:
        """Find hazards near the vessel position from loaded hazard data."""
        nearby = []
        for hazard in self.hazard_locations:
            distance = self._calculate_distance_km(lat, lon, hazard['latitude'], hazard['longitude'])
            if distance <= radius_km:
                hazard_copy = hazard.copy()
                hazard_copy['distance_km'] = round(distance, 3)
                nearby.append(hazard_copy)
        return nearby
    
    def _calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points in kilometers."""
        from math import radians, sin, cos, sqrt, atan2
        R = 6371.0  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2 in degrees."""
        from math import radians, degrees, sin, cos, atan2
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        x = sin(dlon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        bearing = degrees(atan2(x, y))
        return (bearing + 360) % 360

    # --- Legacy functions (renamed to avoid conflicts) ---
    
    def _ensure_wave_height_data(self, weather_data: Dict) -> Dict:
        """
        Ensure wave_height exists in weather data.
        If missing, estimate it from wind speed using empirical formula.
        
        Args:
            weather_data: Weather data dictionary
            
        Returns:
            Updated weather data with wave_height
        """
        if 'wave_height' not in weather_data or weather_data['wave_height'] is None:
            wind_speed = weather_data.get('wind_speed', 0)
            # Empirical formula: wave_height ~ 0.02 * wind_speed^1.5
            estimated_wave_height = 0.02 * (wind_speed ** 1.5)
            weather_data = weather_data.copy()  # Don't modify original
            weather_data['wave_height'] = estimated_wave_height
            logger.debug(f"Estimated wave height: {estimated_wave_height:.2f}m from wind speed: {wind_speed:.1f}m/s")
        
        return weather_data

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
                    
                    weather_data = {
                        'wind_speed': instant.get('wind_speed'),
                        'wind_direction': instant.get('wind_from_direction'),
                        'temperature': instant.get('air_temperature'),
                        'pressure': instant.get('air_pressure_at_sea_level'),
                        'humidity': instant.get('relative_humidity'),
                        'cloudiness': instant.get('cloud_area_fraction')
                    }
                    
                    # Ensure wave_height is calculated
                    return self._ensure_wave_height_data(weather_data)
        except Exception as e:
            logger.debug(f"Weather fetch for location failed: {e}")
        
        return None

    def _check_hazard_proximity_legacy(self, lat: float, lon: float, vessel_data: Dict) -> List[Dict]:
        """Check proximity to all types of hazards (legacy version)."""
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
                # Extract coordinates
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

    def _check_weather_conditions_legacy(self, vessel_data: Dict, weather_data: Dict) -> List[Dict]:
        """Check weather conditions against vessel limits (legacy version)."""
        risks = []
        
        # Check wave height
        wave_height = weather_data.get('wave_height')
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

    def _check_route_deviation_legacy(self, lat: float, lon: float, route_data: Dict) -> Optional[Dict]:
        """Check if vessel is deviating from planned route (legacy version)."""
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

    def _check_night_operation_legacy(self) -> Optional[Dict]:
        """Check if operating during night hours (legacy version)."""
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

    def _check_speed_conditions_legacy(self, vessel_data: Dict, weather_data: Dict) -> Optional[Dict]:
        """Check if vessel speed is appropriate for conditions (legacy version)."""
        vessel_speed = vessel_data.get('speed')
        if not vessel_speed:
            return None
        
        wave_height = weather_data.get('wave_height', 0)
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