# backend/routes/route_routes.py
"""
Routes Blueprint - displays NCA RTZ routes from Norwegian Coastal Administration.
Uses RouteService for empirical verification.
"""

from flask import Blueprint, request, jsonify, render_template, session, current_app
from backend.utils.helpers import get_current_language
from backend.services.route_service import route_service
from datetime import datetime
import logging

# Blueprint for managing routes
routes_bp = Blueprint('routes_bp', __name__)
logger = logging.getLogger(__name__)


@routes_bp.route('/')
def view_routes():
    """
    UI Endpoint: Render the routes view template with empirically verified routes.
    """
    lang = get_current_language()
    
    try:
        # Get empirically verified routes
        empirical_data = route_service.get_empirical_count()
        
        routes = empirical_data.get('routes', [])
        route_count = empirical_data.get('empirical_count', 0)
        
        # Get statistics
        stats = route_service.get_route_statistics()
        
        # Extract unique cities for port status grid
        cities_with_routes = set()
        for route in routes:
            if source_city := route.get('source_city'):
                cities_with_routes.add(source_city.title())
        
        # Calculate display values
        total_distance = stats.get('total_distance_nm', 0)
        waypoint_count = stats.get('total_waypoints', 0)
        active_ports_count = stats.get('ports_with_routes', 0)
        
        logger.info(f"📊 routes.html: Showing {route_count} empirically verified routes")
        
    except Exception as e:
        logger.error(f"Error in view_routes: {e}", exc_info=True)
        # Fallback to empty data
        routes = []
        route_count = 0
        total_distance = 0
        waypoint_count = 0
        cities_with_routes = []
        active_ports_count = 0
        stats = {'message': 'Error loading routes'}
    
    return render_template('routes.html', 
                         routes=routes, 
                         lang=lang,
                         route_count=route_count,
                         total_distance=total_distance,
                         waypoint_count=waypoint_count,
                         cities_with_routes=sorted(list(cities_with_routes)),
                         active_ports_count=active_ports_count,
                         stats=stats,
                         timestamp=datetime.now().strftime('%H:%M %d/%m/%Y'))


@routes_bp.route('/api/routes')
def get_routes():
    """
    API Endpoint: Get all routes as JSON with empirical verification.
    """
    try:
        empirical_data = route_service.get_empirical_count()
        
        return jsonify({
            'success': True,
            'empirical_count': empirical_data.get('empirical_count', 0),
            'routes': empirical_data.get('routes', []),
            'message': f'Found {empirical_data.get("empirical_count", 0)} empirically verified routes'
        })
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'routes': [],
            'count': 0
        }), 500


@routes_bp.route('/api/routes/empirical-data')
def get_empirical_route_data():
    """
    API Endpoint: Get empirical data about route counts.
    """
    try:
        empirical = route_service.get_empirical_data()
        duplicates = route_service.get_duplicates_report()
        
        return jsonify({
            'success': True,
            'empirical_data': empirical,
            'duplicates_report': duplicates,
            'message': 'Empirical route data'
        })
        
    except Exception as e:
        logger.error(f"Error in empirical data API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@routes_bp.route('/api/routes/statistics')
def get_route_statistics():
    """
    API Endpoint: Get route statistics.
    """
    try:
        stats = route_service.get_route_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'message': f'Route statistics for {stats.get("empirical_count", 0)} verified routes'
        })
        
    except Exception as e:
        logger.error(f"Statistics API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@routes_bp.route('/api/routes/scan-rtz')
def scan_rtz_files():
    """
    API Endpoint: Scan for RTZ files and return discovered routes.
    """
    try:
        from backend.services.rtz_parser import discover_rtz_files
        
        raw_routes = discover_rtz_files(enhanced=False)
        empirical_data = route_service.get_empirical_count()
        
        return jsonify({
            'scan_time': datetime.now().isoformat(),
            'raw_routes_found': len(raw_routes),
            'empirical_count': empirical_data.get('empirical_count', 0),
            'duplicates_removed': len(raw_routes) - empirical_data.get('empirical_count', 0),
            'message': f'Empirical verification: {empirical_data.get("empirical_count", 0)} unique routes'
        })
        
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/debug/empirical-test')
def empirical_test():
    """
    Debug endpoint for empirical testing.
    """
    try:
        from backend.services.rtz_parser import discover_rtz_files
        
        raw_routes = discover_rtz_files(enhanced=False)
        empirical_data = route_service.get_empirical_count()
        
        # Count by city
        raw_by_city = {}
        empirical_by_city = {}
        
        for route in raw_routes:
            city = route.get('source_city', 'unknown')
            raw_by_city[city] = raw_by_city.get(city, 0) + 1
        
        for route in empirical_data.get('routes', []):
            city = route.get('source_city', 'unknown')
            empirical_by_city[city] = empirical_by_city.get(city, 0) + 1
        
        return jsonify({
            'success': True,
            'empirical_verification': {
                'raw_routes': len(raw_routes),
                'empirical_count': empirical_data.get('empirical_count', 0),
                'duplicates_removed': len(raw_routes) - empirical_data.get('empirical_count', 0)
            },
            'raw_by_city': raw_by_city,
            'empirical_by_city': empirical_by_city,
            'message': 'Empirical verification test results'
        })
        
    except Exception as e:
        logger.error(f"Empirical test error: {e}")
        return jsonify({'error': str(e)}), 500


# שמור את שאר הפונקציות כפי שהיו
@routes_bp.route('/create', methods=['GET'])
def create_route_form():
    """Display form for creating new route."""
    lang = get_current_language()
    return render_template('create_route.html', lang=lang)


@routes_bp.route('/create', methods=['POST'])
def create_route():
    """API Endpoint: Create new route."""
    data = request.get_json()
    return jsonify({'success': True, 'message': 'Route created', 'route_id': 999})


@routes_bp.route('/list')
def list_routes():
    """Alternative routes listing endpoint."""
    return view_routes()