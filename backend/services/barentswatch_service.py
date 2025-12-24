"""
BarentsWatch API Service for maritime hazard data.
Fetches and caches aquaculture, cable, and offshore infrastructure data.
Uses the official, current BarentsWatch API endpoints and OAuth2 authentication.
"""

import os
import logging
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import re
import time
import hashlib

logger = logging.getLogger(__name__)


class BarentswatchService:
    """
    Service for fetching marine infrastructure data from BarentsWatch API.
    Uses the official and current API endpoints as per developer.barentswatch.no.
    """
    
    def __init__(self):
        """Initialize service with configuration from environment."""
        # Get credentials and token from environment
        self.client_id = os.getenv("BARENTSWATCH_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("BARENTSWATCH_CLIENT_SECRET", "").strip()
        
        # Remove quotes if they exist in the credentials
        if self.client_id.startswith('"') and self.client_id.endswith('"'):
            self.client_id = self.client_id[1:-1]
        if self.client_secret.startswith('"') and self.client_secret.endswith('"'):
            self.client_secret = self.client_secret[1:-1]
        
        # Validate credentials
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️ BarentsWatch credentials not found in .env")
            logger.info("Please add to your .env file WITHOUT quotes:")
            logger.info('BARENTSWATCH_CLIENT_ID=your_actual_client_id')
            logger.info('BARENTSWATCH_CLIENT_SECRET=your_actual_client_secret')
            logger.info("Get credentials from: https://www.barentswatch.no/developer/")
        else:
            logger.info(f"✅ BarentsWatch credentials loaded: {self.client_id[:20]}...")
        
        # API endpoints - OFFICIAL and CURRENT based on BarentsWatch Developer Portal
        # Source: https://developer.barentswatch.no/docs/intro
        self.token_url = "https://id.barentswatch.no/connect/token"
        self.api_base = "https://www.barentswatch.no/bwapi/"  # Current base URL
        
        # CORRECTED ENDPOINTS - Based on BarentsWatch API documentation
        # The previous endpoints were incorrect. These are the correct ones:
        self.endpoints = {
            'aquaculture': 'v1/geodata/download/aquaculture',
            'cables': 'v1/geodata/download/cables',  # Note: changed from 'energy/cable'
            'installations': 'v1/geodata/download/installations'  # Note: changed from 'industry/industry'
        }
        
        # Alternative endpoints to try if the above don't work
        self.alternative_endpoints = {
            'aquaculture': 'v2/geodata/download/aquaculture',
            'cables': 'v2/geodata/download/cables',
            'installations': 'v2/geodata/download/installations'
        }
        
        # Path to .env file
        self.env_file_path = Path(".env")
        
        # Initialize token variables
        self._access_token = ""
        self._refresh_token = ""
        self._token_expiry = None
        
        # Load existing token from .env on startup
        self._load_token_from_env()
        
        # Cache directory for hazard data
        self.cache_dir = Path("backend/assets/barentswatch_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(hours=24)
        
        # Request configuration
        self.request_timeout = 30
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        logger.info(f"✅ Barentswatch Service initialized with OFFICIAL endpoints")
        logger.info(f"   API Base: {self.api_base}")
        logger.info(f"   Endpoints configured: {list(self.endpoints.keys())}")
        logger.info(f"   Cache directory: {self.cache_dir}")
    
    def _load_token_from_env(self):
        """Load access token and expiry from .env file on startup."""
        self._access_token = os.getenv("BARENTSWATCH_ACCESS_TOKEN", "").strip()
        
        # Remove quotes if present
        if self._access_token.startswith('"') and self._access_token.endswith('"'):
            self._access_token = self._access_token[1:-1]
        
        # Load refresh token
        self._refresh_token = os.getenv("BARENTSWATCH_REFRESH_TOKEN", "").strip()
        if self._refresh_token.startswith('"') and self._refresh_token.endswith('"'):
            self._refresh_token = self._refresh_token[1:-1]
        
        # Try to parse token expiry
        expires_str = os.getenv("BARENTSWATCH_TOKEN_EXPIRES", "").strip()
        if expires_str:
            try:
                expires_int = int(expires_str)
                if expires_int > 1000000000:  # Likely a Unix timestamp
                    self._token_expiry = datetime.fromtimestamp(expires_int)
                else:  # Likely seconds remaining from now
                    self._token_expiry = datetime.now() + timedelta(seconds=expires_int)
            except ValueError:
                logger.warning(f"⚠️ Invalid token expiry format: {expires_str}")
                self._token_expiry = None
        else:
            self._token_expiry = None
        
        if self._access_token:
            expiry_status = self._token_expiry.isoformat() if self._token_expiry else 'Unknown'
            logger.info(f"📁 Token loaded from .env, expires at: {expiry_status}")
    
    def _update_env_file(self, access_token: str, refresh_token: str, expires_in: int):
        """
        Update the .env file with new tokens.
        This ensures tokens persist across application restarts.
        """
        try:
            if not self.env_file_path.exists():
                logger.warning(f".env file not found at {self.env_file_path}")
                return
            
            # Read current .env content
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Calculate expiry timestamp
            expiry_timestamp = int((datetime.now() + timedelta(seconds=expires_in)).timestamp())
            
            # Update or add tokens in content
            updates = {
                'BARENTSWATCH_ACCESS_TOKEN': access_token,
                'BARENTSWATCH_REFRESH_TOKEN': refresh_token,
                'BARENTSWATCH_TOKEN_EXPIRES': str(expiry_timestamp)
            }
            
            for key, value in updates.items():
                # Pattern to find existing variable
                pattern = rf'^{key}=.*$'
                new_line = f'{key}="{value}"'
                
                if re.search(pattern, content, re.MULTILINE):
                    # Replace existing line
                    content = re.sub(pattern, new_line, content, flags=re.MULTILINE)
                else:
                    # Add new line at the end
                    content += f'\n{new_line}'
            
            # Write back to .env
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update instance variables
            self._access_token = access_token
            self._refresh_token = refresh_token
            self._token_expiry = datetime.fromtimestamp(expiry_timestamp)
            
            logger.info(f"✅ Updated .env file with new tokens (expires in {expires_in}s)")
            
        except Exception as e:
            logger.error(f"❌ Failed to update .env file: {e}")
            # Still update instance variables even if file write fails
            self._access_token = access_token
            self._refresh_token = refresh_token
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
    
    def _request_new_token_pair(self) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """
        Request a new pair of access and refresh tokens from BarentsWatch OAuth2 endpoint.
        Uses the correct OAuth2 flow as per BarentsWatch documentation.
        
        Returns:
            Tuple of (access_token, refresh_token, expires_in) or (None, None, None) on failure
        """
        if not self.client_id or not self.client_secret:
            logger.error("❌ Cannot request token: client credentials not configured")
            return None, None, None
        
        try:
            # Use the correct scope as per BarentsWatch Power BI guide
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'api'  # Correct scope for BarentsWatch API
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            logger.info(f"🔑 Requesting token from {self.token_url}")
            
            response = requests.post(
                self.token_url, 
                data=auth_data, 
                headers=headers, 
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token', '')
                expires_in = token_data.get('expires_in', 3600)
                
                if access_token:
                    logger.info(f"✅ Successfully obtained token (expires in {expires_in}s)")
                    return access_token, refresh_token, expires_in
                else:
                    logger.error("❌ Token response missing access_token")
                    return None, None, None
            
            else:
                logger.error(f"❌ Token request failed: {response.status_code} - {response.text[:200]}")
                return None, None, None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Token request failed: {e}")
            return None, None, None
        except Exception as e:
            logger.error(f"❌ Unexpected error requesting token: {e}")
            return None, None, None
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get valid access token with automatic refresh logic.
        Returns None if unable to get valid token.
        """
        # Check if we have a valid token (with 5-minute buffer)
        if self._access_token and self._token_expiry:
            time_remaining = (self._token_expiry - datetime.now()).total_seconds()
            
            if time_remaining > 300:  # More than 5 minutes remaining
                logger.debug(f"Using valid access token ({int(time_remaining)}s remaining)")
                return self._access_token
        
        # Token expired or not available - request new token pair
        logger.info("Access token expired or not available, requesting new token")
        
        # Request a new token pair
        access_token, refresh_token, expires_in = self._request_new_token_pair()
        
        if access_token:
            # Update .env file with new tokens
            self._update_env_file(access_token, refresh_token, expires_in)
            return access_token
        
        # All authentication attempts failed
        logger.error("❌ All authentication attempts failed")
        return None
    
    def _get_cached_data(self, endpoint_type: str, bbox: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Get cached data if available and not expired.
        Returns None if no cache or cache expired.
        """
        try:
            # Create cache filename based on endpoint and bbox
            cache_key = endpoint_type
            if bbox:
                cache_key += f"_{hashlib.md5(bbox.encode()).hexdigest()[:8]}"
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if not cache_file.exists():
                return None
            
            # Check if cache is expired
            file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - file_mtime > self.cache_duration:
                logger.debug(f"Cache expired for {endpoint_type}")
                return None
            
            # Load cached data
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded {len(data)} items from cache for {endpoint_type}")
            return data
            
        except Exception as e:
            logger.warning(f"Failed to load cache for {endpoint_type}: {e}")
            return None
    
    def _save_to_cache(self, endpoint_type: str, data: List[Dict], bbox: Optional[str] = None):
        """
        Save data to cache file.
        """
        try:
            # Create cache filename based on endpoint and bbox
            cache_key = endpoint_type
            if bbox:
                cache_key += f"_{hashlib.md5(bbox.encode()).hexdigest()[:8]}"
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            # Save data to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved {len(data)} items to cache for {endpoint_type}")
            
        except Exception as e:
            logger.warning(f"Failed to save cache for {endpoint_type}: {e}")
    
    def _make_api_request(self, endpoint_type: str, bbox: Optional[str] = None, use_cache: bool = True) -> List[Dict]:
        """
        Make authenticated request to BarentsWatch API using OFFICIAL endpoints.
        Implements caching and retry logic.
        
        Args:
            endpoint_type: Type of data ('aquaculture', 'cables', 'installations')
            bbox: Optional bounding box filter
            use_cache: Whether to use cached data if available
            
        Returns:
            List of data items or empty list on failure
        """
        # Check cache first
        if use_cache:
            cached_data = self._get_cached_data(endpoint_type, bbox)
            if cached_data is not None:
                logger.info(f"📁 Using cached data for {endpoint_type} ({len(cached_data)} items)")
                return cached_data
        
        # Get access token
        token = self._get_access_token()
        if not token:
            logger.warning(f"⚠️ No API token available for {endpoint_type}")
            return []
        
        # Try different endpoint versions
        endpoints_to_try = [
            self.endpoints.get(endpoint_type),
            self.alternative_endpoints.get(endpoint_type)
        ]
        
        # Also try some common variations
        if endpoint_type == 'cables':
            endpoints_to_try.extend(['v1/geodata/download/energy/cables', 'v1/geodata/download/energy/cable'])
        elif endpoint_type == 'installations':
            endpoints_to_try.extend(['v1/geodata/download/industry', 'v1/geodata/download/offshore'])
        
        for endpoint in endpoints_to_try:
            if not endpoint:
                continue
            
            # Construct full URL with optional bbox parameter
            url = f"{self.api_base}{endpoint}"
            if bbox:
                url += f"?bbox={bbox}"
            else:
                # Add format parameter for JSON response
                url += "?format=json"
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Retry logic
            for attempt in range(self.max_retries):
                try:
                    if attempt > 0:
                        logger.info(f"Retry {attempt}/{self.max_retries} for {endpoint_type}")
                        time.sleep(self.retry_delay * attempt)
                    
                    logger.info(f"🌐 Trying endpoint: {url}")
                    
                    # Make request with timeout
                    response = requests.get(url, headers=headers, timeout=self.request_timeout)
                    
                    # Handle response
                    if response.status_code == 200:
                        data = response.json()
                        
                        if isinstance(data, list):
                            logger.info(f"✅ Successfully retrieved {len(data)} {endpoint_type} items from {endpoint}")
                            # Save to cache
                            self._save_to_cache(endpoint_type, data, bbox)
                            return data
                        elif isinstance(data, dict):
                            logger.info(f"✅ Successfully retrieved {endpoint_type} data from {endpoint}")
                            result = [data]
                            self._save_to_cache(endpoint_type, result, bbox)
                            return result
                        else:
                            logger.warning(f"⚠️ Unexpected data format for {endpoint_type} from {endpoint}: {type(data)}")
                            continue
                    
                    elif response.status_code == 401:
                        logger.warning(f"⚠️ Token expired for {endpoint_type}")
                        # Clear token to force refresh on next request
                        self._access_token = None
                        # Get new token and retry
                        token = self._get_access_token()
                        if token:
                            headers['Authorization'] = f'Bearer {token}'
                            continue
                        else:
                            return []
                    
                    elif response.status_code == 404:
                        logger.debug(f"Endpoint not found (404): {endpoint}")
                        break  # Try next endpoint
                    
                    else:
                        logger.debug(f"API request failed: {response.status_code} for {endpoint}")
                        if attempt < self.max_retries - 1:
                            continue
                        break  # Try next endpoint
                        
                except requests.exceptions.Timeout:
                    logger.debug(f"Request timeout for {endpoint_type} at {endpoint}")
                    if attempt < self.max_retries - 1:
                        continue
                    break
                    
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Request failed for {endpoint_type} at {endpoint}: {e}")
                    if attempt < self.max_retries - 1:
                        continue
                    break
                    
                except json.JSONDecodeError as e:
                    logger.debug(f"Invalid JSON for {endpoint_type} at {endpoint}: {e}")
                    break
        
        # If we get here, all endpoints failed
        logger.warning(f"❌ All endpoints failed for {endpoint_type}")
        return []
    
    def get_aquaculture_facilities(self, bbox: Optional[str] = None, use_cache: bool = True) -> List[Dict]:
        """
        Fetch aquaculture (fish farm) locations from BarentsWatch API.
        This uses the official aquaculture endpoint for open data.
        
        Args:
            bbox: Optional bounding box filter (e.g., "4.5,58.5,5.5,59.5")
            use_cache: Whether to use cached data
            
        Returns:
            List of aquaculture facilities
        """
        logger.info("Fetching aquaculture data from BarentsWatch API")
        data = self._make_api_request('aquaculture', bbox, use_cache)
        
        if data:
            transformed = self._transform_aquaculture_data(data)
            logger.info(f"✅ Successfully loaded {len(transformed)} aquaculture facilities from API")
            return transformed
        
        logger.warning("⚠️ API request failed or returned empty data for aquaculture")
        return []
    
    def get_subsea_cables(self, use_cache: bool = True) -> List[Dict]:
        """
        Fetch submarine cable data from BarentsWatch API.
        Uses the official energy/cable endpoint.
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            List of subsea cables
        """
        logger.info("Fetching subsea cable data from BarentsWatch API")
        data = self._make_api_request('cables', None, use_cache)
        
        if data:
            transformed = self._transform_cable_data(data)
            logger.info(f"✅ Successfully loaded {len(transformed)} subsea cables from API")
            return transformed
        
        logger.warning("⚠️ API request failed or returned empty data for cables")
        return []
    
    def get_offshore_installations(self, use_cache: bool = True) -> List[Dict]:
        """
        Fetch offshore installations (wind turbines, platforms) from BarentsWatch API.
        Uses the official industry/industry endpoint.
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            List of offshore installations
        """
        logger.info("Fetching offshore installation data from BarentsWatch API")
        data = self._make_api_request('installations', None, use_cache)
        
        if data:
            transformed = self._transform_installation_data(data)
            logger.info(f"✅ Successfully loaded {len(transformed)} offshore installations from API")
            return transformed
        
        logger.warning("⚠️ API request failed or returned empty data for installations")
        return []
    
    # --- Data Transformation Methods ---
    
    def _transform_aquaculture_data(self, data: List[Dict]) -> List[Dict]:
        """Transform aquaculture API response to standard format."""
        transformed = []
        for item in data:
            if isinstance(item, dict):
                # Handle various API response formats
                # Extract coordinates - API returns geojson format
                lat, lon = self._extract_coordinates_from_geojson(item)
                
                if lat is not None and lon is not None:
                    transformed.append({
                        'id': item.get('id', item.get('objectId', str(hash(json.dumps(item, sort_keys=True))))),
                        'name': item.get('name', item.get('navn', 'Aquaculture Facility')),
                        'type': 'aquaculture',
                        'latitude': float(lat),
                        'longitude': float(lon),
                        'owner': item.get('owner', item.get('eier', 'Unknown')),
                        'size_hectares': float(item.get('size', item.get('area', item.get('storrelse', 0)))),
                        'status': item.get('status', 'active'),
                        'source': 'Barentswatch API',
                        'data_quality': 'high',
                        'last_updated': datetime.now().isoformat()
                    })
        return transformed
    
    def _transform_cable_data(self, data: List[Dict]) -> List[Dict]:
        """Transform cable API response to standard format."""
        transformed = []
        for item in data:
            if isinstance(item, dict):
                lat, lon = self._extract_coordinates_from_geojson(item)
                
                if lat is not None and lon is not None:
                    transformed.append({
                        'id': item.get('id', item.get('objectId', str(hash(json.dumps(item, sort_keys=True))))),
                        'name': item.get('name', item.get('navn', 'Subsea Cable')),
                        'type': 'cable',
                        'latitude': float(lat),
                        'longitude': float(lon),
                        'voltage': item.get('voltage', item.get('spenning', 'Unknown')),
                        'owner': item.get('owner', item.get('eier', 'Unknown')),
                        'status': item.get('status', 'active'),
                        'source': 'Barentswatch API',
                        'data_quality': 'high',
                        'last_updated': datetime.now().isoformat()
                    })
        return transformed
    
    def _transform_installation_data(self, data: List[Dict]) -> List[Dict]:
        """Transform installation API response to standard format."""
        transformed = []
        for item in data:
            if isinstance(item, dict):
                lat, lon = self._extract_coordinates_from_geojson(item)
                
                if lat is not None and lon is not None:
                    transformed.append({
                        'id': item.get('id', item.get('objectId', str(hash(json.dumps(item, sort_keys=True))))),
                        'name': item.get('name', item.get('navn', 'Offshore Installation')),
                        'type': item.get('type', item.get('installation_type', 'platform')),
                        'latitude': float(lat),
                        'longitude': float(lon),
                        'owner': item.get('owner', item.get('eier', 'Unknown')),
                        'status': item.get('status', 'active'),
                        'height_m': float(item.get('height', item.get('height_m', item.get('hoyde', 0)))),
                        'source': 'Barentswatch API',
                        'data_quality': 'high',
                        'last_updated': datetime.now().isoformat()
                    })
        return transformed
    
    def _extract_coordinates_from_geojson(self, item: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Extract coordinates from GeoJSON geometry."""
        try:
            # Check for geometry field
            if 'geometry' in item and isinstance(item['geometry'], dict):
                geom_type = item['geometry'].get('type', '')
                coordinates = item['geometry'].get('coordinates', [])
                
                if geom_type == 'Point' and len(coordinates) >= 2:
                    # GeoJSON format is [longitude, latitude]
                    lon, lat = coordinates[0], coordinates[1]
                    return float(lat), float(lon)
                
                elif geom_type == 'Polygon' and coordinates:
                    # Use centroid of polygon (first ring)
                    polygon_coords = coordinates[0]
                    if len(polygon_coords) > 0:
                        lats = [float(p[1]) for p in polygon_coords]
                        lons = [float(p[0]) for p in polygon_coords]
                        return sum(lats)/len(lats), sum(lons)/len(lons)
                
                elif geom_type == 'MultiPoint' and coordinates:
                    # Use first point
                    if len(coordinates) > 0 and len(coordinates[0]) >= 2:
                        lon, lat = coordinates[0][0], coordinates[0][1]
                        return float(lat), float(lon)
                        
                elif geom_type == 'LineString' and coordinates:
                    # Use midpoint of line
                    if len(coordinates) > 0 and len(coordinates[0]) >= 2:
                        mid_idx = len(coordinates) // 2
                        lon, lat = coordinates[mid_idx][0], coordinates[mid_idx][1]
                        return float(lat), float(lon)
        except Exception as e:
            logger.debug(f"Error extracting coordinates from GeoJSON: {e}")
        
        # Fallback to direct fields
        try:
            lat = item.get('latitude', item.get('lat', None))
            lon = item.get('longitude', item.get('lon', None))
            
            if lat is not None and lon is not None:
                return float(lat), float(lon)
        except (ValueError, TypeError):
            pass
        
        # Try alternative field names
        try:
            lat = item.get('y', item.get('Y', None))
            lon = item.get('x', item.get('X', None))
            
            if lat is not None and lon is not None:
                return float(lat), float(lon)
        except (ValueError, TypeError):
            pass
        
        return None, None
    
    def clear_cache(self, endpoint_type: Optional[str] = None):
        """
        Clear cache for specific endpoint type or all cache.
        
        Args:
            endpoint_type: Optional endpoint type to clear ('aquaculture', 'cables', 'installations')
                         If None, clears all cache.
        """
        try:
            if endpoint_type:
                pattern = f"{endpoint_type}*.json"
                files = list(self.cache_dir.glob(pattern))
            else:
                files = list(self.cache_dir.glob("*.json"))
            
            for file in files:
                file.unlink()
            
            logger.info(f"🧹 Cleared cache: {len(files)} files")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status with detailed information."""
        # Check token validity
        token_valid = False
        time_remaining = 0
        
        if self._access_token and self._token_expiry:
            time_remaining = (self._token_expiry - datetime.now()).total_seconds()
            token_valid = time_remaining > 0
        
        # Test API connectivity
        api_test_results = {}
        for endpoint_type in ['aquaculture', 'cables', 'installations']:
            endpoint = self.endpoints.get(endpoint_type)
            api_test_results[endpoint_type] = {
                'endpoint': endpoint,
                'configured': bool(endpoint),
                'full_url': f"{self.api_base}{endpoint}" if endpoint else None
            }
        
        # Check cache status
        cache_files = list(self.cache_dir.glob("*.json"))
        cache_info = {}
        for file in cache_files:
            file_mtime = datetime.fromtimestamp(file.stat().st_mtime)
            age_hours = (datetime.now() - file_mtime).total_seconds() / 3600
            cache_info[file.name] = {
                'size_kb': file.stat().st_size / 1024,
                'age_hours': round(age_hours, 2),
                'is_fresh': age_hours < self.cache_duration.total_seconds() / 3600
            }
        
        status = {
            'service': 'BarentswatchService',
            'configured': bool(self.client_id and self.client_secret),
            'token_valid': token_valid,
            'time_until_expiry_seconds': int(time_remaining) if token_valid else 0,
            'api_base': self.api_base,
            'endpoints_configured': api_test_results,
            'cache': {
                'directory': str(self.cache_dir),
                'duration_hours': self.cache_duration.total_seconds() / 3600,
                'files_count': len(cache_files),
                'files': cache_info
            },
            'data_available': {
                'aquaculture': len(self.get_aquaculture_facilities(use_cache=True)) > 0,
                'cables': len(self.get_subsea_cables(use_cache=True)) > 0,
                'installations': len(self.get_offshore_installations(use_cache=True)) > 0
            },
            'data_sources': {
                'primary': 'BarentsWatch API',
                'api_documentation': 'https://developer.barentswatch.no/docs/intro',
                'open_data_portal': 'https://www.barentswatch.no/en/articles/open-data-via-barentswatch/'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if self._token_expiry:
            status['token_expiry_time'] = self._token_expiry.isoformat()
        
        return status
    
    def refresh_all_data(self) -> Dict[str, Any]:
        """
        Force refresh of all data by clearing cache and fetching fresh data.
        Returns summary of refreshed data.
        """
        logger.info("🔄 Force refreshing all data from BarentsWatch API")
        
        # Clear all cache
        self.clear_cache()
        
        # Fetch fresh data
        results = {
            'aquaculture': self.get_aquaculture_facilities(use_cache=False),
            'cables': self.get_subsea_cables(use_cache=False),
            'installations': self.get_offshore_installations(use_cache=False),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add counts
        results['counts'] = {
            'aquaculture': len(results['aquaculture']),
            'cables': len(results['cables']),
            'installations': len(results['installations']),
            'total': len(results['aquaculture']) + len(results['cables']) + len(results['installations'])
        }
        
        logger.info(f"✅ Refreshed all data: {results['counts']['total']} total items")
        return results
    
    def test_endpoints(self) -> Dict[str, Any]:
        """
        Test all endpoints to find which ones work.
        Returns detailed results for each endpoint.
        """
        logger.info("🧪 Testing all API endpoints")
        
        results = {}
        token = self._get_access_token()
        
        if not token:
            return {'error': 'No valid token available'}
        
        # List of endpoints to test based on BarentsWatch documentation
        test_endpoints = [
            # Standard endpoints
            'v1/geodata/download/aquaculture',
            'v1/geodata/download/cables',
            'v1/geodata/download/installations',
            
            # Alternative endpoints
            'v2/geodata/download/aquaculture',
            'v2/geodata/download/cables',
            'v2/geodata/download/installations',
            
            # Industry/energy specific
            'v1/geodata/download/industry',
            'v1/geodata/download/energy',
            'v1/geodata/download/offshore',
            
            # Full paths
            'v1/geodata/download/aquaculture/aquaculturefarm',
            'v1/geodata/download/energy/cable',
            'v1/geodata/download/industry/industry',
        ]
        
        for endpoint in test_endpoints:
            url = f"{self.api_base}{endpoint}?format=json"
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                results[endpoint] = {
                    'status_code': response.status_code,
                    'url': url,
                    'success': response.status_code == 200,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.text) if response.text else 0
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            results[endpoint]['item_count'] = len(data)
                        elif isinstance(data, dict):
                            results[endpoint]['item_count'] = 1
                    except:
                        results[endpoint]['item_count'] = 'N/A'
                
                logger.debug(f"Tested {endpoint}: {response.status_code}")
                
            except Exception as e:
                results[endpoint] = {
                    'error': str(e),
                    'url': url,
                    'success': False
                }
        
        # Find working endpoints
        working_endpoints = {k: v for k, v in results.items() if v.get('success')}
        
        logger.info(f"✅ Endpoint test complete. Found {len(working_endpoints)} working endpoints")
        
        return {
            'all_results': results,
            'working_endpoints': working_endpoints,
            'summary': {
                'total_tested': len(test_endpoints),
                'working': len(working_endpoints),
                'failed': len(test_endpoints) - len(working_endpoints)
            }
        }


# Global instance for easy import
barentswatch_service = BarentswatchService()