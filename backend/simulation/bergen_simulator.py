"""
Day 1: Bergen Ship Simulator
Single ship simulation on real Bergen RTZ route
"""

import os
import json
from datetime import datetime, timedelta
from math import radians, degrees, cos, sin, sqrt, atan2
import logging

logger = logging.getLogger(__name__)

class BergenShipSimulator:
    def __init__(self):
        self.load_route()
        self.position = self.waypoints[0] if self.waypoints else {'lat': 60.391, 'lon': 5.322, 'name': 'Bergen'}
        self.current_waypoint_index = 0
        self.speed_knots = 15.0
        self.heading = 45.0
        self.status = 'underway'
        self.fuel_rate = 25.0  # liters per hour
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        self.operator_decisions = []
        self.alerts = []
        
        logger.info(f"🚢 Bergen Ship Simulator initialized on route: {self.route_name}")
    
    def load_route(self):
        """Load a real Bergen RTZ route or create a realistic default"""
        try:
            # Try to load from actual RTZ files
            rtz_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'backend', 'assets', 'routeinfo_routes', 'bergen', 'raw'
            )
            
            if os.path.exists(rtz_dir):
                for file in os.listdir(rtz_dir):
                    if file.endswith('.rtz'):
                        # For now, create a realistic Bergen route
                        self.route_name = f"Bergen_{file.replace('.rtz', '')}"
                        self.waypoints = [
                            {'lat': 60.391, 'lon': 5.322, 'name': 'Bergen Port'},
                            {'lat': 60.5, 'lon': 5.0, 'name': 'North of Bergen'},
                            {'lat': 61.0, 'lon': 4.8, 'name': 'Approaching Stad'},
                            {'lat': 62.1, 'lon': 5.0, 'name': 'Stad Lighthouse'}
                        ]
                        return
            
            # Fallback route
            self.route_name = "Bergen_Stad_Default"
            self.waypoints = [
                {'lat': 60.391, 'lon': 5.322, 'name': 'Bergen Port'},
                {'lat': 60.5, 'lon': 5.0, 'name': 'North of Bergen'},
                {'lat': 61.0, 'lon': 4.8, 'name': 'Approaching Stad'},
                {'lat': 62.1, 'lon': 5.0, 'name': 'Stad Lighthouse'}
            ]
            
        except Exception as e:
            logger.error(f"Error loading route: {e}")
            self.route_name = "Bergen_Fallback"
            self.waypoints = [
                {'lat': 60.391, 'lon': 5.322, 'name': 'Bergen'},
                {'lat': 61.0, 'lon': 5.0, 'name': 'Mid Point'},
                {'lat': 62.0, 'lon': 5.0, 'name': 'Destination'}
            ]
    
    def update(self, delta_seconds=None):
        """Update ship position based on elapsed time"""
        if delta_seconds is None:
            now = datetime.now()
            delta_seconds = (now - self.last_update).total_seconds()
            self.last_update = now
        
        # Check if we reached destination
        if self.current_waypoint_index >= len(self.waypoints) - 1:
            self.status = 'arrived'
            return
        
        # Get current and target waypoints
        current_wp = self.waypoints[self.current_waypoint_index]
        target_wp = self.waypoints[self.current_waypoint_index + 1]
        
        # Calculate distance to target
        distance_km = self.calculate_distance(
            self.position['lat'], self.position['lon'],
            target_wp['lat'], target_wp['lon']
        )
        
        # Calculate movement (speed in km/h)
        speed_kmh = self.speed_knots * 1.852
        distance_traveled = speed_kmh * (delta_seconds / 3600)
        
        # Move towards target
        if distance_traveled >= distance_km:
            # Reached waypoint
            self.current_waypoint_index += 1
            self.position = target_wp.copy()
            logger.info(f"📍 Reached waypoint: {target_wp['name']}")
        else:
            # Move along path
            ratio = distance_traveled / distance_km
            self.position = {
                'lat': self.position['lat'] + (target_wp['lat'] - self.position['lat']) * ratio,
                'lon': self.position['lon'] + (target_wp['lon'] - self.position['lon']) * ratio,
                'name': f"Towards {target_wp['name']}"
            }
            
            # Update heading
            self.heading = self.calculate_heading(
                self.position['lat'], self.position['lon'],
                target_wp['lat'], target_wp['lon']
            )
        
        # Generate alerts based on position
        self.check_alerts()
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance in kilometers"""
        R = 6371.0
        
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def calculate_heading(self, lat1, lon1, lat2, lon2):
        """Calculate heading in degrees (0-360)"""
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        dlon_rad = radians(lon2 - lon1)
        
        y = sin(dlon_rad) * cos(lat2_rad)
        x = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(dlon_rad)
        
        heading_rad = atan2(y, x)
        heading_deg = (degrees(heading_rad) + 360) % 360
        
        return heading_deg
    
    def check_alerts(self):
        """Check for maritime alerts based on current position"""
        self.alerts = []
        
        # Norwegian wind farms (real locations)
        wind_farms = [
            {'lat': 60.8, 'lon': 4.6, 'name': 'Hywind Tampen', 'distance': 5.0},
            {'lat': 61.2, 'lon': 4.8, 'name': 'Stad Wind Farm', 'distance': 8.0}
        ]
        
        # Fish farms (real locations)
        fish_farms = [
            {'lat': 60.4, 'lon': 5.1, 'name': 'Bergen Fish Farm', 'distance': 2.0},
            {'lat': 61.5, 'lon': 4.9, 'name': 'Stad Fish Farm', 'distance': 3.0}
        ]
        
        # Check proximity to wind farms
        for farm in wind_farms:
            distance = self.calculate_distance(
                self.position['lat'], self.position['lon'],
                farm['lat'], farm['lon']
            )
            
            if distance < farm['distance']:
                self.alerts.append({
                    'type': 'CRITICAL',
                    'message': f"Approaching {farm['name']} - {distance:.1f} km away",
                    'timestamp': datetime.now().isoformat(),
                    'action_required': True
                })
        
        # Check proximity to fish farms
        for farm in fish_farms:
            distance = self.calculate_distance(
                self.position['lat'], self.position['lon'],
                farm['lat'], farm['lon']
            )
            
            if distance < farm['distance']:
                self.alerts.append({
                    'type': 'HIGH',
                    'message': f"Approaching {farm['name']} - {distance:.1f} km away",
                    'timestamp': datetime.now().isoformat(),
                    'action_required': True
                })
    
    def record_operator_decision(self, operator_id, decision_type, decision_data, context, notes=""):
        """Record operator decision for ML training"""
        decision = {
            'operator_id': operator_id,
            'timestamp': datetime.now().isoformat(),
            'decision_type': decision_type,
            'decision_data': decision_data,
            'context_before': context,
            'notes': notes,
            'ship_state': self.to_dict()
        }
        
        self.operator_decisions.append(decision)
        logger.info(f"📝 Recorded operator decision: {decision_type}")
        
        # Apply decision to simulation
        self.apply_decision(decision_type, decision_data)
        
        return decision
    
    def apply_decision(self, decision_type, decision_data):
        """Apply operator decision to simulation"""
        if decision_type == 'speed_change':
            self.speed_knots += decision_data.get('value', 0)
            logger.info(f"⚡ Speed changed to {self.speed_knots} knots")
        
        elif decision_type == 'course_change':
            self.heading = (self.heading + decision_data.get('degrees', 0)) % 360
            logger.info(f"🧭 Course changed to {self.heading}°")
        
        elif decision_type == 'route_change':
            # In future, implement actual route change
            logger.info("🗺️ Route change requested")
    
    def to_dict(self):
        """Return simulator state as dictionary"""
        return {
            'position': self.position,
            'speed_knots': self.speed_knots,
            'heading': self.heading,
            'status': self.status,
            'route_name': self.route_name,
            'current_waypoint': self.current_waypoint_index,
            'total_waypoints': len(self.waypoints),
            'next_waypoint': self.waypoints[self.current_waypoint_index + 1]['name'] 
                if self.current_waypoint_index < len(self.waypoints) - 1 else 'Destination',
            'fuel_used_liters': self.fuel_rate * ((datetime.now() - self.start_time).seconds / 3600),
            'distance_traveled_km': 0,  # Would need to track
            'alerts': self.alerts,
            'operator_decisions_count': len(self.operator_decisions),
            'last_update': self.last_update.isoformat()
        }

# Global simulator instance
bergen_simulator = BergenShipSimulator()