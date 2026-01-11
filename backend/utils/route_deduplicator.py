"""
Simple deduplication for maritime routes
Only fixes the counting issue - doesn't change database
"""

import hashlib
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)


def generate_route_hash(route: Dict) -> str:
    """
    Generate unique hash for a route
    Based on origin, destination, and waypoints
    """
    # Use what we have
    origin = route.get('origin', '') or route.get('source_city', '')
    destination = route.get('destination', '')
    name = route.get('name', '') or route.get('route_name', '')
    
    # Create unique string
    unique_string = f"{origin}|{destination}|{name}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:10]


def deduplicate_routes(routes: List[Dict]) -> List[Dict]:
    """
    Remove duplicate routes - SIMPLE VERSION
    Just for counting correctly
    """
    if not routes:
        return []
    
    seen_hashes = set()
    unique_routes = []
    
    for route in routes:
        route_hash = generate_route_hash(route)
        
        if route_hash not in seen_hashes:
            seen_hashes.add(route_hash)
            unique_routes.append(route)
        else:
            logger.debug(f"Removed duplicate: {route.get('name', 'Unknown')}")
    
    logger.info(f"Deduplication: {len(routes)} → {len(unique_routes)} routes")
    return unique_routes


def get_route_count_report(routes: List[Dict]) -> Dict:
    """
    Report on route counts before/after deduplication
    """
    unique_count = len(deduplicate_routes(routes))
    
    # Group by source
    sources = {}
    for route in routes:
        source = route.get('data_source', 'unknown') or route.get('source_type', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    return {
        'total_before_dedup': len(routes),
        'unique_after_dedup': unique_count,
        'duplicates_removed': len(routes) - unique_count,
        'sources': sources,
        'recommendation': f'Display {unique_count} routes (not {len(routes)})'
    }