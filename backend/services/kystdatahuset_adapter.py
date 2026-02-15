"""
Kystdatahuset API Adapter for real-time Norwegian AIS data.
Complete implementation with error handling, caching, and all 10 cities support.
Empirical data source for scientific maritime research.

Uses environment variables from .env file for configuration.
"""

import os
import logging
import requests
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import json
import time

logger = logging.getLogger(__name__)


class KystdatahusetAdapter:
    """
    Complete adapter for Kystdatahuset open Norwegian AIS API.
    Provides empirical vessel data for all 10 Norwegian cities in your project.
    
    Configuration is loaded from environment variables:
    - USE_KYSTDATAHUSET_AIS: Enable/disable this service
    - KYSTDATAHUSET_USER_AGENT: User-Agent string for API requests
    """
    
    BASE_URL = "https://www.kystdatahuset.no/api/v1/ais"
    
    # Your 10 Norwegian cities with accurate coordinates
    # IMPORTANT: Use English names without special characters for API compatibility
    NORWEGIAN_CITIES = {
        'alesund': {'lat': 62.4722, 'lon': 6.1497, 'name': 'Alesund', 'display_name': 'Ålesund', 'region': 'Møre og Romsdal'},
        'andalsnes': {'lat': 62.5675, 'lon': 7.6870, 'name': 'Andalsnes', 'display_name': 'Åndalsnes', 'region': 'Møre og Romsdal'},
        'bergen': {'lat': 60.3913, 'lon': 5.3221, 'name': 'Bergen', 'display_name': 'Bergen', 'region': 'Vestland'},
        'drammen': {'lat': 59.7441, 'lon': 10.2045, 'name': 'Drammen', 'display_name': 'Drammen', 'region': 'Viken'},
        'flekkefjord': {'lat': 58.2970, 'lon': 6.6605, 'name': 'Flekkefjord', 'display_name': 'Flekkefjord', 'region': 'Agder'},
        'kristiansand': {'lat': 58.1467, 'lon': 7.9958, 'name': 'Kristiansand', 'display_name': 'Kristiansand', 'region': 'Agder'},
        'oslo': {'lat': 59.9139, 'lon': 10.7522, 'name': 'Oslo', 'display_name': 'Oslo', 'region': 'Oslo'},
        'sandefjord': {'lat': 59.1312, 'lon': 10.2167, 'name': 'Sandefjord', 'display_name': 'Sandefjord', 'region': 'Vestfold og Telemark'},
        'stavanger': {'lat': 58.9699, 'lon': 5.7331, 'name': 'Stavanger', 'display_name': 'Stavanger', 'region': 'Rogaland'},
        'trondheim': {'lat': 63.4305, 'lon': 10.3951, 'name': 'Trondheim', 'display_name': 'Trondheim', 'region': 'Trøndelag'}
    }
    
    def __init__(self, timeout: int = 15, max_retries: int = 3):
        """
        Initialize the Kystdatahuset adapter.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Check if service is enabled via environment variable
        self.enabled = os.getenv("USE_KYSTDATAHUSET_AIS", "true").lower() == "true"
        
        if not self.enabled:
            logger.warning("⚠️ KystdatahusetAdapter is disabled via USE_KYSTDATAHUSET_AIS environment variable")
            return
        
        # Load User-Agent from .env - using the actual environment variable
        user_agent = os.getenv("KYSTDATAHUSET_USER_AGENT", "").strip()
        
        if not user_agent:
            # Use a browser-like User-Agent to avoid 406 errors
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            logger.info("📝 Using browser-like User-Agent for Kystdatahuset to avoid 406 errors")
        else:
            logger.info(f"📝 Using configured User-Agent: {user_agent[:60]}...")
        
        # Create a session with proper headers for Norwegian API
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9,no;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
        
        # Simple cache to avoid redundant API calls (5 minutes TTL)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes in seconds
        
        # Statistics tracking
        self.request_count = 0
        self.successful_requests = 0
        self.last_request_time = None
        
        logger.info(f"✅ KystdatahusetAdapter initialized for {len(self.NORWEGIAN_CITIES)} Norwegian cities")
        logger.info(f"📡 Service enabled: {self.enabled}")
        logger.info(f"📡 User-Agent configured: {user_agent[:60]}...")
        
        # Test connection on startup
        self._test_initial_connection()
    
    def _test_initial_connection(self):
        """Test API connection on initialization."""
        if not self.enabled:
            return
            
        logger.info("🧪 Testing initial connection to Kystdatahuset API...")
        try:
            # Test with a small Bergen area
            test_bbox = self._create_bounding_box(60.3913, 5.3221, 5)  # 5km around Bergen
            test_response = self.session.get(
                f"{self.BASE_URL}/vessels",
                params={'bbox': test_bbox},
                timeout=10
            )
            
            if test_response.status_code == 200:
                logger.info(f"✅ Initial connection test successful (Status: {test_response.status_code})")
                data = test_response.json()
                logger.info(f"   Found {len(data)} vessels in test area")
            elif test_response.status_code == 406:
                logger.warning(f"⚠️ API returned 406 - Trying alternative endpoint...")
                # Try alternative endpoint format
                alt_response = self.session.get(
                    f"{self.BASE_URL}/positions",
                    params={'bbox': test_bbox},
                    timeout=10
                )
                if alt_response.status_code == 200:
                    logger.info(f"✅ Alternative endpoint /positions works")
            else:
                logger.warning(f"⚠️ API returned status {test_response.status_code}")
                logger.debug(f"   Response: {test_response.text[:200]}")
                
        except Exception as e:
            logger.warning(f"⚠️ Initial connection test failed: {e}")
    
    def get_vessels_near_city(self, city_name: str, radius_km: float = 20) -> List[Dict]:
        """
        Get vessels near a specific Norwegian city.
        
        Args:
            city_name: One of your 10 Norwegian cities (case insensitive)
            radius_km: Search radius in kilometers (default: 20km)
            
        Returns:
            List of vessel data dictionaries
            
        Raises:
            ValueError: If city_name is not in the list of 10 cities
            
        Note: Returns empty list if service is disabled.
        """
        if not self.enabled:
            logger.debug("Kystdatahuset service disabled, returning empty list")
            return []
        
        # Normalize city name - remove special characters for lookup
        city_key = city_name.lower().replace('å', 'a').replace('ø', 'o').replace('æ', 'ae')
        
        # Map common variations
        city_mappings = {
            'alesund': 'alesund',
            'aalesund': 'alesund',
            'andalsnes': 'andalsnes',
            'aandalsnes': 'andalsnes',
            'bergen': 'bergen',
            'drammen': 'drammen',
            'flekkefjord': 'flekkefjord',
            'kristiansand': 'kristiansand',
            'oslo': 'oslo',
            'sandefjord': 'sandefjord',
            'stavanger': 'stavanger',
            'trondheim': 'trondheim'
        }
        
        mapped_city = city_mappings.get(city_key)
        if not mapped_city or mapped_city not in self.NORWEGIAN_CITIES:
            valid_cities = ", ".join(self.NORWEGIAN_CITIES.keys())
            logger.warning(f"Unknown city: '{city_name}'. Valid cities: {valid_cities}")
            return []
        
        city_data = self.NORWEGIAN_CITIES[mapped_city]
        lat, lon = city_data['lat'], city_data['lon']
        
        logger.info(f"🔍 Searching near {city_data['display_name']} ({lat:.4f}, {lon:.4f})")
        
        # Create bounding box for the area around the city
        bbox = self._create_bounding_box(lat, lon, radius_km)
        
        # Get vessels and enrich with city information
        vessels = self._get_vessels_with_retry(bbox)
        enriched_vessels = []
        
        for vessel in vessels:
            enriched = self._enrich_vessel_with_city_data(vessel, mapped_city)
            enriched_vessels.append(enriched)
        
        logger.info(f"📊 Found {len(enriched_vessels)} vessels near {city_data['display_name']} (radius: {radius_km}km)")
        return enriched_vessels
    
    def _get_vessels_with_retry(self, bbox: str) -> List[Dict]:
        """
        Get vessels from API with retry logic for reliability.
        
        Args:
            bbox: Bounding box string "min_lon,min_lat,max_lon,max_lat"
            
        Returns:
            List of vessel data dictionaries
        """
        if not self.enabled:
            return []
        
        # Check cache first
        cache_key = f"bbox_{bbox}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (datetime.now(timezone.utc) - cached_time).seconds < self._cache_ttl:
                logger.debug(f"Using cached data for bbox: {bbox}")
                return cached_data
        
        # Try with retries
        for attempt in range(self.max_retries):
            try:
                self.request_count += 1
                self.last_request_time = datetime.now(timezone.utc)
                
                params = {'bbox': bbox}
                logger.debug(f"📤 Requesting vessels with bbox: {bbox} (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.session.get(
                    f"{self.BASE_URL}/vessels",
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    vessels = response.json()
                    self.successful_requests += 1
                    
                    # Cache the result
                    self._cache[cache_key] = (datetime.now(timezone.utc), vessels)
                    
                    logger.debug(f"✅ API request successful: {len(vessels)} vessels")
                    return vessels
                    
                elif response.status_code == 406:
                    logger.warning(f"⚠️ API returned 406 - Trying alternative endpoint /positions")
                    
                    # Try alternative endpoint
                    alt_response = self.session.get(
                        f"{self.BASE_URL}/positions",
                        params=params,
                        timeout=self.timeout
                    )
                    
                    if alt_response.status_code == 200:
                        vessels = alt_response.json()
                        self.successful_requests += 1
                        self._cache[cache_key] = (datetime.now(timezone.utc), vessels)
                        logger.debug(f"✅ Alternative endpoint successful: {len(vessels)} vessels")
                        return vessels
                    
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logger.warning(f"⚠️ Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                    
                else:
                    logger.warning(f"⚠️ API returned status {response.status_code} (attempt {attempt + 1}/{self.max_retries})")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(1)  # Wait before retry
                        continue
                    else:
                        return []
                        
            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    return []
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Network error: {e} (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    return []
        
        return []
    
    def _create_bounding_box(self, center_lat: float, center_lon: float, radius_km: float) -> str:
        """
        Create a bounding box string for API queries.
        
        Args:
            center_lat: Center latitude in degrees
            center_lon: Center longitude in degrees
            radius_km: Radius from center in kilometers
            
        Returns:
            Bounding box string "min_lon,min_lat,max_lon,max_lat"
        """
        # 1 degree of latitude ≈ 111 km
        lat_delta = radius_km / 111.0
        
        # 1 degree of longitude varies with latitude
        lon_delta = radius_km / (111.0 * abs(math.cos(math.radians(center_lat))))
        
        min_lon = center_lon - lon_delta
        max_lon = center_lon + lon_delta
        min_lat = center_lat - lat_delta
        max_lat = center_lat + lat_delta
        
        # Ensure values are within reasonable bounds for Norway
        min_lat = max(min_lat, 57.0)   # Southern Norway
        max_lat = min(max_lat, 72.0)   # Northern Norway
        min_lon = max(min_lon, 3.0)    # Western Norway
        max_lon = min(max_lon, 32.0)   # Eastern Norway
        
        return f"{min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}"
    
    def _enrich_vessel_with_city_data(self, vessel: Dict, city_key: str) -> Dict:
        """
        Enrich vessel data with city-specific information.
        
        Args:
            vessel: Raw vessel data from API
            city_key: The city key this vessel was found near
            
        Returns:
            Enriched vessel data
        """
        enriched = vessel.copy()
        
        # Add timestamp if not present
        if 'timestamp' not in enriched:
            enriched['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add city information
        city_data = self.NORWEGIAN_CITIES[city_key]
        enriched['nearest_city'] = city_data['display_name']
        enriched['city_region'] = city_data['region']
        enriched['city_key'] = city_key
        
        # Extract standard fields (handle different naming conventions)
        enriched['name'] = vessel.get('name', vessel.get('vessel_name', vessel.get('Name', 'Unknown')))
        enriched['latitude'] = vessel.get('latitude', vessel.get('lat', vessel.get('Lat', 0)))
        enriched['longitude'] = vessel.get('longitude', vessel.get('lon', vessel.get('Lon', 0)))
        enriched['speed'] = vessel.get('speed', vessel.get('SOG', vessel.get('Speed', 0)))
        enriched['course'] = vessel.get('course', vessel.get('COG', vessel.get('Course', 0)))
        enriched['mmsi'] = vessel.get('mmsi', vessel.get('MMSI', ''))
        
        # Calculate distance to city center if we have coordinates
        vessel_lat = enriched['latitude']
        vessel_lon = enriched['longitude']
        
        if vessel_lat and vessel_lon and vessel_lat != 0 and vessel_lon != 0:
            distance = self._calculate_distance_km(
                vessel_lat, vessel_lon,
                city_data['lat'], city_data['lon']
            )
            enriched['distance_to_city_km'] = round(distance, 2)
        
        # Add data source information
        enriched['data_source'] = 'kystdatahuset'
        enriched['source_url'] = self.BASE_URL
        enriched['is_empirical'] = False  # This is real-time data
        enriched['service_enabled'] = self.enabled
        
        return enriched
    
    def _calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates in degrees
            lat2, lon2: Second point coordinates in degrees
            
        Returns:
            Distance in kilometers
        """
        R = 6371.0  # Earth's radius in kilometers
        
        # Convert degrees to radians
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
    
    def get_service_status(self) -> Dict[str, any]:
        """
        Get comprehensive service status and statistics.
        
        Returns:
            Dictionary with service status information
        """
        user_agent = self.session.headers.get('User-Agent', 'Not configured')
        
        status = {
            'service': 'KystdatahusetAdapter',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'enabled': self.enabled,
            'api_endpoint': self.BASE_URL,
            'configuration': {
                'timeout_seconds': self.timeout,
                'max_retries': self.max_retries,
                'user_agent': user_agent[:80] + '...' if len(user_agent) > 80 else user_agent,
                'supported_cities': list(self.NORWEGIAN_CITIES.keys()),
                'city_count': len(self.NORWEGIAN_CITIES),
                'env_use_kystdatahuset': os.getenv("USE_KYSTDATAHUSET_AIS", "Not set"),
                'env_user_agent_set': bool(os.getenv("KYSTDATAHUSET_USER_AGENT", "").strip())
            },
            'request_statistics': {
                'total_requests': self.request_count,
                'successful_requests': self.successful_requests,
                'success_rate': f"{(self.successful_requests/self.request_count*100):.1f}%" if self.request_count > 0 else "0%",
                'last_request': self.last_request_time.isoformat() if self.last_request_time else None
            },
            'cache_statistics': {
                'cache_size': len(self._cache),
                'cache_ttl_seconds': self._cache_ttl
            },
            'data_quality': {
                'source': 'Norwegian Coastal Administration (Kystdatahuset)',
                'data_type': 'Real-time AIS positions',
                'update_frequency': 'Near real-time (1-5 minute delay)',
                'coverage': 'Norwegian territorial waters and EEZ',
                'license': 'Norwegian Open Data License'
            }
        }
        
        # Test current connectivity if enabled
        if self.enabled:
            try:
                test_bbox = self._create_bounding_box(60.3913, 5.3221, 5)  # 5km around Bergen
                test_response = self.session.get(
                    f"{self.BASE_URL}/vessels",
                    params={'bbox': test_bbox},
                    timeout=5
                )
                
                status['connectivity_test'] = {
                    'status': 'success' if test_response.status_code == 200 else 'failed',
                    'status_code': test_response.status_code,
                    'test_area': 'Bergen (5km radius)',
                    'response_time': 'tested'
                }
            except Exception as e:
                status['connectivity_test'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            status['connectivity_test'] = {
                'status': 'disabled',
                'reason': 'Service disabled via USE_KYSTDATAHUSET_AIS'
            }
        
        return status


# Global instance for easy import
kystdatahuset_adapter = KystdatahusetAdapter()