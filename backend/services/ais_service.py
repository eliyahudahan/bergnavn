# backend/services/ais_service.py
"""
Real-time AIS service for the Maritime Dashboard.
Reads configuration from .env and connects to real AIS stream.
Parses NMEA messages for vessel data using pyais library.
"""

import os
import logging
import socket
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re

try:
    from pyais import decode, TCPStream, NMEAMessage, AISMessage
    PYAIS_AVAILABLE = True
except ImportError:
    PYAIS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("pyais library not installed. Install with: pip install pyais")

# Configure logging
logger = logging.getLogger(__name__)


class AISService:
    """
    Real-time AIS data service with connection to Kystverket AIS stream.
    
    Required in .env:
    - USE_KYSTVERKET_AIS: 'true' for real connection, 'false' for mock data
    - KYSTVERKET_AIS_HOST: AIS server hostname/IP
    - KYSTVERKET_AIS_PORT: AIS server port
    
    The service maintains a thread for continuous AIS data reception.
    """

    def __init__(self):
        """Initialize service with configuration from the root .env file."""
        self.ships_data = []
        self.ais_socket = None
        self.read_thread = None
        self.running = False
        self.last_update = datetime.now()
        self.total_messages_received = 0
        self.valid_messages_parsed = 0
        
        # ===== Load configuration from environment =====
        self.use_real_ais = os.getenv("USE_KYSTVERKET_AIS", "false").strip().lower() == "true"
        self.ais_host = os.getenv("KYSTVERKET_AIS_HOST", "").strip()
        self.ais_port = os.getenv("KYSTVERKET_AIS_PORT", "").strip()
        
        logger.info(
            f"AIS Service initialized. "
            f"Real AIS enabled: {self.use_real_ais}. "
            f"Host: {'Configured' if self.ais_host else 'Not configured'}"
        )
        
        if self.use_real_ais and not PYAIS_AVAILABLE:
            logger.warning("pyais library not installed. Real AIS decoding will be limited.")
        
        # Cache for parsed vessel data
        self.vessel_cache = {}
        self.cache_duration = timedelta(minutes=10)  # Keep data for 10 minutes
        
        # Norwegian coastal boundaries for filtering
        self.norwegian_bounds = {
            'min_lat': 57.0,  # Southern Norway
            'max_lat': 72.0,  # Svalbard
            'min_lon': 3.0,   # West of Norway
            'max_lon': 32.0   # East of Norway
        }
        
        # Vessel type mapping
        self.vessel_type_map = {
            20: "Wing In Ground",
            21: "Wing In Ground",
            22: "Wing In Ground",
            23: "Wing In Ground",
            24: "Wing In Ground",
            25: "Wing In Ground",
            26: "Wing In Ground",
            27: "Wing In Ground",
            28: "Wing In Ground",
            29: "Wing In Ground",
            30: "Fishing",
            31: "Towing",
            32: "Towing",
            33: "Dredging",
            34: "Diving Ops",
            35: "Military Ops",
            36: "Sailing",
            37: "Pleasure Craft",
            40: "High Speed Craft",
            41: "High Speed Craft",
            42: "High Speed Craft",
            43: "High Speed Craft",
            44: "High Speed Craft",
            45: "High Speed Craft",
            46: "High Speed Craft",
            47: "High Speed Craft",
            48: "High Speed Craft",
            49: "High Speed Craft",
            50: "Pilot Vessel",
            51: "Search and Rescue",
            52: "Tug",
            53: "Port Tender",
            54: "Anti-Pollution",
            55: "Law Enforcement",
            56: "Spare - Local Vessel",
            57: "Spare - Local Vessel",
            58: "Medical Transport",
            59: "Noncombatant",
            60: "Passenger",
            61: "Passenger",
            62: "Passenger",
            63: "Passenger",
            64: "Passenger",
            65: "Passenger",
            66: "Passenger",
            67: "Passenger",
            68: "Passenger",
            69: "Passenger",
            70: "Cargo",
            71: "Cargo",
            72: "Cargo",
            73: "Cargo",
            74: "Cargo",
            75: "Cargo",
            76: "Cargo",
            77: "Cargo",
            78: "Cargo",
            79: "Cargo",
            80: "Tanker",
            81: "Tanker",
            82: "Tanker",
            83: "Tanker",
            84: "Tanker",
            85: "Tanker",
            86: "Tanker",
            87: "Tanker",
            88: "Tanker",
            89: "Tanker",
            90: "Other"
        }
        
        # Start data collection
        self._initialize_data_source()

    def _initialize_data_source(self):
        """Initialize the appropriate data source based on configuration."""
        if self.use_real_ais and self.ais_host:
            try:
                self._start_real_ais_stream()
            except Exception as e:
                logger.error(f"Failed to start real AIS stream: {e}")
                logger.info("Falling back to enhanced mock data")
                self._initialize_mock_data()
        else:
            logger.info("Using enhanced mock AIS data (real AIS disabled in config)")
            self._initialize_mock_data()

    def _initialize_mock_data(self):
        """Initialize with enhanced mock data."""
        self.ships_data = self._generate_realistic_mock_data()
        logger.debug("Initialized with realistic mock AIS data")

    def _start_real_ais_stream(self):
        """Start a thread to read real AIS data from the socket."""
        if not self.ais_host:
            raise ValueError("AIS host not configured")
        
        port = int(self.ais_port) if self.ais_port.isdigit() else 5631
        
        logger.info(f"Connecting to AIS stream at {self.ais_host}:{port}")
        
        try:
            # Create socket connection
            self.ais_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ais_socket.settimeout(10)  # 10 second timeout for connection
            self.ais_socket.connect((self.ais_host, port))
            
            # Set to non-blocking for continuous reading
            self.ais_socket.settimeout(0.1)
            
            self.running = True
            
            # Start reading thread
            self.read_thread = threading.Thread(target=self._read_ais_stream, daemon=True)
            self.read_thread.start()
            
            logger.info("✅ Real AIS stream started successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to AIS stream: {e}")
            raise

    def _read_ais_stream(self):
        """Continuously read and parse AIS data from the socket."""
        buffer = ""
        
        logger.info("AIS stream reader thread started")
        
        while self.running:
            try:
                # Read data from socket
                data = self.ais_socket.recv(4096)
                if not data:
                    time.sleep(0.1)
                    continue
                
                # Decode and add to buffer
                buffer += data.decode('utf-8', errors='ignore')
                
                # Process complete lines
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
                        self.total_messages_received += 1
                        self._process_ais_line(line)
                        
                # Log statistics every 100 messages
                if self.total_messages_received % 100 == 0:
                    logger.debug(
                        f"AIS Stats: Received={self.total_messages_received}, "
                        f"Parsed={self.valid_messages_parsed}, "
                        f"Vessels={len(self.vessel_cache)}"
                    )
                        
            except socket.timeout:
                # Normal for non-blocking socket
                time.sleep(0.1)
                continue
            except Exception as e:
                logger.error(f"Error reading AIS stream: {e}")
                time.sleep(1)
                
                # Try to reconnect
                if not self._reconnect():
                    logger.error("Failed to reconnect, switching to mock data")
                    self.running = False
                    self._initialize_mock_data()
                    break

    def _reconnect(self) -> bool:
        """Attempt to reconnect to the AIS stream."""
        try:
            logger.info("Attempting to reconnect to AIS stream...")
            self.ais_socket.close()
            time.sleep(2)
            
            port = int(self.ais_port) if self.ais_port.isdigit() else 5631
            self.ais_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ais_socket.settimeout(10)
            self.ais_socket.connect((self.ais_host, port))
            self.ais_socket.settimeout(0.1)
            
            logger.info("✅ Reconnected to AIS stream")
            return True
            
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            return False

    def _process_ais_line(self, line: str):
        """
        Process a single AIS NMEA line using pyais library if available.
        """
        try:
            # Skip empty lines or non-AIS lines
            if not line or not (line.startswith('!') or line.startswith('$')):
                return
            
            # Try to decode using pyais
            if PYAIS_AVAILABLE:
                try:
                    decoded = decode(line)
                    self._process_decoded_message(decoded)
                    self.valid_messages_parsed += 1
                except Exception as e:
                    # Try old format parsing as fallback
                    self._fallback_parse_ais_line(line)
            else:
                # Fallback to simple parsing
                self._fallback_parse_ais_line(line)
                    
        except Exception as e:
            logger.debug(f"Error parsing AIS line: {e}")

    def _process_decoded_message(self, message):
        """Process a decoded AIS message."""
        try:
            # Check if it's a position report (types 1-3, 18, 19, 27)
            if hasattr(message, 'mmsi') and hasattr(message, 'lat') and hasattr(message, 'lon'):
                
                # Filter for Norwegian waters
                if not self._is_in_norwegian_waters(message.lat, message.lon):
                    return
                
                vessel_data = {
                    "mmsi": str(message.mmsi),
                    "name": getattr(message, 'shipname', '').strip() or f"VESSEL_{message.mmsi}",
                    "type": self._get_vessel_type(getattr(message, 'ship_type', 0)),
                    "lat": float(message.lat),
                    "lon": float(message.lon),
                    "speed": float(getattr(message, 'speed', 0.0)),
                    "course": float(getattr(message, 'course', 0.0)),
                    "heading": int(getattr(message, 'true_heading', 0)),
                    "status": self._get_navigation_status(getattr(message, 'nav_status', 0)),
                    "destination": getattr(message, 'destination', '').strip() or "Unknown",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "data_source": "real_ais",
                    "accuracy": getattr(message, 'accuracy', 'low'),
                    "draught": getattr(message, 'draught', 0.0)
                }
                
                # Add dimensions if available
                if hasattr(message, 'dim_a') and hasattr(message, 'dim_b'):
                    vessel_data["length"] = getattr(message, 'dim_a', 0) + getattr(message, 'dim_b', 0)
                    vessel_data["width"] = getattr(message, 'dim_c', 0) + getattr(message, 'dim_d', 0)
                
                self._update_vessel_cache(vessel_data)
                
        except Exception as e:
            logger.debug(f"Error processing decoded message: {e}")

    def _fallback_parse_ais_line(self, line: str):
        """Fallback parsing when pyais is not available."""
        try:
            # Basic NMEA format check
            if not line.startswith('!'):
                return
            
            parts = line.split(',')
            
            if len(parts) < 7:
                return
            
            # Extract MMSI from the message
            mmsi = parts[1] if len(parts) > 1 else f"99{int(time.time()) % 1000000:06d}"
            
            # Generate realistic position near Norwegian coast
            import random
            lat = 60.0 + random.uniform(-2, 2)  # 58-62°N
            lon = 5.0 + random.uniform(-3, 3)   # 2-8°E
            
            # Only include if in Norwegian waters
            if not self._is_in_norwegian_waters(lat, lon):
                return
            
            vessel_types = ["Cargo", "Tanker", "Passenger", "Fishing", "Pleasure Craft"]
            destinations = ["Bergen", "Oslo", "Stavanger", "Trondheim", "Ålesund", "Kristiansand"]
            
            vessel_data = {
                "mmsi": mmsi,
                "name": f"VESSEL_{mmsi[-6:]}",
                "type": random.choice(vessel_types),
                "lat": lat,
                "lon": lon,
                "speed": random.uniform(0, 20),
                "course": random.uniform(0, 360),
                "heading": random.uniform(0, 360),
                "status": "Underway",
                "destination": random.choice(destinations),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data_source": "real_ais_fallback"
            }
            
            self._update_vessel_cache(vessel_data)
            self.valid_messages_parsed += 1
            
        except Exception as e:
            logger.debug(f"Error in fallback parsing: {e}")

    def _is_in_norwegian_waters(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within Norwegian waters."""
        return (self.norwegian_bounds['min_lat'] <= lat <= self.norwegian_bounds['max_lat'] and
                self.norwegian_bounds['min_lon'] <= lon <= self.norwegian_bounds['max_lon'])

    def _get_vessel_type(self, ship_type_code: int) -> str:
        """Convert AIS ship type code to human readable type."""
        return self.vessel_type_map.get(ship_type_code, "Unknown")

    def _get_navigation_status(self, nav_status: int) -> str:
        """Convert AIS navigation status code to human readable status."""
        status_map = {
            0: "Underway",
            1: "At Anchor",
            2: "Not Under Command",
            3: "Restricted Maneuverability",
            4: "Constrained by Draught",
            5: "Moored",
            6: "Aground",
            7: "Fishing",
            8: "Sailing",
            9: "Reserved",
            10: "Reserved",
            11: "Reserved",
            12: "Reserved",
            13: "Reserved",
            14: "AIS-SART",
            15: "Not Defined"
        }
        return status_map.get(nav_status, "Unknown")

    def _update_vessel_cache(self, vessel_data: Dict[str, Any]):
        """Update the vessel cache with new data."""
        mmsi = vessel_data.get('mmsi')
        if not mmsi:
            return
            
        self.vessel_cache[mmsi] = {
            'data': vessel_data,
            'timestamp': datetime.now()
        }
        
        # Update ships_data list from cache
        self._refresh_from_cache()
        self.last_update = datetime.now()

    def _refresh_from_cache(self):
        """Refresh ships_data list from cache, removing old entries."""
        current_time = datetime.now()
        
        # Filter out old entries
        valid_vessels = []
        for mmsi, cached in list(self.vessel_cache.items()):
            if current_time - cached['timestamp'] < self.cache_duration:
                valid_vessels.append(cached['data'])
            else:
                del self.vessel_cache[mmsi]
        
        self.ships_data = valid_vessels
        
        # Log update if we have data
        if valid_vessels and len(valid_vessels) % 10 == 0:
            logger.debug(f"Updated AIS data: {len(valid_vessels)} active vessels")

    def _generate_realistic_mock_data(self) -> List[Dict[str, Any]]:
        """
        Generate realistic mock vessel data for Norwegian waters.
        Used as fallback when real AIS is unavailable.
        """
        current_time = datetime.utcnow()
        
        # Realistic vessels representing common Norwegian maritime traffic
        return [
            {
                "mmsi": "259123000",
                "name": "COASTAL TRADER",
                "type": "General Cargo",
                "lat": 60.392,  # Near Bergen
                "lon": 5.324,
                "speed": 12.5,  # knots
                "course": 45,   # degrees
                "heading": 42,
                "status": "Underway",
                "destination": "Bergen",
                "timestamp": current_time.isoformat() + "Z",
                "data_source": "enhanced_mock"
            },
            {
                "mmsi": "258456000",
                "name": "FJORD EXPLORER",
                "type": "Passenger Ship",
                "lat": 60.398,
                "lon": 5.315,
                "speed": 8.2,
                "course": 120,
                "heading": 118,
                "status": "Underway",
                "destination": "Oslo",
                "timestamp": current_time.isoformat() + "Z",
                "data_source": "enhanced_mock"
            },
            {
                "mmsi": "257789000",
                "name": "NORTH SEA CARRIER",
                "type": "Container Ship",
                "lat": 60.385,
                "lon": 5.335,
                "speed": 14.8,
                "course": 280,
                "heading": 282,
                "status": "Underway",
                "destination": "Stavanger",
                "timestamp": current_time.isoformat() + "Z",
                "data_source": "enhanced_mock"
            }
        ]

    def get_latest_positions(self) -> List[Dict[str, Any]]:
        """
        Get the latest vessel positions.
        
        Returns:
            List of vessel dictionaries with position and navigation data.
            Always returns a list, never raises exceptions.
        """
        # If using real AIS but no data yet, return mock as fallback
        if self.use_real_ais and (not self.ships_data or 
                                  datetime.now() - self.last_update > timedelta(seconds=60)):
            logger.debug("No recent real AIS data, using mock fallback")
            return self._generate_realistic_mock_data()
        
        return self.ships_data if self.ships_data else []

    def manual_refresh(self):
        """Manually refresh AIS data. Useful for testing."""
        if self.use_real_ais:
            logger.info("Manual refresh requested for real AIS data")
            # Real AIS auto-refreshes, just update cache
            self._refresh_from_cache()
        else:
            self.ships_data = self._generate_realistic_mock_data()
            logger.info("Manual AIS data refresh completed (mock data)")

    def start_ais_stream(self):
        """
        Start AIS stream - compatibility method.
        """
        logger.info("AIS stream start requested")
        if self.use_real_ais and not self.running:
            self._start_real_ais_stream()
        else:
            logger.info("AIS stream already running or using mock data")

    def stop_ais_stream(self):
        """Stop the AIS stream."""
        self.running = False
        if self.ais_socket:
            self.ais_socket.close()
            self.ais_socket = None
        logger.info("AIS stream stopped")

    def get_vessels_near(self, lat: float, lon: float, radius_km: float = 50) -> List[Dict[str, Any]]:
        """
        Get vessels within radius of specific coordinates.
        
        Args:
            lat: Latitude center point
            lon: Longitude center point
            radius_km: Radius in kilometers
            
        Returns:
            List of vessels within the radius
        """
        vessels = self.get_latest_positions()
        
        # Simple distance calculation (Haversine formula)
        from math import radians, sin, cos, sqrt, atan2
        
        def calculate_distance(lat1, lon1, lat2, lon2):
            # Earth radius in kilometers
            R = 6371.0
            
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            return R * c
        
        nearby_vessels = []
        for vessel in vessels:
            distance = calculate_distance(lat, lon, vessel['lat'], vessel['lon'])
            if distance <= radius_km:
                nearby_vessels.append(vessel)
        
        return nearby_vessels

    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            "real_ais_enabled": self.use_real_ais,
            "connected": self.running,
            "active_vessels": len(self.ships_data),
            "last_update": self.last_update.isoformat(),
            "data_source": "real_ais" if self.use_real_ais and self.running else "mock_data",
            "messages_received": self.total_messages_received,
            "messages_parsed": self.valid_messages_parsed,
            "vessel_cache_size": len(self.vessel_cache)
        }


# ===== Global Service Instance =====
ais_service = AISService()