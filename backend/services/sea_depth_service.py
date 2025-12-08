# backend/services/sea_depth_service.py
# English-only comments inside file as requested.
import os
import requests
import time
from functools import lru_cache

# Optional local-file support (GeoTIFF). If rasterio not installed or file missing we skip local.
LOCAL_ETOPo_PATH = os.getenv("LOCAL_ETOP0_PATH", "")  # set to local GeoTIFF path if available
NOAA_IDENTIFY_URL = "https://gis.ngdc.noaa.gov/arcgis/rest/services/etopo1/MapServer/identify"

class SeaDepthService:
    """
    Hybrid sea depth service:
    1) Try local GeoTIFF (fast) if available (requires rasterio)
    2) Else query NOAA ETOPO1 identify endpoint (timeout 2s)
    3) Else use Norway heuristic (lat/lon bands)
    Caching applied via lru_cache for repeated lookups.
    """
    def __init__(self):
        self.local_path = LOCAL_ETOPo_PATH if LOCAL_ETOPo_PATH else None
        self._has_rasterio = False
        try:
            import rasterio  # type: ignore
            self._has_rasterio = True
            self._rasterio = rasterio
        except Exception:
            self._has_rasterio = False

    @lru_cache(maxsize=4096)
    def get_depth(self, lat: float, lon: float) -> dict:
        # Try local GeoTIFF first
        try:
            if self._has_rasterio and self.local_path and os.path.exists(self.local_path):
                val = self._read_local(lat, lon)
                if val is not None:
                    return {"depth_m": val, "source": "local_etopo", "accuracy": "high"}
        except Exception:
            pass
        # Try NOAA identify API with short timeout
        try:
            params = {
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "tolerance": 10,
                "mapExtent": f"{lon},{lat},{lon},{lat}",
                "imageDisplay": "400,300,96",
                "returnGeometry": False,
                "f": "json"
            }
            r = requests.get(NOAA_IDENTIFY_URL, params=params, timeout=2.0)
            if r.status_code == 200:
                j = r.json()
                # try to extract the most relevant value
                # fallback: find 'Grid' value or check attributes
                features = j.get("results") or []
                for feat in features:
                    attrs = feat.get("attributes", {})
                    # common attribute name might be 'ETOPO1' or 'value' — be flexible
                    for key in ("ETOPO1", "value", "GRIDCODE", "elevation", "Z"):
                        if key in attrs:
                            try:
                                return {"depth_m": float(attrs[key]), "source": "noaa_etopo1", "accuracy": "high"}
                            except Exception:
                                continue
            # if NOAA didn't provide, fall through
        except Exception:
            pass
        # Heuristic fallback (Norway-specific lat-depth heuristic)
        depth = self._norway_heuristic(lat, lon)
        return {"depth_m": depth, "source": "norway_heuristic", "accuracy": "medium"}

    def _read_local(self, lat: float, lon: float):
        try:
            # local GeoTIFF read (nearest)
            with self._rasterio.open(self.local_path) as ds:
                rowcol = ds.index(lon, lat)
                val = ds.read(1)[rowcol]
                # ETOPO often stores elevation (land + ice). Depth = negative elevation when below sea level.
                return float(val)
        except Exception:
            return None

    def _norway_heuristic(self, lat: float, lon: float) -> float:
        # Simple empirical bands tuned for Norwegian fjords / seas.
        # Negative values = depth below sea level.
        if 58.0 <= lat <= 60.5 and 4.0 <= lon <= 8.5:
            return -300.0  # typical Bergen fjord deep
        if 59.5 <= lat <= 60.5 and 9.5 <= lon <= 11.5:
            return -40.0   # Oslofjord (shallow)
        if 62.5 <= lat <= 64.0 and 9.0 <= lon <= 11.5:
            return -500.0  # Trondheim fjord deep channel
        if lat >= 65.0:
            return -800.0  # far north deep waters typical
        return -150.0  # default coastal depth
