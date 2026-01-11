"""
Real-time maritime vessel simulator.
Simulates vessel movement along RTZ routes with live alerts integration.
Features:
- Real-time movement based on actual routes
- Live alert integration
- Waypoint tracking and ETA calculation
- Fallback to Bergen as primary port
- Interactive map display
"""

import logging
import math
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import random
from enum import Enum

logger = logging.getLogger(__name__)

class VesselStatus(Enum):
    """Vessel status enumeration."""
    DOCKED = "docked"
    DEPARTING = "departing"
    UNDERWAY = "underway"
    ARRIVING = "arriving"
    ANCHORED = "anchored"
    EMERGENCY = "emergency"

class AlertLevel(Enum):
    """Alert level enumeration."""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"

@dataclass
class VesselPosition:
    """Vessel position data class."""
    lat: float
    lon: float
    heading: float  # degrees
    speed_knots: float
    timestamp: datetime
    waypoint_index: int = 0
    distance_to_next_waypoint_nm: float = 0.0
    eta_next_waypoint: Optional[datetime] = None

@dataclass
class Waypoint:
    """Waypoint data class."""
    name: str
    lat: float
    lon: float
    sequence: int
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    departure: Optional[datetime] = None

@dataclass
class SimulatedVessel:
    """Simulated vessel data class."""
    mmsi: str
    name: str
    type: str
    length_m: float
    draft_m: float
    max_speed_knots: float
    current_speed_knots: float
    status: VesselStatus
    position: VesselPosition
    route_id: str
    waypoints: List[Waypoint] = field(default_factory=list)
    alerts: List[Dict] = field(default_factory=list)
    departure_time: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    total_distance_nm: float = 0.0
    distance_traveled_nm: float = 0.0
    progress_percentage: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'mmsi': self.mmsi,
            'name': self.name,
            'type': self.type,
            'length_m': self.length_m,
            'draft_m': self.draft_m,
            'current_speed_knots': round(self.current_speed_knots, 1),
            'status': self.status.value,
            'position': {
                'lat': round(self.position.lat, 6),
                'lon': round(self.position.lon, 6),
                'heading': round(self.position.heading, 1),
                'speed_knots': round(self.position.speed_knots, 1),
                'timestamp': self.position.timestamp.isoformat(),
                'waypoint_index': self.position.waypoint_index,
                'distance_to_next_waypoint_nm': round(self.position.distance_to_next_waypoint_nm, 2),
                'eta_next_waypoint': self.position.eta_next_waypoint.isoformat() if self.position.eta_next_waypoint else None
            },
            'route_id': self.route_id,
            'waypoints': [
                {
                    'name': wp.name,
                    'lat': wp.lat,
                    'lon': wp.lon,
                    'sequence': wp.sequence,
                    'estimated_arrival': wp.estimated_arrival.isoformat() if wp.estimated_arrival else None,
                    'actual_arrival': wp.actual_arrival.isoformat() if wp.actual_arrival else None,
                    'departure': wp.departure.isoformat() if wp.departure else None
                } for wp in self.waypoints
            ],
            'alerts': self.alerts,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'estimated_arrival': self.estimated_arrival.isoformat() if self.estimated_arrival else None,
            'total_distance_nm': round(self.total_distance_nm, 1),
            'distance_traveled_nm': round(self.distance_traveled_nm, 1),
            'progress_percentage': round(self.progress_percentage, 1)
        }

