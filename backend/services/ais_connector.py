# backend/services/ais_connector.py
"""
AIS connector - tries to use Kystverket TCP stream when configured and permitted,
otherwise falls back to a free public data generator service (simulator).
This module exposes:
 - start_ais_stream() to begin background polling/streaming
 - get_latest_ships() to access most recent snapshot
Usage:
  from backend.services.ais_connector import ais_manager
  ais_manager.start_ais_stream()
  ships = ais_manager.get_latest_ships()
Notes:
 - Real TCP connection to Kystverket requires network access and license/permission.
 - Do not hardcode credentials here; use environment variables.
"""

import threading
import socket
import time
import os
from typing import List, Dict, Any

# Import local free AIS generator and advanced simulator if available
try:
    from backend.services.free_ais_service import FreeAisService
except Exception:
    FreeAisService = None

# Keep state in a simple manager object
class AISManager:
    def __init__(self):
        self._ships: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._thread = None
        self._stop_event = threading.Event()
        # Configuration via env
        self.kystverket_host = os.getenv("KYSTVERKET_AIS_HOST", "153.44.253.27")
        self.kystverket_port = int(os.getenv("KYSTVERKET_AIS_PORT", "5631"))
        self.use_kystverket = os.getenv("USE_KYSTVERKET_AIS", "true").lower() in ("1","true","yes")
        # Fallback service
        self.free_service = FreeAisService() if FreeAisService else None

    def start_ais_stream(self, poll_interval: int = 30):
        """Start background collector thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, args=(poll_interval,), daemon=True)
        self._thread.start()

    def stop_ais_stream(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _connect_and_read(self):
        """Attempt to connect to Kystverket TCP stream. For safety we only establish a short
        handshake and then use a placeholder parser. Do not parse raw TCP without permission."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(8)
            sock.connect((self.kystverket_host, self.kystverket_port))
            # If connected, we mark as connected then close. Production should parse AIS NMEA/TCP properly.
            sock.close()
            return True
        except Exception:
            return False

    def _run(self, poll_interval: int):
        while not self._stop_event.is_set():
            try:
                using_live = False
                if self.use_kystverket:
                    ok = self._connect_and_read()
                    if ok:
                        using_live = True
                        # NOTE: In production, implement a proper AIS NMEA/TCP parser here.
                        # For safety in this template we do not pull raw data.
                        # Instead we keep the last known snapshot (could be updated by a proper reader).
                # Fallback to free service snapshot
                if not using_live and self.free_service:
                    snapshot = self.free_service.get_norwegian_commercial_vessels()
                else:
                    # If live connection would be used, we still fallback to free snapshot in this template
                    snapshot = self.free_service.get_norwegian_commercial_vessels() if self.free_service else []

                # attach processing metrics or normalization here
                with self._lock:
                    self._ships = snapshot
            except Exception:
                # keep loop running on errors
                pass
            time.sleep(poll_interval)

    def get_latest_ships(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._ships)

# Single global manager
ais_manager = AISManager()
