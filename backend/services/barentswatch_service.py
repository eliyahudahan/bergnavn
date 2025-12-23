"""
BarentsWatch API Service for maritime hazard data.
Fetches and caches aquaculture, cable, and offshore infrastructure data.
"""

import os
import logging
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class BarentsWatchService:
    """
    Service for fetching marine infrastructure data from BarentsWatch API.
    """
    def __init__(self):
        """Initialize service with configuration from environment."""
        # Get credentials from environment
        self.client_id = os.getenv("BARENTSWATCH_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("BARENTSWATCH_CLIENT_SECRET", "").strip()
        
        # Validate credentials
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️ BarentsWatch credentials not found in .env")
            logger.info("Please add to your .env file:")
            logger.info("BARENTSWATCH_CLIENT_ID=your_client_id_here")
            logger.info("BARENTSWATCH_CLIENT_SECRET=your_client_secret_here")
            logger.info("Get credentials from: https://www.barentswatch.no/developer/")
        
        # API endpoints
        self.token_url = "https://id.barentswatch.no/connect/token"
        self.api_base = "https://www.barentswatch.no/bwapi/v2/"
        
        self._access_token = None
        self._token_expiry = None
        
        # Cache directory
        self.cache_dir = Path("backend/assets/barentswatch_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(hours=24)
        
        logger.info(f"✅ BarentsWatch Service initialized. Client ID: {'Configured' if self.client_id else 'NOT configured'}")

    def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth2 access token for BarentsWatch API.
        
        Returns:
            Access token string or None if failed
        """
        # Return cached token if still valid
        if (self._access_token and self._token_expiry and 
            datetime.now() < self._token_expiry):
            logger.debug("Using cached BarentsWatch token")
            return self._access_token
        
        # Check if credentials are configured
        if not self.client_id or not self.client_secret:
            logger.error("❌ BarentsWatch credentials not configured")
            logger.info("Add these to your .env file:")
            logger.info("BARENTSWATCH_CLIENT_ID=your_client_id")
            logger.info("BARENTSWATCH_CLIENT_SECRET=your_client_secret")
            return None
        
        try:
            # Prepare authentication data
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'api'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            logger.info(f"🔑 Requesting token from {self.token_url}")
            
            # Make token request
            response = requests.post(
                self.token_url, 
                data=auth_data, 
                headers=headers, 
                timeout=30
            )
            
            # Handle different response scenarios
            if response.status_code == 400:
                logger.error(f"❌ Bad request (400): {response.text[:200]}")
                logger.info("Possible issues:")
                logger.info("1. Invalid client_id or client_secret")
                logger.info("2. Client not activated in BarentsWatch portal")
                logger.info("3. Incorrect scope parameter")
                return None
            
            elif response.status_code == 401:
                logger.error(f"❌ Unauthorized (401): Check your credentials")
                return None
            
            elif response.status_code == 403:
                logger.error(f"❌ Forbidden (403): No access to API")
                return None
            
            response.raise_for_status()
            
            # Parse token response
            token_data = response.json()
            self._access_token = token_data.get('access_token')
            
            if not self._access_token:
                logger.error("❌ No access_token in response")
                return None
            
            # Calculate token expiry
            expires_in = token_data.get('expires_in', 3600)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
            
            logger.info(f"✅ Successfully obtained BarentsWatch API token (expires in {expires_in}s)")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text[:200]}")
            return None
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response: {e}")
            return None
        
        except Exception as e:
            logger.error(f"❌ Unexpected error getting token: {e}")
            return None

    def _make_api_request(self, endpoint: str) -> List[Dict]:
        """
        Make authenticated request to BarentsWatch API.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            List of data items or empty list on failure
        """
        # Get access token
        token = self._get_access_token()
        if not token:
            logger.warning(f"⚠️ No API token available for {endpoint}")
            return []
        
        # Construct full URL
        url = f"{self.api_base}{endpoint}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        try:
            logger.info(f"🌐 Fetching data from BarentsWatch: {endpoint}")
            
            # Make request with timeout
            response = requests.get(url, headers=headers, timeout=30)
            
            # Handle response
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    logger.info(f"✅ Retrieved {len(data)} items from {endpoint}")
                    return data
                elif isinstance(data, dict):
                    logger.info(f"✅ Retrieved data from {endpoint}")
                    return [data]
                else:
                    logger.warning(f"⚠️ Unexpected data format from {endpoint}")
                    return []
            
            elif response.status_code == 401:
                logger.error(f"❌ Token expired for {endpoint}")
                # Clear token to force refresh
                self._access_token = None
                return []
            
            elif response.status_code == 404:
                logger.warning(f"⚠️ Endpoint not found: {endpoint}")
                return []
            
            else:
                logger.error(f"❌ API request failed: {response.status_code} for {endpoint}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed for {endpoint}: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON from {endpoint}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error for {endpoint}: {e}")
            return []

    def get_aquaculture_facilities(self, bbox: Optional[str] = None) -> List[Dict]:
        """
        Fetch aquaculture (fish farm) locations.
        
        Endpoint: geodata/areas/aquaculture
        
        Args:
            bbox: Optional bounding box filter (not always supported)
            
        Returns:
            List of aquaculture facilities
        """
        # Try real API first
        endpoint = "geodata/areas/aquaculture"
        if bbox:
            endpoint += f"?bbox={bbox}"
        
        data = self._make_api_request(endpoint)
        if data:
            return self._transform_aquaculture_data(data)
        
        # Fallback to sample data
        logger.warning("⚠️ Using sample aquaculture data (API unavailable)")
        return self._get_sample_aquaculture_data()

    def get_subsea_cables(self) -> List[Dict]:
        """
        Fetch submarine cable data.
        
        Endpoint: geodata/infrastructure/cables
        
        Returns:
            List of subsea cables
        """
        # Try real API
        data = self._make_api_request("geodata/infrastructure/cables")
        if data:
            return self._transform_cable_data(data)
        
        # Fallback
        logger.warning("⚠️ Using sample cable data (API unavailable)")
        return self._get_sample_cable_data()

    def get_offshore_installations(self) -> List[Dict]:
        """
        Fetch offshore installations (wind turbines, platforms).
        
        Endpoint: geodata/infrastructure/installations
        
        Returns:
            List of offshore installations
        """
        # Try real API
        data = self._make_api_request("geodata/infrastructure/installations")
        if data:
            return self._transform_installation_data(data)
        
        # Fallback
        logger.warning("⚠️ Using sample installation data (API unavailable)")
        return self._get_sample_installation_data()

    # --- Data Transformation Methods ---
    
    def _transform_aquaculture_data(self, data: List[Dict]) -> List[Dict]:
        """Transform aquaculture API response to standard format."""
        transformed = []
        for item in data:
            # Handle different possible response formats
            if isinstance(item, dict):
                transformed.append({
                    'id': item.get('id', str(hash(str(item)))),
                    'name': item.get('name', 'Aquaculture Facility'),
                    'type': 'aquaculture',
                    'latitude': item.get('latitude') or item.get('lat') or item.get('y') or 60.0,
                    'longitude': item.get('longitude') or item.get('lon') or item.get('x') or 5.0,
                    'owner': item.get('owner', 'Unknown'),
                    'size_hectares': item.get('size', item.get('area', 0)),
                    'status': item.get('status', 'active'),
                    'source': 'BarentsWatch API'
                })
        return transformed

    def _transform_cable_data(self, data: List[Dict]) -> List[Dict]:
        """Transform cable API response to standard format."""
        transformed = []
        for item in data:
            if isinstance(item, dict):
                # Try to extract coordinates
                lat = item.get('latitude') or item.get('lat') or item.get('y')
                lon = item.get('longitude') or item.get('lon') or item.get('x')
                
                if lat is not None and lon is not None:
                    transformed.append({
                        'id': item.get('id', str(hash(str(item)))),
                        'name': item.get('name', 'Subsea Cable'),
                        'type': 'cable',
                        'latitude': float(lat),
                        'longitude': float(lon),
                        'voltage': item.get('voltage', 'Unknown'),
                        'owner': item.get('owner', 'Unknown'),
                        'status': item.get('status', 'active'),
                        'source': 'BarentsWatch API'
                    })
        return transformed

    def _transform_installation_data(self, data: List[Dict]) -> List[Dict]:
        """Transform installation API response to standard format."""
        transformed = []
        for item in data:
            if isinstance(item, dict):
                transformed.append({
                    'id': item.get('id', str(hash(str(item)))),
                    'name': item.get('name', 'Offshore Installation'),
                    'type': item.get('type', item.get('installation_type', 'platform')),
                    'latitude': item.get('latitude') or item.get('lat') or item.get('y') or 60.0,
                    'longitude': item.get('longitude') or item.get('lon') or item.get('x') or 5.0,
                    'owner': item.get('owner', 'Unknown'),
                    'status': item.get('status', 'active'),
                    'height_m': item.get('height', item.get('height_m', 0)),
                    'source': 'BarentsWatch API'
                })
        return transformed

    # --- Sample Data for Testing ---
    
    def _get_sample_aquaculture_data(self) -> List[Dict]:
        """Sample aquaculture data for testing when API fails."""
        return [
            {
                'id': 'aq-001',
                'name': 'Bergen Fish Farm',
                'type': 'aquaculture',
                'latitude': 60.391,
                'longitude': 5.310,
                'owner': 'Norwegian Seafood Co.',
                'size_hectares': 15.5,
                'status': 'active',
                'source': 'Sample Data'
            },
            {
                'id': 'aq-002',
                'name': 'Fjord Aquaculture',
                'type': 'aquaculture',
                'latitude': 60.405,
                'longitude': 5.295,
                'owner': 'Fjord Fisheries',
                'size_hectares': 22.0,
                'status': 'active',
                'source': 'Sample Data'
            }
        ]

    def _get_sample_cable_data(self) -> List[Dict]:
        """Sample cable data for testing when API fails."""
        return [
            {
                'id': 'cable-001',
                'name': 'North Sea Power Cable',
                'type': 'cable',
                'latitude': 60.398,
                'longitude': 5.320,
                'voltage': '132 kV',
                'owner': 'Statnett',
                'status': 'active',
                'source': 'Sample Data'
            }
        ]

    def _get_sample_installation_data(self) -> List[Dict]:
        """Sample installation data for testing when API fails."""
        return [
            {
                'id': 'inst-001',
                'name': 'Statfjord Platform',
                'type': 'platform',
                'latitude': 61.200,
                'longitude': 1.850,
                'owner': 'Equinor',
                'status': 'active',
                'height_m': 250,
                'source': 'Sample Data'
            },
            {
                'id': 'inst-002',
                'name': 'Hywind Tampen',
                'type': 'wind_turbine',
                'latitude': 60.850,
                'longitude': 3.150,
                'owner': 'Equinor',
                'status': 'active',
                'height_m': 180,
                'source': 'Sample Data'
            }
        ]

    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        token_valid = bool(self._access_token and self._token_expiry and 
                          datetime.now() < self._token_expiry)
        
        return {
            'configured': bool(self.client_id and self.client_secret),
            'token_valid': token_valid,
            'last_token_refresh': self._token_expiry.isoformat() if self._token_expiry else None,
            'data_available': {
                'aquaculture': len(self.get_aquaculture_facilities()) > 0,
                'cables': len(self.get_subsea_cables()) > 0,
                'installations': len(self.get_offshore_installations()) > 0
            },
            'credentials_status': '✅ Configured' if self.client_id else '❌ Missing'
        }


# Global instance
barentswatch_service = BarentsWatchService()