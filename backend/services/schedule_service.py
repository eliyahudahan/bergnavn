# backend/services/schedule_service.py
"""
Schedule service using Entur (Norwegian public transport API) for ferry/timetables.
Entur offers free APIs for Norwegian public transport (includes some ferry services).
This module:
 - query_stop_departures(stop_id) -> list
 - search_routes(origin, destination, datetime) -> list (uses journey planner)
ENV:
 - ENTUR_API_KEY optional (some endpoints can be used without key for small usage)
Notes:
 - Entur API follows SIRI/Netex concepts. Check entur.no developer docs for details.
"""

import os
import requests
from typing import Any, Dict, List, Optional

ENTUR_BASE = "https://api.entur.io"  # public gateway
ENTUR_KEY = os.getenv("ENTUR_API_KEY", "")

HEADERS = {"Content-Type": "application/json"}
if ENTUR_KEY:
    HEADERS["ET-Client-Name"] = ENTUR_KEY

def get_stop_departures(stop_id: str) -> List[Dict[str, Any]]:
    """Get upcoming departures for a stop_place (may include ferries if available)."""
    url = f"{ENTUR_BASE}/departure-board/v1/departureBoard?id={stop_id}"
    r = requests.get(url, headers=HEADERS, timeout=8)
    if r.status_code == 200:
        return r.json().get("data", {}).get("estimatedCalls", [])
    return []

def journey_search(origin: str, destination: str, departure_time: Optional[str] = None) -> List[Dict[str, Any]]:
    """Simple wrapper for the journey planner; origin/destination can be coordinates or stop ids."""
    url = f"{ENTUR_BASE}/journey-planner/v3/graphql"
    # Minimal GraphQL payload (Entur uses GraphQL for journey planner in some gateways)
    query = """
    query Plan($from:PlaceRef, $to:PlaceRef) {
      plan(from: $from, to: $to) {
        itineraries {
          duration
          legs {
            mode
            from { name }
            to { name }
            departure
            arrival
          }
        }
      }
    }
    """
    variables = {"from": {"id": origin}, "to": {"id": destination}}
    r = requests.post(url, json={"query": query, "variables": variables}, headers=HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json().get("data", {}).get("plan", {}).get("itineraries", [])
    return []
