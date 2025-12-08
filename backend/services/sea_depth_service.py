# backend/services/sea_depth_service.py
# English-only comments inside file.
from math import hypot
from datetime import datetime

# Empirical depth profiles for the 10 cities (meters, negative = depth)
# These are conservative representative values (not exact bathymetry).
_DEPTH_PROFILES = {
    "bergen": {"typical_depth_m": -300, "band": "deep_fjord"},
    "oslo": {"typical_depth_m": -40, "band": "shallow_fjord"},
    "stavanger": {"typical_depth_m": -150, "band": "fjord_coastal"},
    "trondheim": {"typical_depth_m": -400, "band": "deep_fjord"},
    "kristiansand": {"typical_depth_m": -60, "band": "coastal"},
    "alesund": {"typical_depth_m": -250, "band": "fjord_deep"},
    "drammen": {"typical_depth_m": -30, "band": "sheltered_fjord"},
    "sandefjord": {"typical_depth_m": -50, "band": "coastal"},
    "flekkefjord": {"typical_depth_m": -70, "band": "coastal"},
    "andalsnes": {"typical_depth_m": -220, "band": "fjord_deep"}
}

_CITY_COORDS = {
    "bergen": (60.39, 5.32),
    "oslo": (59.91, 10.75),
    "stavanger": (58.97, 5.73),
    "trondheim": (63.43, 10.40),
    "kristiansand": (58.15, 8.00),
    "alesund": (62.47, 6.15),
    "drammen": (59.74, 10.20),
    "sandefjord": (59.13, 10.22),
    "flekkefjord": (58.26, 6.66),
    "andalsnes": (62.57, 7.69)
}

def _nearest_city(lat, lon):
    best = None
    best_dist = 1e9
    for c, (clat, clon) in _CITY_COORDS.items():
        d = hypot(lat - clat, lon - clon)
        if d < best_dist:
            best = c
            best_dist = d
    return best, best_dist

class SeaDepthService:
    """Empirical sea depth service for project cities."""
    def __init__(self):
        pass

    def get_best_sea_depth(self, lat, lon):
        """
        Return dict:
        {
           "depth_m": -300,
           "source": "empirical_city_profile",
           "city": "bergen",
           "timestamp": "...",
           "confidence": "medium"
        }
        """
        city, dist = _nearest_city(lat, lon)
        profile = _DEPTH_PROFILES.get(city, {"typical_depth_m": -150})
        depth = profile["typical_depth_m"]
        # Simple distance adjustment: closer to city => more typical; further => move toward open sea depth
        if dist > 1.0:
            # small gradient: add deeper factor proportional to distance (heuristic)
            depth = int(depth - (dist * 30))  # deeper further offshore
        return {
            "depth_m": depth,
            "source": "empirical_city_profile",
            "city": city,
            "distance_to_city_deg": round(dist, 4),
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": "medium"
        }