class RealTimeSimulator:
    """
    Real-time maritime vessel simulator.
    Manages multiple simulated vessels with live updates.
    """
    
    def __init__(self):
        self.vessels: Dict[str, SimulatedVessel] = {}
        self.routes: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._running = False
        self._update_thread: Optional[threading.Thread] = None
        self.update_interval = 1.0  # Update every second
        
        # Norwegian ports in order of importance
        self.norwegian_ports = [
            {'city': 'Bergen', 'lat': 60.3913, 'lon': 5.3221, 'priority': 1},
            {'city': 'Oslo', 'lat': 59.9139, 'lon': 10.7522, 'priority': 2},
            {'city': 'Stavanger', 'lat': 58.9699, 'lon': 5.7331, 'priority': 3},
            {'city': 'Trondheim', 'lat': 63.4305, 'lon': 10.3951, 'priority': 4},
            {'city': 'Ålesund', 'lat': 62.4722, 'lon': 6.1497, 'priority': 5},
            {'city': 'Kristiansand', 'lat': 58.1467, 'lon': 7.9958, 'priority': 6},
            {'city': 'Drammen', 'lat': 59.7441, 'lon': 10.2045, 'priority': 7},
            {'city': 'Sandefjord', 'lat': 59.1312, 'lon': 10.2167, 'priority': 8},
            {'city': 'Åndalsnes', 'lat': 62.5675, 'lon': 7.6870, 'priority': 9},
            {'city': 'Flekkefjord', 'lat': 58.2970, 'lon': 6.6605, 'priority': 10}
        ]
        
        # Initialize with some vessels
        self._initialize_default_vessels()
    
    def _initialize_default_vessels(self):
        """Initialize with some default vessels."""
        try:
            # Try to get actual routes from the system
            from backend.services.route_service import route_service
            routes = route_service.get_all_routes_deduplicated()
            
            if routes and len(routes) > 0:
                # Use actual routes
                for i, route in enumerate(routes[:3]):  # First 3 routes
                    self._create_vessel_for_route(route, vessel_index=i)
            else:
                # Fallback: create vessels for Bergen routes
                self._create_fallback_vessels()
                
        except ImportError:
            # Fallback if route_service not available
            self._create_fallback_vessels()
    
    def _create_vessel_for_route(self, route: Dict, vessel_index: int = 0):
        """Create a vessel for a specific route."""
        route_id = route.get('route_name', f'route_{vessel_index}')
        
        # Create waypoints from route data
        waypoints_data = route.get('waypoints', [])
        if len(waypoints_data) < 2:
            logger.warning(f"Route {route_id} has insufficient waypoints")
            return
        
        waypoints = []
        for i, wp_data in enumerate(waypoints_data):
            waypoints.append(Waypoint(
                name=wp_data.get('name', f'WP{i+1}'),
                lat=wp_data.get('lat', 0),
                lon=wp_data.get('lon', 0),
                sequence=i
            ))
        
        # Vessel configuration
        vessel_types = ['Container Ship', 'Tanker', 'Bulk Carrier', 'Passenger Ship']
        vessel_type = vessel_types[vessel_index % len(vessel_types)]
        
        mmsi = f'259{vessel_index:06}'  # Norwegian MMSI prefix
        
        # Calculate total distance
        total_distance = route.get('total_distance_nm', 0)
        if total_distance == 0:
            # Estimate based on waypoints
            total_distance = self._calculate_route_distance(waypoints)
        
        # Create vessel
        departure_time = datetime.now()
        estimated_arrival = departure_time + timedelta(hours=total_distance / 15)  # Assume 15 knots
        
        vessel = SimulatedVessel(
            mmsi=mmsi,
            name=f"SimVessel_{route.get('origin', 'Bergen')}_{route.get('destination', 'Stavanger')}",
            type=vessel_type,
            length_m=150 + vessel_index * 50,
            draft_m=8 + vessel_index * 2,
            max_speed_knots=20,
            current_speed_knots=15,
            status=VesselStatus.DEPARTING,
            position=VesselPosition(
                lat=waypoints[0].lat,
                lon=waypoints[0].lon,
                heading=self._calculate_initial_heading(waypoints[0], waypoints[1]),
                speed_knots=15,
                timestamp=departure_time,
                waypoint_index=0,
                distance_to_next_waypoint_nm=self._calculate_distance(
                    waypoints[0].lat, waypoints[0].lon,
                    waypoints[1].lat, waypoints[1].lon
                )
            ),
            route_id=route_id,
            waypoints=waypoints,
            departure_time=departure_time,
            estimated_arrival=estimated_arrival,
            total_distance_nm=total_distance
        )
        
        # Update ETA for first waypoint
        if len(waypoints) > 1:
            distance = vessel.position.distance_to_next_waypoint_nm
            time_to_wp = timedelta(hours=distance / vessel.current_speed_knots)
            vessel.position.eta_next_waypoint = departure_time + time_to_wp
        
        with self._lock:
            self.vessels[mmsi] = vessel
            self.routes[route_id] = route
        
        logger.info(f"Created vessel {vessel.name} for route {route_id}")
    
    def _create_fallback_vessels(self):
        """Create fallback vessels when no routes are available."""
        # Bergen to Stavanger route
        bergen_stavanger = SimulatedVessel(
            mmsi='259001000',
            name="Bergen Explorer",
            type="Container Ship",
            length_m=200,
            draft_m=10,
            max_speed_knots=18,
            current_speed_knots=15,
            status=VesselStatus.UNDERWAY,
            position=VesselPosition(
                lat=60.3913,
                lon=5.3221,
                heading=180,
                speed_knots=15,
                timestamp=datetime.now(),
                waypoint_index=0,
                distance_to_next_waypoint_nm=25.0
            ),
            route_id="bergen_stavanger",
            waypoints=[
                Waypoint(name="Bergen Port", lat=60.3913, lon=5.3221, sequence=0),
                Waypoint(name="Fedjeosen", lat=60.8, lon=4.7, sequence=1),
                Waypoint(name="Stadthavet", lat=62.0, lon=5.0, sequence=2),
                Waypoint(name="Stavanger Port", lat=58.9699, lon=5.7331, sequence=3)
            ],
            departure_time=datetime.now() - timedelta(hours=1),
            estimated_arrival=datetime.now() + timedelta(hours=8),
            total_distance_nm=150.0,
            distance_traveled_nm=25.0,
            progress_percentage=16.7
        )
        
        # Update ETA for next waypoint
        bergen_stavanger.position.eta_next_waypoint = datetime.now() + timedelta(hours=1)
        
        with self._lock:
            self.vessels['259001000'] = bergen_stavanger
        
        logger.info("Created fallback vessel: Bergen Explorer")
    
    def _calculate_route_distance(self, waypoints: List[Waypoint]) -> float:
        """Calculate total distance of a route in nautical miles."""
        total_distance = 0.0
        for i in range(len(waypoints) - 1):
            wp1 = waypoints[i]
            wp2 = waypoints[i + 1]
            distance = self._calculate_distance(wp1.lat, wp1.lon, wp2.lat, wp2.lon)
            total_distance += distance
        return total_distance
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in nautical miles."""
        # Haversine formula
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
    
    def _calculate_initial_heading(self, wp1: Waypoint, wp2: Waypoint) -> float:
        """Calculate initial heading from waypoint 1 to waypoint 2."""
        lat1 = math.radians(wp1.lat)
        lon1 = math.radians(wp1.lon)
        lat2 = math.radians(wp2.lat)
        lon2 = math.radians(wp2.lon)
        
        dlon = lon2 - lon1
        
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        initial_heading = math.atan2(x, y)
        initial_heading = math.degrees(initial_heading)
        
        # Normalize to 0-360
        initial_heading = (initial_heading + 360) % 360
        
        return initial_heading
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2."""
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)
        
        dlon = lon2 - lon1
        
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        
        return (bearing + 360) % 360
    
    def start(self):
        """Start the real-time simulation."""
        if self._running:
            return
        
        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
        logger.info("Real-time simulator started")
    
    def stop(self):
        """Stop the real-time simulation."""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=2.0)
        logger.info("Real-time simulator stopped")
    
    def _update_loop(self):
        """Main update loop for real-time simulation."""
        while self._running:
            try:
                self._update_vessels()
                self._generate_alerts()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in simulation update loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _update_vessels(self):
        """Update all vessel positions."""
        current_time = datetime.now()
        
        with self._lock:
            for mmsi, vessel in list(self.vessels.items()):
                try:
                    self._update_vessel_position(vessel, current_time)
                except Exception as e:
                    logger.error(f"Error updating vessel {mmsi}: {e}")
    
    def _update_vessel_position(self, vessel: SimulatedVessel, current_time: datetime):
        """Update a single vessel's position."""
        if vessel.status == VesselStatus.DOCKED:
            return
        
        # Get current and next waypoint
        current_wp_index = vessel.position.waypoint_index
        if current_wp_index >= len(vessel.waypoints) - 1:
            # Arrived at final destination
            vessel.status = VesselStatus.ARRIVING
            vessel.position.speed_knots = 0
            vessel.current_speed_knots = 0
            
            # Mark final waypoint arrival
            if vessel.waypoints[-1].actual_arrival is None:
                vessel.waypoints[-1].actual_arrival = current_time
            
            return
        
        current_wp = vessel.waypoints[current_wp_index]
        next_wp = vessel.waypoints[current_wp_index + 1]
        
        # Calculate bearing to next waypoint
        target_bearing = self._calculate_bearing(
            vessel.position.lat, vessel.position.lon,
            next_wp.lat, next_wp.lon
        )
        
        # Gradually adjust heading toward target
        heading_diff = target_bearing - vessel.position.heading
        if abs(heading_diff) > 180:
            heading_diff = heading_diff - 360 if heading_diff > 0 else heading_diff + 360
        
        # Adjust heading (max 5 degrees per update)
        max_heading_change = 5.0
        heading_change = max(-max_heading_change, min(max_heading_change, heading_diff))
        vessel.position.heading = (vessel.position.heading + heading_change) % 360
        
        # Calculate movement
        speed_ms = vessel.position.speed_knots * 0.514444  # knots to m/s
        time_elapsed = self.update_interval / 3600  # hours
        
        # Calculate distance moved this update
        distance_moved_nm = vessel.position.speed_knots * time_elapsed
        
        # Update vessel's traveled distance
        vessel.distance_traveled_nm += distance_moved_nm
        
        # Update position (simplified great circle movement)
        lat_rad = math.radians(vessel.position.lat)
        lon_rad = math.radians(vessel.position.lon)
        
        distance_rad = distance_moved_nm / 3440.065  # Convert NM to radians
        
        new_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(distance_rad) +
            math.cos(lat_rad) * math.sin(distance_rad) * math.cos(math.radians(vessel.position.heading))
        )
        
        new_lon_rad = lon_rad + math.atan2(
            math.sin(math.radians(vessel.position.heading)) * math.sin(distance_rad) * math.cos(lat_rad),
            math.cos(distance_rad) - math.sin(lat_rad) * math.sin(new_lat_rad)
        )
        
        vessel.position.lat = math.degrees(new_lat_rad)
        vessel.position.lon = math.degrees(new_lon_rad)
        vessel.position.timestamp = current_time
        
        # Update distance to next waypoint
        distance_to_next = self._calculate_distance(
            vessel.position.lat, vessel.position.lon,
            next_wp.lat, next_wp.lon
        )
        vessel.position.distance_to_next_waypoint_nm = distance_to_next
        
        # Update ETA for next waypoint
        if vessel.position.speed_knots > 0:
            hours_to_next = distance_to_next / vessel.position.speed_knots
            vessel.position.eta_next_waypoint = current_time + timedelta(hours=hours_to_next)
        
        # Check if we've reached the next waypoint
        waypoint_radius_nm = 0.5  # Consider reached if within 0.5 NM
        if distance_to_next <= waypoint_radius_nm:
            # Mark current waypoint departure
            current_wp.departure = current_time
            
            # Mark next waypoint arrival
            next_wp.actual_arrival = current_time
            
            # Move to next waypoint
            vessel.position.waypoint_index += 1
            
            # If there's another waypoint after this, update distance
            if vessel.position.waypoint_index < len(vessel.waypoints) - 1:
                next_next_wp = vessel.waypoints[vessel.position.waypoint_index + 1]
                next_distance = self._calculate_distance(
                    next_wp.lat, next_wp.lon,
                    next_next_wp.lat, next_next_wp.lon
                )
                vessel.position.distance_to_next_waypoint_nm = next_distance
            
            logger.info(f"Vessel {vessel.name} reached waypoint {next_wp.name}")
        
        # Update progress percentage
        if vessel.total_distance_nm > 0:
            vessel.progress_percentage = min(100.0, (vessel.distance_traveled_nm / vessel.total_distance_nm) * 100)
        
        # Update vessel status based on progress
        if vessel.progress_percentage >= 95:
            vessel.status = VesselStatus.ARRIVING
        elif vessel.progress_percentage > 0:
            vessel.status = VesselStatus.UNDERWAY
    
    def _generate_alerts(self):
        """Generate alerts for vessels."""
        current_time = datetime.now()
        
        with self._lock:
            for vessel in self.vessels.values():
                if vessel.status in [VesselStatus.DOCKED, VesselStatus.EMERGENCY]:
                    continue
                
                # Clear old alerts (older than 1 hour)
                vessel.alerts = [a for a in vessel.alerts 
                               if current_time - datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) < timedelta(hours=1)]
                
                # Generate new alerts
                new_alerts = []
                
                # Speed alert
                if vessel.position.speed_knots > vessel.max_speed_knots * 0.9:
                    new_alerts.append({
                        'type': 'SPEED_WARNING',
                        'level': AlertLevel.WARNING.value,
                        'message': f"High speed: {vessel.position.speed_knots:.1f} knots",
                        'timestamp': current_time.isoformat(),
                        'details': {
                            'current_speed': vessel.position.speed_knots,
                            'max_speed': vessel.max_speed_knots
                        }
                    })
                
                # Proximity to waypoint alert
                if vessel.position.distance_to_next_waypoint_nm < 2.0:
                    next_wp = vessel.waypoints[min(vessel.position.waypoint_index + 1, len(vessel.waypoints) - 1)]
                    new_alerts.append({
                        'type': 'WAYPOINT_APPROACH',
                        'level': AlertLevel.INFO.value,
                        'message': f"Approaching {next_wp.name} ({vessel.position.distance_to_next_waypoint_nm:.1f} NM)",
                        'timestamp': current_time.isoformat(),
                        'details': {
                            'waypoint': next_wp.name,
                            'distance_nm': vessel.position.distance_to_next_waypoint_nm
                        }
                    })
                
                # Progress alert
                if vessel.progress_percentage > 0 and vessel.progress_percentage % 25 < 1:
                    new_alerts.append({
                        'type': 'PROGRESS_UPDATE',
                        'level': AlertLevel.INFO.value,
                        'message': f"Progress: {vessel.progress_percentage:.1f}% complete",
                        'timestamp': current_time.isoformat(),
                        'details': {
                            'progress': vessel.progress_percentage,
                            'distance_traveled': vessel.distance_traveled_nm,
                            'total_distance': vessel.total_distance_nm
                        }
                    })
                
                # Add new alerts
                vessel.alerts.extend(new_alerts)
    
    def get_all_vessels(self) -> List[Dict]:
        """Get all simulated vessels."""
        with self._lock:
            return [vessel.to_dict() for vessel in self.vessels.values()]
    
    def get_vessel(self, mmsi: str) -> Optional[Dict]:
        """Get a specific vessel by MMSI."""
        with self._lock:
            vessel = self.vessels.get(mmsi)
            return vessel.to_dict() if vessel else None
    
    def create_vessel(self, route_name: str, origin: str, destination: str) -> Optional[Dict]:
        """Create a new simulated vessel for a route."""
        try:
            # Try to find a matching route
            from backend.services.route_service import route_service
            routes = route_service.get_all_routes_deduplicated()
            
            matching_routes = [
                r for r in routes 
                if r.get('origin', '').lower() == origin.lower() 
                and r.get('destination', '').lower() == destination.lower()
            ]
            
            if matching_routes:
                route = matching_routes[0]
                vessel_index = len(self.vessels)
                self._create_vessel_for_route(route, vessel_index)
                
                # Return the newly created vessel
                mmsi = f'259{vessel_index:06}'
                return self.get_vessel(mmsi)
            else:
                logger.warning(f"No route found from {origin} to {destination}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating vessel: {e}")
            return None
    
    def update_vessel_speed(self, mmsi: str, speed_knots: float) -> bool:
        """Update vessel speed."""
        with self._lock:
            vessel = self.vessels.get(mmsi)
            if vessel:
                vessel.current_speed_knots = max(0, min(speed_knots, vessel.max_speed_knots))
                vessel.position.speed_knots = vessel.current_speed_knots
                return True
            return False
    
    def get_simulation_status(self) -> Dict:
        """Get overall simulation status."""
        with self._lock:
            vessels_count = len(self.vessels)
            active_vessels = sum(1 for v in self.vessels.values() 
                               if v.status not in [VesselStatus.DOCKED, VesselStatus.EMERGENCY])
            
            return {
                'timestamp': datetime.now().isoformat(),
                'running': self._running,
                'vessels_count': vessels_count,
                'active_vessels': active_vessels,
                'update_interval': self.update_interval,
                'ports_covered': [port['city'] for port in self.norwegian_ports]
            }

# Global simulator instance
realtime_simulator = RealTimeSimulator()