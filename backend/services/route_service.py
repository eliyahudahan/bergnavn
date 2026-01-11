# backend/services/route_service.py
"""
Route Service - Returns empirically verified route counts.
Always shows one true number without duplicates.
"""

import logging
import hashlib
import json
from typing import List, Dict, Set, Tuple

logger = logging.getLogger(__name__)


class RouteFingerprint:
    """Unique fingerprint for route deduplication."""
    
    def __init__(self, route: Dict):
        self.route = route
        self.name = self._normalize_name(route.get('route_name') or route.get('name', ''))
        self.waypoints = route.get('waypoints', [])
        self.source_city = route.get('source_city', '').lower()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize route name for comparison."""
        if not name:
            return ''
        
        normalized = name.upper()
        normalized = normalized.replace('NCA_', '')
        normalized = normalized.replace('_2025', '')
        normalized = normalized.replace('_RTZ', '')
        normalized = normalized.replace('.RTZ', '')
        normalized = normalized.strip('_')
        
        return normalized
    
    @property
    def hash(self) -> str:
        """Generate unique hash for this route."""
        # Create string representation
        content = json.dumps({
            'name': self.name,
            'source_city': self.source_city,
            'waypoint_count': len(self.waypoints),
            'first_last': self._get_first_last_points()
        }, sort_keys=True)
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_first_last_points(self) -> str:
        """Get string representation of first and last waypoints."""
        if not self.waypoints:
            return ''
        
        if len(self.waypoints) == 1:
            wp = self.waypoints[0]
            return f"{wp.get('lat', 0):.4f},{wp.get('lon', 0):.4f}"
        
        first = self.waypoints[0]
        last = self.waypoints[-1]
        return f"{first.get('lat', 0):.4f},{first.get('lon', 0):.4f}|{last.get('lat', 0):.4f},{last.get('lon', 0):.4f}"


class RouteService:
    """
    Service for managing maritime routes with empirical verification.
    """
    
    def __init__(self):
        self._verified_count = None
        self._verified_routes = None
        self._verification_hash = None
    
    def get_all_routes_deduplicated(self) -> List[Dict]:
        """
        Get empirically deduplicated routes.
        
        Returns:
            List of unique route dictionaries
        """
        if self._verified_routes is not None:
            return self._verified_routes
        
        try:
            from backend.services.rtz_parser import discover_rtz_files
            
            # Get all raw routes
            raw_routes = discover_rtz_files(enhanced=False)
            
            if not raw_routes:
                logger.warning("No routes found")
                self._verified_routes = []
                self._verified_count = 0
                return []
            
            # Empirical deduplication
            unique_routes = self._empirical_deduplication(raw_routes)
            
            # Enhance routes for display
            enhanced_routes = [self._enhance_route(route) for route in unique_routes]
            
            # Store for caching
            self._verified_routes = enhanced_routes
            self._verified_count = len(enhanced_routes)
            self._verification_hash = self._calculate_verification_hash(enhanced_routes)
            
            logger.info(f"✅ Empirical route count: {self._verified_count} unique routes")
            
            return enhanced_routes
            
        except ImportError as e:
            logger.error(f"Cannot import rtz_parser: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in get_all_routes_deduplicated: {e}")
            return []
    
    def _empirical_deduplication(self, routes: List[Dict]) -> List[Dict]:
        """Perform empirical deduplication using multiple methods."""
        if not routes:
            return []
        
        # Method 1: Name-based deduplication
        seen_names = set()
        phase1_routes = []
        
        for route in routes:
            fp = RouteFingerprint(route)
            if fp.name and fp.name not in seen_names:
                seen_names.add(fp.name)
                phase1_routes.append(route)
        
        logger.debug(f"Phase 1 (name): {len(routes)} → {len(phase1_routes)}")
        
        # Method 2: Hash-based deduplication
        seen_hashes = set()
        unique_routes = []
        
        for route in phase1_routes:
            fp = RouteFingerprint(route)
            route_hash = fp.hash
            
            if route_hash not in seen_hashes:
                seen_hashes.add(route_hash)
                unique_routes.append(route)
            else:
                logger.debug(f"Duplicate removed: {fp.name}")
        
        logger.debug(f"Phase 2 (hash): {len(phase1_routes)} → {len(unique_routes)}")
        
        return unique_routes
    
    def _enhance_route(self, route: Dict) -> Dict:
        """Enhance route with additional fields for display."""
        enhanced = route.copy()
        
        # Ensure name field
        if 'name' not in enhanced:
            enhanced['name'] = enhanced.get('route_name', 'Unknown Route')
        
        # Clean name for display
        if 'clean_name' not in enhanced:
            raw_name = enhanced.get('route_name') or enhanced.get('name', '')
            clean_name = raw_name.replace('NCA_', '').replace('_2025', '').replace('_', ' ').title()
            enhanced['clean_name'] = clean_name
        
        # Origin and destination
        if 'origin' not in enhanced or enhanced['origin'] == 'Unknown':
            enhanced['origin'] = enhanced.get('source_city', 'Norwegian Coast').title()
        
        if 'destination' not in enhanced or enhanced['destination'] == 'Unknown':
            enhanced['destination'] = 'Norwegian Waters'
        
        # Numeric fields
        if 'total_distance_nm' not in enhanced:
            enhanced['total_distance_nm'] = float(enhanced.get('total_distance', 0) or 0)
        
        if 'waypoint_count' not in enhanced:
            enhanced['waypoint_count'] = len(enhanced.get('waypoints', []))
        
        # Add verification tag
        fp = RouteFingerprint(route)
        enhanced['empirically_verified'] = True
        enhanced['verification_hash'] = fp.hash[:8]
        
        return enhanced
    
    def _calculate_verification_hash(self, routes: List[Dict]) -> str:
        """Calculate verification hash for the entire set."""
        if not routes:
            return hashlib.md5(b'empty').hexdigest()
        
        # Sort routes consistently
        sorted_routes = sorted(routes, key=lambda x: x.get('clean_name', ''))
        
        # Create verification data
        verification_data = []
        for route in sorted_routes:
            verification_data.append({
                'name': route.get('clean_name', ''),
                'hash': route.get('verification_hash', ''),
                'waypoints': route.get('waypoint_count', 0)
            })
        
        return hashlib.sha256(json.dumps(verification_data, sort_keys=True).encode()).hexdigest()
    
    def get_route_statistics(self) -> Dict:
        """
        Get route statistics based on empirical data.
        
        Returns:
            Dictionary with route statistics
        """
        routes = self.get_all_routes_deduplicated()
        
        if not routes:
            return {
                'total_routes': 0,
                'unique_routes': 0,
                'ports_with_routes': 0,
                'total_distance_nm': 0,
                'total_waypoints': 0,
                'empirical_count': 0,
                'verification_hash': self._verification_hash or ''
            }
        
        # Count unique ports/cities
        ports_set = set()
        for route in routes:
            if source_city := route.get('source_city'):
                ports_set.add(source_city.title())
        
        # Calculate totals
        total_distance = sum(float(r.get('total_distance_nm', 0)) for r in routes)
        total_waypoints = sum(r.get('waypoint_count', 0) for r in routes)
        
        return {
            'total_routes': len(routes),
            'unique_routes': len(routes),
            'empirical_count': len(routes),
            'ports_with_routes': len(ports_set),
            'port_list': sorted(list(ports_set)),
            'total_distance_nm': round(total_distance, 1),
            'total_waypoints': total_waypoints,
            'verification_hash': self._verification_hash or '',
            'status': 'empirically_verified'
        }
    
    def get_empirical_count(self) -> Dict:
        """
        Get empirical route count with verification.
        
        Returns:
            Dictionary with empirical count and verification
        """
        routes = self.get_all_routes_deduplicated()
        
        return {
            'empirical_count': len(routes),
            'routes': routes,
            'ports_count': len(set(r.get('source_city', '') for r in routes if r.get('source_city'))),
            'verification_hash': self._verification_hash or '',
            'status': 'verified',
            'methodology': 'empirical_deduplication'
        }
    
    def get_empirical_data(self) -> Dict:
        """
        Get empirical data about route counts.
        """
        try:
            from backend.services.rtz_parser import discover_rtz_files
            
            raw_routes = discover_rtz_files(enhanced=False)
            unique_routes = self.get_all_routes_deduplicated()
            
            return {
                'raw_routes_from_rtz_parser': len(raw_routes),
                'unique_routes_after_deduplication': len(unique_routes),
                'duplicates_removed': len(raw_routes) - len(unique_routes),
                'duplicate_percentage': round((len(raw_routes) - len(unique_routes)) / max(len(raw_routes), 1) * 100, 1)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_duplicates_report(self) -> Dict:
        """
        Get report on duplicate routes found and removed.
        """
        try:
            from backend.services.rtz_parser import discover_rtz_files
            
            raw_routes = discover_rtz_files(enhanced=False)
            unique_routes = self.get_all_routes_deduplicated()
            
            # Count duplicates by source city
            raw_by_city = {}
            unique_by_city = {}
            
            for route in raw_routes:
                city = route.get('source_city', 'unknown')
                raw_by_city[city] = raw_by_city.get(city, 0) + 1
            
            for route in unique_routes:
                city = route.get('source_city', 'unknown')
                unique_by_city[city] = unique_by_city.get(city, 0) + 1
            
            return {
                'raw_count': len(raw_routes),
                'unique_count': len(unique_routes),
                'duplicate_count': len(raw_routes) - len(unique_routes),
                'raw_by_city': raw_by_city,
                'unique_by_city': unique_by_city,
                'duplicates_by_city': {
                    city: raw_by_city.get(city, 0) - unique_by_city.get(city, 0)
                    for city in set(list(raw_by_city.keys()) + list(unique_by_city.keys()))
                }
            }
        except Exception as e:
            return {'error': str(e)}


# Singleton instance
route_service = RouteService()