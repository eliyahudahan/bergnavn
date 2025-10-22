# backend/services/ais_service.py - New file
import socket
import threading
import time
import json
from datetime import datetime

class AISLiveService:
    """
    Real-time AIS Data Service for maritime tracking
    Connects to Kystverket AIS server: 153.44.253.27:5631
    Provides live ship data enriched with Data Science metrics
    """
    
    def __init__(self):
        self.ships_data = []
        self.is_connected = False
        self.ais_host = '153.44.253.27'
        self.ais_port = 5631
        self._stop_event = threading.Event()
        
    def start_ais_stream(self):
        """Start AIS data collection in background thread"""
        def collect_ais_data():
            while not self._stop_event.is_set():
                try:
                    # Try real AIS connection
                    self._connect_to_ais()
                    
                    # If connection fails, use enhanced simulation
                    if not self.is_connected:
                        self.ships_data = self._get_enhanced_mock_data()
                    
                    time.sleep(30)  # Refresh every 30 seconds
                    
                except Exception as e:
                    print(f"AIS service error: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=collect_ais_data, daemon=True)
        thread.start()
        print("✅ AIS Service started")
    
    def _connect_to_ais(self):
        """Attempt connection to real AIS server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.ais_host, self.ais_port))
            self.is_connected = True
            print("🔗 Connected to Kystverket AIS")
            
            # In production: parse real AIS data here
            # For now, use enhanced simulation
            self.ships_data = self._get_enhanced_mock_data()
            sock.close()
            
        except Exception as e:
            self.is_connected = False
            print(f"❌ AIS connection failed: {e}")
    
    def _get_enhanced_mock_data(self):
        """Enhanced mock data with realistic maritime patterns"""
        ships = []
        base_time = datetime.now()
        
        # Realistic ship routes Kristiansand ↔ Oslo
        routes = [
            {'name': 'VICTORIA WILSON', 'mmsi': '257158400', 'type': 'Cargo', 'speed': 14.2},
            {'name': 'KRISTIANSAND FJORD', 'mmsi': '258225000', 'type': 'Passenger', 'speed': 8.5},
            {'name': 'OSLO CARRIER', 'mmsi': '259187300', 'type': 'Container', 'speed': 16.8},
            {'name': 'SKAGERRAK TRADER', 'mmsi': '257894500', 'type': 'Tanker', 'speed': 11.3}
        ]
        
        for i, ship_info in enumerate(routes):
            # Simulate progressive movement
            progress = ((base_time.minute + (i * 15)) % 60) / 60.0
            
            if i % 2 == 0:  # Kristiansand → Oslo
                start_lat, start_lon = 58.1467, 8.0980
                end_lat, end_lon = 59.9139, 10.7522
                destination = 'OSLO'
            else:  # Oslo → Kristiansand
                start_lat, start_lon = 59.9139, 10.7522  
                end_lat, end_lon = 58.1467, 8.0980
                destination = 'KRISTIANSAND'
            
            current_lat = start_lat + (end_lat - start_lat) * progress
            current_lon = start_lon + (end_lon - start_lon) * progress
            
            ship = {
                'mmsi': ship_info['mmsi'],
                'name': ship_info['name'],
                'type': ship_info['type'],
                'lat': round(current_lat, 4),
                'lon': round(current_lon, 4),
                'sog': ship_info['speed'],  # Speed Over Ground
                'cog': 45 + (i * 30),      # Course Over Ground
                'heading': 50 + (i * 40),
                'destination': destination,
                'timestamp': base_time.isoformat(),
                'status': 'Underway',
                'data_quality': 'simulated'  # Would be 'live' with real AIS
            }
            
            # Add Data Science metrics
            ship.update(self._calculate_ship_metrics(ship))
            ships.append(ship)
        
        return ships
    
    def _calculate_ship_metrics(self, ship):
        """Calculate Data Science metrics for ship performance"""
        speed = ship.get('sog', 10)
        optimal_speed = 12  # Most fuel-efficient speed
        
        speed_deviation = abs(speed - optimal_speed)
        fuel_efficiency = max(0, 100 - (speed_deviation * 8))
        
        return {
            'fuel_efficiency_score': round(fuel_efficiency),
            'optimal_speed': optimal_speed,
            'speed_deviation': round(speed_deviation, 1),
            'optimization_potential': min(100, speed_deviation * 12)
        }
    
    def stop_service(self):
        """Stop the AIS service"""
        self._stop_event.set()

# Global instance
ais_service = AISLiveService()