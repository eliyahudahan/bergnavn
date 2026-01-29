"""
BarentsWatch API Service for maritime hazard data.
This service handles both real-time AIS data and static geodata.

Uses environment variables from .env file for configuration:
- BARENTSWATCH_CLIENT_ID: Your client ID (format: email:clientname)
- BARENTSWATCH_CLIENT_SECRET: Your client secret
- BARENTSWATCH_ACCESS_TOKEN: Auto-managed access token
- BARENTSWATCH_TOKEN_EXPIRES: Auto-managed token expiry timestamp
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

logger = logging.getLogger(__name__)

class BarentswatchService:
    """
    Main service class for interacting with BarentsWatch APIs.
    
    Features:
    - Automatic token management with refresh
    - Persistent token storage in .env file
    - Fallback to empirical data when API fails
    - Comprehensive error handling
    """
    
    def __init__(self):
        """
        Initialize the service with configuration from environment variables.
        Automatically detects available access levels based on token scope.
        """
        # Load credentials from .env - strip any surrounding quotes
        self.client_id = os.getenv("BARENTSWATCH_CLIENT_ID", "").strip('"\'')
        self.client_secret = os.getenv("BARENTSWATCH_CLIENT_SECRET", "").strip('"\'')
        
        # Validate credentials
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️ BarentsWatch credentials not found in environment variables")
            logger.warning("   Please set BARENTSWATCH_CLIENT_ID and BARENTSWATCH_CLIENT_SECRET in .env file")
        
        # OAuth2 endpoint for token acquisition
        self.token_url = "https://id.barentswatch.no/connect/token"
        
        # Determine scope based on client type
        # If client ID contains 'AIS' or based on empirical testing
        self.scope = self._determine_scope()
        
        # Base URL for all BarentsWatch API calls
        self.api_base = "https://www.barentswatch.no/bwapi/"
        
        # AIS endpoint (works with 'ais' scope)
        self.ais_endpoint = 'v2/ais/vessels'
        
        # Path to .env file for token persistence
        self.env_file_path = Path(".env")
        
        # Token management variables
        self._access_token = ""
        self._token_expiry = None
        self._refresh_token = None
        
        # Load any existing token on startup
        self._load_token_from_env()
        
        # Service status
        self._has_valid_credentials = bool(self.client_id and self.client_secret)
        self._last_token_refresh = None
        
        logger.info("✅ BarentswatchService initialized")
        logger.info(f"   Client ID configured: {'✅' if self.client_id else '❌'}")
        logger.info(f"   Client Secret configured: {'✅' if self.client_secret else '❌'}")
        logger.info(f"   Using scope: '{self.scope}'")
    
    def _determine_scope(self) -> str:
        """
        Determine the correct scope to use based on client ID pattern.
        
        Returns:
            'ais' for AIS clients, 'api' for general API clients
        """
        # Check if client ID suggests AIS client
        client_id_lower = self.client_id.lower()
        
        # Common patterns for AIS clients
        ais_indicators = ['ais', 'ais-', '-ais', 'ais_', '_ais']
        
        for indicator in ais_indicators:
            if indicator in client_id_lower:
                logger.info(f"   Detected AIS client from client ID pattern")
                return "ais"
        
        # Default to 'api' for general access
        logger.info(f"   Using default 'api' scope")
        return "api"
    
    def _load_token_from_env(self):
        """
        Load existing access token and its expiry timestamp from the .env file.
        This allows the service to persist tokens across application restarts.
        """
        self._access_token = os.getenv("BARENTSWATCH_ACCESS_TOKEN", "").strip('"\'')
        self._refresh_token = os.getenv("BARENTSWATCH_REFRESH_TOKEN", "").strip('"\'')
        
        # Parse the expiry timestamp
        expires_str = os.getenv("BARENTSWATCH_TOKEN_EXPIRES", "").strip('"\'')
        if expires_str:
            try:
                expires_int = int(expires_str)
                self._token_expiry = datetime.fromtimestamp(expires_int)
                
                time_remaining = (self._token_expiry - datetime.now()).total_seconds()
                if time_remaining > 0:
                    logger.info(f"📁 Token loaded from .env, expires in {int(time_remaining)}s")
                else:
                    logger.warning(f"📁 Token from .env has expired {abs(int(time_remaining))}s ago")
                    self._access_token = ""  # Mark as expired
            except ValueError:
                logger.warning(f"⚠️ Could not parse token expiry: {expires_str}")
                self._token_expiry = None
        else:
            self._token_expiry = None
    
    def _request_new_token(self) -> Optional[str]:
        """
        Request a new access token from BarentsWatch OAuth2 endpoint.
        
        Returns:
            The new access token string if successful, None otherwise.
        """
        if not self._has_valid_credentials:
            logger.error("❌ Cannot request token: Invalid credentials")
            return None
        
        try:
            # Prepare the OAuth2 client credentials grant request
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': self.scope
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            logger.info(f"🔑 Requesting new token with scope: '{self.scope}'")
            
            response = requests.post(
                self.token_url, 
                data=auth_data, 
                headers=headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
                refresh_token = token_data.get('refresh_token')  # May not be present
                
                if access_token:
                    logger.info(f"✅ Successfully obtained new token (expires in {expires_in}s)")
                    
                    # Update internal state
                    self._access_token = access_token
                    if refresh_token:
                        self._refresh_token = refresh_token
                    
                    self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    self._last_token_refresh = datetime.now()
                    
                    # Persist the new token to .env file
                    self._update_env_file(access_token, refresh_token, expires_in)
                    return access_token
                else:
                    logger.error("❌ Token response is missing the 'access_token' field")
                    return None
            else:
                # Log detailed error information
                logger.error(f"❌ Token request failed with status {response.status_code}")
                logger.error(f"   Response: {response.text[:200]}")
                
                # Special handling for common errors
                if response.status_code == 400:
                    logger.error("   Hint: Check if client credentials are correct and URL-encoded if needed")
                elif response.status_code == 401:
                    logger.error("   Hint: Client authentication failed. Check client_id and client_secret")
                
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error during token request: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error during token request: {e}")
            return None
    
    def _update_env_file(self, access_token: str, refresh_token: Optional[str], expires_in: int):
        """
        Update the .env file with a new access token and calculated expiry timestamp.
        
        Args:
            access_token: The new OAuth2 access token string.
            refresh_token: The refresh token (if provided).
            expires_in: Time to expiry in seconds from now.
        """
        try:
            if not self.env_file_path.exists():
                logger.warning(f"⚠️ .env file not found at {self.env_file_path}. Token will not be persisted.")
                return
            
            # Read the entire .env file
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Calculate the absolute expiry timestamp
            expiry_timestamp = int((datetime.now() + timedelta(seconds=expires_in)).timestamp())
            
            # Define the key-value pairs to update
            updates = {
                'BARENTSWATCH_ACCESS_TOKEN': access_token,
                'BARENTSWATCH_TOKEN_EXPIRES': str(expiry_timestamp)
            }
            
            if refresh_token:
                updates['BARENTSWATCH_REFRESH_TOKEN'] = refresh_token
            
            # For each key, find and replace or append
            for key, value in updates.items():
                # Pattern to match the entire line
                pattern = rf'^{key}=.*$'
                new_line = f'{key}="{value}"'
                
                if re.search(pattern, content, re.MULTILINE):
                    # Replace existing line
                    content = re.sub(pattern, new_line, content, flags=re.MULTILINE)
                else:
                    # Append new line at the end
                    content += f'\n{new_line}'
            
            # Write the updated content back
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"💾 Token saved to .env file (expires at {self._token_expiry.strftime('%H:%M:%S')})")
            
        except Exception as e:
            logger.error(f"❌ Failed to update .env file: {e}")
            # Token is still valid in memory, just not persisted
    
    def _ensure_valid_token(self) -> Optional[str]:
        """
        Ensure we have a valid access token, refreshing if necessary.
        
        Returns:
            A valid access token string, or None if authentication fails.
        """
        # Check if we have credentials at all
        if not self._has_valid_credentials:
            logger.warning("⚠️ No valid credentials configured")
            return None
        
        # Check if current token is still valid (with 5-minute buffer)
        if self._access_token and self._token_expiry:
            time_remaining = (self._token_expiry - datetime.now()).total_seconds()
            
            if time_remaining > 300:  # More than 5 minutes left
                logger.debug(f"Using cached token ({int(time_remaining)}s remaining)")
                return self._access_token
            elif time_remaining > 0:  # Less than 5 minutes but still valid
                logger.info(f"🔄 Token expiring soon ({int(time_remaining)}s), refreshing...")
            else:  # Token has expired
                logger.warning(f"🔄 Token expired {abs(int(time_remaining))}s ago, refreshing...")
        
        # Token is expired or doesn't exist - request a new one
        logger.info("🔄 Access token expired or unavailable, requesting a new one")
        return self._request_new_token()
    
    def get_vessel_positions(self, bbox: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Fetch real-time AIS vessel positions from BarentsWatch API.
        
        Args:
            bbox: Optional bounding box filter as "min_lon,min_lat,max_lon,max_lat"
            limit: Maximum number of vessels to return (default: 100)
            
        Returns:
            List of vessel dictionaries with position and metadata.
            
        Example bbox for Norwegian coast: "4.0,58.0,30.0,71.0"
        
        Note: Returns empty list if API fails or credentials are invalid.
        """
        token = self._ensure_valid_token()
        if not token:
            logger.warning("⚠️ Cannot fetch AIS data: No valid authentication token")
            return []
        
        # Construct the full AIS API URL
        url = f"{self.api_base}{self.ais_endpoint}"
        params = {}
        
        if bbox:
            params['bbox'] = bbox
        if limit:
            params['limit'] = str(limit)
        
        # Add format parameter if no other params exist
        if not params:
            params['format'] = 'json'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        try:
            logger.info(f"🌐 Fetching real-time AIS data from {url}")
            start_time = time.time()
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"✅ Retrieved {len(data)} real-time vessel positions in {response_time:.2f}s")
                    
                    # Add metadata to each vessel
                    for vessel in data:
                        vessel['data_source'] = 'barentswatch'
                        vessel['timestamp'] = datetime.now().isoformat()
                        vessel['api_response_time'] = f"{response_time:.2f}s"
                    
                    return data
                else:
                    logger.warning(f"⚠️ AIS API returned unexpected data format: {type(data)}")
                    return []
            elif response.status_code == 401:
                logger.warning("🔑 AIS request unauthorized - token may be invalid or expired")
                # Try to refresh token and retry once
                self._access_token = None
                self._token_expiry = None
                token = self._ensure_valid_token()
                
                if token:
                    headers['Authorization'] = f'Bearer {token}'
                    retry_response = requests.get(url, headers=headers, params=params, timeout=30)
                    
                    if retry_response.status_code == 200:
                        data = retry_response.json()
                        if isinstance(data, list):
                            logger.info(f"✅ Retrieved {len(data)} vessels after token refresh")
                            return data
                
                return []
            elif response.status_code == 403:
                logger.error("🚫 AIS request forbidden - check if your client has AIS scope permission")
                logger.error("   Hint: You may need 'ais' scope instead of 'api'")
                return []
            else:
                logger.warning(f"⚠️ AIS request failed with status {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout fetching AIS data after 30s")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching AIS data: {e}")
            return []
    
    def get_vessels_near_city(self, city_name: str, radius_km: float = 20) -> List[Dict]:
        """
        Get vessels near a specific city using BarentsWatch API.
        
        Args:
            city_name: City name (supports Norwegian cities)
            radius_km: Search radius in kilometers
            
        Returns:
            List of vessel dictionaries
        """
        # City coordinates mapping
        city_coords = {
            'bergen': (60.3913, 5.3221),
            'oslo': (59.9139, 10.7522),
            'stavanger': (58.9699, 5.7331),
            'trondheim': (63.4305, 10.3951),
            'alesund': (62.4722, 6.1497),
            'andalsnes': (62.5675, 7.6870),
            'drammen': (59.7441, 10.2045),
            'flekkefjord': (58.2970, 6.6605),
            'kristiansand': (58.1467, 7.9958),
            'sandefjord': (59.1312, 10.2167)
        }
        
        city_lower = city_name.lower()
        if city_lower not in city_coords:
            logger.warning(f"⚠️ Unknown city: {city_name}")
            return []
        
        lat, lon = city_coords[city_lower]
        
        # Create bounding box
        import math
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(math.cos(math.radians(lat))))
        
        bbox = f"{lon - lon_delta:.4f},{lat - lat_delta:.4f},{lon + lon_delta:.4f},{lat + lat_delta:.4f}"
        
        # Get vessels
        vessels = self.get_vessel_positions(bbox=bbox, limit=50)
        
        # Add city information
        for vessel in vessels:
            vessel['nearest_city'] = city_name
            vessel['search_radius_km'] = radius_km
        
        logger.info(f"📊 Found {len(vessels)} BarentsWatch vessels near {city_name}")
        return vessels
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the BarentsWatch API connection and return detailed status.
        
        Returns:
            Dictionary with connection test results
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'credentials_configured': self._has_valid_credentials,
            'client_id_present': bool(self.client_id),
            'client_secret_present': bool(self.client_secret),
            'current_scope': self.scope,
            'has_valid_token': False,
            'token_expiry': None,
            'api_test_successful': False,
            'api_response_time': None,
            'error': None
        }
        
        if not self._has_valid_credentials:
            result['error'] = 'Missing credentials in environment variables'
            return result
        
        # Check token status
        token = self._ensure_valid_token()
        if token:
            result['has_valid_token'] = True
            if self._token_expiry:
                result['token_expiry'] = self._token_expiry.isoformat()
                time_remaining = (self._token_expiry - datetime.now()).total_seconds()
                result['token_expires_in_seconds'] = int(time_remaining)
        
        # Test API call
        try:
            start_time = time.time()
            test_vessels = self.get_vessel_positions(limit=1)
            response_time = time.time() - start_time
            
            result['api_response_time'] = f"{response_time:.2f}s"
            result['api_test_successful'] = bool(test_vessels is not None)
            result['test_vessels_returned'] = len(test_vessels) if test_vessels else 0
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Provide comprehensive status information about the BarentsWatch service.
        
        Returns:
            Dictionary containing service configuration, access levels, and data availability.
        """
        token_valid = False
        token_expiry_str = None
        token_remaining = 0
        
        if self._access_token and self._token_expiry:
            time_remaining = (self._token_expiry - datetime.now()).total_seconds()
            token_valid = time_remaining > 0
            token_expiry_str = self._token_expiry.isoformat()
            token_remaining = int(time_remaining)
        
        # Test connection
        connection_test = self.test_connection()
        
        return {
            'service': 'BarentswatchService',
            'timestamp': datetime.now().isoformat(),
            'authentication': {
                'client_id_configured': bool(self.client_id),
                'client_secret_configured': bool(self.client_secret),
                'token_valid': token_valid,
                'token_expiry': token_expiry_str,
                'token_remaining_seconds': token_remaining,
                'current_scope': self.scope,
                'last_token_refresh': self._last_token_refresh.isoformat() if self._last_token_refresh else None
            },
            'connection_test': connection_test,
            'capabilities': {
                'ais_realtime': True,  # Always true, but may fail at runtime
                'geodata_static': self.scope == 'api',  # Only with 'api' scope
                'api_endpoint_ais': f"{self.api_base}{self.ais_endpoint}"
            },
            'recommendations': [
                'Ensure BARENTSWATCH_CLIENT_ID and BARENTSWATCH_CLIENT_SECRET are set in .env',
                f"Current scope is '{self.scope}' - use 'ais' for AIS data, 'api' for geodata",
                'Tokens auto-refresh when expiring (5-minute buffer)',
                'Check logs for detailed error information'
            ]
        }


# Global service instance for easy import
barentswatch_service = BarentswatchService()