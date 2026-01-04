"""
Integrated Ship Simulator for BergNavn
Connects to existing RTZ, Weather, Risk, and Alert services
Uses real Norwegian routes, real weather data, and existing risk assessment
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import math

# Configure logging
logger = logging.getLogger(__name__)


class IntegratedShipSimulator:
    """
    Main ship simulator that integrates with all existing BergNavn services.
    
    Key Features:
    1. Uses real RTZ routes from existing parser
    2. Integrates with real weather service
    3. Uses existing risk engine for safety checks
    4. Uses existing alerts service for notifications
    5. Records operator decisions for ML training
    6. Provides real-time simulation with adjustable speed
    """
    
    def __init__(self, route_name: str = "Bergen to Oslo"):
        """
        Initialize the simulator with existing services.
        
        Args:
            route_name: Name of the route to simulate
        """
        self.ship_id = "SIM-BERG-001"
        self.ship_name = "MS Bergen Navigator"
        self.ship_type = "Container Ship"
        self.status = "docked"
        
        # Initialize with existing services
        self._init_services()
        
        # Load real route data using existing RTZ parser
        self.route_data = self._load_real_route(route_name)
        self.waypoints = self.route_data.get('waypoints', [])
        self.current_waypoint_index = 0
        
        # Ship state
        self.current_position = self.waypoints[0] if self.waypoints else [60.3913, 5.3221]  # Bergen port
        self.speed_knots = 15.0
        self.heading = 0.0
        self.fuel_remaining = 100.0  # percentage
        self.total_distance_nm = self.route_data.get('total_distance_nm', 0)
        self.distance_traveled_nm = 0.0
        
        # Integration with existing services
        self.operator_decisions = []
        self.last_decision_time = None
        self.active_alerts = []
        
        # Simulation control
        self.running = False
        self.simulation_thread = None
        self.simulation_start_time = None
        self.last_update_time = datetime.now()
        
        # Performance tracking
        self.position_history = []
        self.weather_history = []
        self.risk_history = []
        
        logger.info(f"🚢 Integrated Ship Simulator initialized")
        logger.info(f"   Ship: {self.ship_name} ({self.ship_id})")
        logger.info(f"   Route: {self.route_data.get('route_name', route_name)}")
        logger.info(f"   Origin: {self.route_data.get('origin', 'Unknown')}")
        logger.info(f"   Destination: {self.route_data.get('destination', 'Unknown')}")
        logger.info(f"   Waypoints: {len(self.waypoints)}")
        logger.info(f"   Total Distance: {self.total_distance_nm:.1f} nm")
        
    def _init_services(self):
        """Initialize connections to existing BergNavn services."""
        try:
            # Import existing services
            from backend.services.weather_service import weather_service
            from backend.services.risk_engine import risk_engine
            from backend.services.alerts_service import maritime_alerts_service
            
            self.weather_service = weather_service
            self.risk_engine = risk_engine
            self.alerts_service = maritime_alerts_service
            
            logger.info("✅ Connected to existing BergNavn services")
            
        except ImportError as e:
            logger.warning(f"⚠️ Could not connect to some services: {e}")
            # Create dummy services for simulation
            self.weather_service = None
            self.risk_engine = None
            self.alerts_service = None
    
    def _load_real_route(self, route_name: str) -> Dict:
        """Load real RTZ route data using existing RTZ parser."""
        try:
            # Use existing RTZ parser to discover routes
            from backend.services.rtz_parser import discover_rtz_files
            
            all_routes = discover_rtz_files(enhanced=False)
            
            # Find Bergen routes
            bergen_routes = [r for r in all_routes if r.get('source_city') == 'bergen']
            
            if not bergen_routes:
                logger.warning(f"No Bergen routes found, using fallback")
                return self._create_fallback_route()
            
            # Use the first Bergen route found
            route_data = bergen_routes[0]
            
            # Ensure waypoints are in the correct format
            waypoints = []
            for wp in route_data.get('waypoints', []):
                if isinstance(wp, dict) and 'lat' in wp and 'lon' in wp:
                    waypoints.append([wp['lat'], wp['lon']])
            
            route_data['waypoints'] = waypoints
            
            logger.info(f"📊 Loaded real route: {route_data.get('route_name')}")
            logger.info(f"   From: {route_data.get('origin')}")
            logger.info(f"   To: {route_data.get('destination')}")
            logger.info(f"   Distance: {route_data.get('total_distance_nm', 0):.1f} nm")
            
            return route_data
            
        except ImportError as e:
            logger.warning(f"RTZ parser not available: {e}")
            return self._create_fallback_route()
        except Exception as e:
            logger.error(f"Error loading route: {e}")
            return self._create_fallback_route()
    
    def _create_fallback_route(self) -> Dict:
        """Create a fallback route when real routes are unavailable."""
        logger.info("Creating fallback route for simulation")
        
        # Bergen to Oslo approximate route
        waypoints = [
            [60.3913, 5.3221],  # Bergen
            [60.467, 5.500],    # North of Bergen
            [60.600, 5.800],    # Further north
            [60.800, 6.100],    # Towards Voss
            [60.700, 6.500],    # Inland
            [60.900, 7.100],    # Mountains
            [61.000, 7.800],    # Towards Oslo
            [59.9139, 10.7522]  # Oslo
        ]
        
        # Calculate total distance
        total_distance = 0.0
        for i in range(len(waypoints) - 1):
            total_distance += self._calculate_distance_nm(
                waypoints[i][0], waypoints[i][1],
                waypoints[i+1][0], waypoints[i+1][1]
            )
        
        return {
            'route_name': 'Bergen to Oslo (Fallback)',
            'waypoints': waypoints,
            'origin': 'Bergen',
            'destination': 'Oslo',
            'total_distance_nm': round(total_distance, 2),
            'waypoint_count': len(waypoints),
            'source_city': 'bergen',
            'data_source': 'fallback_simulation'
        }
    
    def start_simulation(self):
        """Start the ship simulation."""
        if self.running:
            logger.warning("⚠️ Simulation already running")
            return False
        
        self.running = True
        self.status = "underway"
        self.simulation_start_time = datetime.now()
        
        # Start simulation in background thread
        self.simulation_thread = threading.Thread(target=self._run_simulation, daemon=True)
        self.simulation_thread.start()
        
        logger.info(f"🚢 Simulation started: {self.ship_name}")
        logger.info(f"   Position: {self.current_position}")
        logger.info(f"   Speed: {self.speed_knots} knots")
        logger.info(f"   Destination: Waypoint {self.current_waypoint_index + 1}/{len(self.waypoints)}")
        
        return True
    
    def stop_simulation(self):
        """Stop the simulation."""
        if not self.running:
            return
        
        self.running = False
        self.status = "docked"
        
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2)
        
        # Calculate simulation statistics
        duration = datetime.now() - self.simulation_start_time if self.simulation_start_time else timedelta(0)
        
        logger.info(f"🛑 Simulation stopped")
        logger.info(f"   Duration: {duration}")
        logger.info(f"   Distance traveled: {self.distance_traveled_nm:.1f} nm")
        logger.info(f"   Decisions recorded: {len(self.operator_decisions)}")
    
    def _run_simulation(self):
        """Main simulation loop - runs in background thread."""
        logger.info("🔄 Starting simulation loop...")
        
        simulation_tick = 0
        
        while self.running:
            try:
                start_time = time.time()
                
                # Move ship toward next waypoint
                previous_position = self.current_position.copy()
                self._update_position()
                
                # Calculate distance traveled in this tick
                tick_distance = self._calculate_distance_nm(
                    previous_position[0], previous_position[1],
                    self.current_position[0], self.current_position[1]
                )
                self.distance_traveled_nm += tick_distance
                
                # Get real weather data if service is available
                current_weather = self._get_current_weather()
                
                # Check for alerts using existing alerts service
                if self.alerts_service:
                    vessel_data = self._create_vessel_data()
                    context = {'weather': current_weather}
                    alerts = self.alerts_service.generate_vessel_alerts(vessel_data, context)
                    self.active_alerts = alerts
                
                # Check risks using existing risk engine
                if self.risk_engine:
                    vessel_data = self._create_vessel_data()
                    risks = self.risk_engine.assess_vessel(vessel_data, current_weather)
                    self.risk_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'position': self.current_position.copy(),
                        'risks': risks
                    })
                
                # Log position every 10 ticks
                if simulation_tick % 10 == 0:
                    self._log_simulation_state()
                
                # Store position history (keep last 100 positions)
                self.position_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'position': self.current_position.copy(),
                    'speed': self.speed_knots,
                    'heading': self.heading
                })
                if len(self.position_history) > 100:
                    self.position_history.pop(0)
                
                # Store weather history
                if current_weather:
                    self.weather_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'weather': current_weather
                    })
                    if len(self.weather_history) > 50:
                        self.weather_history.pop(0)
                
                self.last_update_time = datetime.now()
                simulation_tick += 1
                
                # Calculate sleep time to maintain real-time simulation
                # 1 second real time = X simulation time based on speed
                elapsed = time.time() - start_time
                sleep_time = max(0.1, 1.0 - elapsed)  # Aim for 1 second per tick
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"⚠️ Simulation error: {e}")
                time.sleep(5)
    
    def _update_position(self):
        """Update ship position based on speed and heading toward next waypoint."""
        if not self.waypoints or self.current_waypoint_index >= len(self.waypoints):
            self.status = "arrived"
            self.running = False
            logger.info("🎯 Reached final destination!")
            return
        
        target = self.waypoints[self.current_waypoint_index]
        current_lat, current_lon = self.current_position
        
        # Calculate bearing to target
        target_bearing = self._calculate_bearing(current_lat, current_lon, target[0], target[1])
        
        # Adjust heading gradually toward target
        heading_diff = (target_bearing - self.heading) % 360
        if heading_diff > 180:
            heading_diff -= 360
        
        # Maximum turn rate: 10 degrees per tick
        max_turn = 10.0
        turn_amount = max(-max_turn, min(max_turn, heading_diff))
        self.heading = (self.heading + turn_amount) % 360
        
        # Calculate distance traveled in this tick
        # At speed_knots knots, distance in nm per hour = speed_knots
        # Per tick (1 second), distance = speed_knots / 3600
        distance_nm_per_tick = self.speed_knots / 3600.0
        
        # Move ship in current heading direction
        distance_degrees = distance_nm_per_tick / 60.0  # 1 nm = 1/60 degree approx
        
        # Convert distance and heading to lat/lon change
        lat_change = distance_degrees * math.cos(math.radians(self.heading))
        lon_change = distance_degrees * math.sin(math.radians(self.heading)) / math.cos(math.radians(current_lat))
        
        self.current_position = [
            current_lat + lat_change,
            current_lon + lon_change
        ]
        
        # Check if reached waypoint
        distance_to_target = self._calculate_distance_nm(
            current_lat, current_lon, target[0], target[1]
        )
        
        if distance_to_target < 0.5:  # Within 0.5 nm of waypoint
            self.current_waypoint_index += 1
            logger.info(f"📍 Reached waypoint {self.current_waypoint_index}/{len(self.waypoints)}")
            
            if self.current_waypoint_index >= len(self.waypoints):
                self.status = "arrived"
                self.running = False
                logger.info("🎯 Reached final destination!")
    
    def _get_current_weather(self) -> Dict:
        """Get current weather at ship position using existing weather service."""
        if not self.weather_service:
            # Fallback weather data
            return {
                'temperature_c': 8.5,
                'wind_speed_ms': 5.2,
                'wind_direction': 45,
                'wave_height_m': 1.2,
                'data_source': 'simulation_fallback'
            }
        
        try:
            lat, lon = self.current_position
            weather = self.weather_service.get_current_weather(lat, lon)
            return weather
        except Exception as e:
            logger.warning(f"Could not get weather: {e}")
            return {
                'temperature_c': 8.5,
                'wind_speed_ms': 5.2,
                'wind_direction': 45,
                'wave_height_m': 1.2,
                'data_source': 'fallback'
            }
    
    def _create_vessel_data(self) -> Dict:
        """Create vessel data dictionary for risk and alert services."""
        return {
            'mmsi': self.ship_id,
            'name': self.ship_name,
            'type': self.ship_type,
            'lat': self.current_position[0],
            'lon': self.current_position[1],
            'speed': self.speed_knots,
            'heading': self.heading,
            'draught': 8.5,  # meters
            'length': 200.0,  # meters
            'timestamp': datetime.now().isoformat()
        }
    
    def _log_simulation_state(self):
        """Log current simulation state."""
        lat, lon = self.current_position
        
        # Calculate progress
        total_waypoints = len(self.waypoints)
        progress = (self.current_waypoint_index / max(1, total_waypoints - 1)) * 100
        
        logger.info(f"📡 {self.ship_name}: "
                   f"[{lat:.4f}, {lon:.4f}] "
                   f"Speed: {self.speed_knots:.1f}kn "
                   f"Heading: {self.heading:.1f}° "
                   f"Progress: {progress:.1f}% "
                   f"Alerts: {len(self.active_alerts)}")
    
    def record_operator_decision(self, decision_type: str, decision_data: Dict, notes: str = "") -> Dict:
        """
        Record an operator decision (for ML training).
        
        Args:
            decision_type: Type of decision (speed_change, course_change, etc.)
            decision_data: Decision parameters
            notes: Optional notes from operator
            
        Returns:
            Recorded decision
        """
        decision = {
            'timestamp': datetime.now().isoformat(),
            'ship_id': self.ship_id,
            'decision_type': decision_type,
            'decision_data': decision_data,
            'context': {
                'position': self.current_position.copy(),
                'speed': self.speed_knots,
                'heading': self.heading,
                'fuel': self.fuel_remaining,
                'waypoint_index': self.current_waypoint_index,
                'total_waypoints': len(self.waypoints),
                'weather': self._get_current_weather(),
                'active_alerts': [alert.get('type') for alert in self.active_alerts[:3]]
            },
            'operator_notes': notes
        }
        
        self.operator_decisions.append(decision)
        self.last_decision_time = datetime.now()
        
        logger.info(f"📝 Operator decision recorded: {decision_type}")
        return decision
    
    def change_speed(self, delta_knots: float) -> float:
        """Change ship speed."""
        new_speed = max(5.0, min(25.0, self.speed_knots + delta_knots))
        old_speed = self.speed_knots
        self.speed_knots = new_speed
        
        logger.info(f"⚡ Speed changed: {old_speed:.1f} → {new_speed:.1f} knots")
        
        # Record this as an operator decision
        self.record_operator_decision(
            decision_type='speed_change',
            decision_data={'delta': delta_knots, 'new_speed': new_speed},
            notes=f"Operator adjusted speed by {delta_knots} knots"
        )
        
        return new_speed
    
    def change_course(self, delta_degrees: float) -> float:
        """Change ship course."""
        new_heading = (self.heading + delta_degrees) % 360
        old_heading = self.heading
        self.heading = new_heading
        
        logger.info(f"🧭 Course changed: {old_heading:.1f}° → {new_heading:.1f}°")
        
        # Record this as an operator decision
        self.record_operator_decision(
            decision_type='course_change',
            decision_data={'delta': delta_degrees, 'new_heading': new_heading},
            notes=f"Operator adjusted course by {delta_degrees} degrees"
        )
        
        return new_heading
    
    def get_status(self) -> Dict:
        """Get current simulation status."""
        return {
            'ship_id': self.ship_id,
            'ship_name': self.ship_name,
            'ship_type': self.ship_type,
            'status': self.status,
            'position': self.current_position,
            'speed_knots': self.speed_knots,
            'heading': self.heading,
            'fuel_remaining': self.fuel_remaining,
            
            'route_info': {
                'route_name': self.route_data.get('route_name'),
                'origin': self.route_data.get('origin'),
                'destination': self.route_data.get('destination'),
                'current_waypoint': self.current_waypoint_index,
                'total_waypoints': len(self.waypoints),
                'total_distance_nm': self.total_distance_nm,
                'distance_traveled_nm': round(self.distance_traveled_nm, 2),
                'progress_percent': round((self.current_waypoint_index / max(1, len(self.waypoints) - 1)) * 100, 1)
            },
            
            'simulation_info': {
                'running': self.running,
                'start_time': self.simulation_start_time.isoformat() if self.simulation_start_time else None,
                'last_update': self.last_update_time.isoformat(),
                'decisions_recorded': len(self.operator_decisions),
                'position_history_count': len(self.position_history),
                'weather_history_count': len(self.weather_history)
            },
            
            'services_status': {
                'weather_service': bool(self.weather_service),
                'risk_engine': bool(self.risk_engine),
                'alerts_service': bool(self.alerts_service)
            },
            
            'alerts': self.active_alerts[:5]  # Top 5 alerts
        }
    
    def get_operator_decisions(self, limit: int = 50) -> List[Dict]:
        """Get recorded operator decisions."""
        return self.operator_decisions[-limit:] if self.operator_decisions else []
    
    def get_position_history(self) -> List[Dict]:
        """Get position history."""
        return self.position_history
    
    def reset_simulation(self):
        """Reset simulation to initial state."""
        self.stop_simulation()
        
        self.current_position = self.waypoints[0] if self.waypoints else [60.3913, 5.3221]
        self.current_waypoint_index = 0
        self.speed_knots = 15.0
        self.heading = 0.0
        self.fuel_remaining = 100.0
        self.distance_traveled_nm = 0.0
        
        self.operator_decisions = []
        self.active_alerts = []
        self.position_history = []
        self.weather_history = []
        self.risk_history = []
        
        logger.info("�� Simulation reset to initial state")
    
    # ========== UTILITY FUNCTIONS ==========
    
    def _calculate_distance_nm(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in nautical miles."""
        R = 3440.065  # Earth radius in nautical miles
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2 in degrees."""
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlon = lon2_rad - lon1_rad
        x = math.sin(dlon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        
        bearing_rad = math.atan2(x, y)
        bearing_deg = math.degrees(bearing_rad)
        
        return (bearing_deg + 360) % 360


# Global simulator instance for easy access
_simulator_instance = None

def get_simulator(route_name: str = "Bergen to Oslo") -> IntegratedShipSimulator:
    """
    Get or create the simulator instance.
    
    Args:
        route_name: Route name for the simulation
        
    Returns:
        IntegratedShipSimulator instance
    """
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = IntegratedShipSimulator(route_name)
    return _simulator_instance
