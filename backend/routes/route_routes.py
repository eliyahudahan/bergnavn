# backend/routes/route_routes.py
from flask import Blueprint, request, jsonify, render_template, session
from backend.utils.helpers import get_current_language

# Blueprint for managing routes
routes_bp = Blueprint('routes_bp', __name__)

@routes_bp.route('/')
def view_routes():
    """
    UI Endpoint: Render the routes view template.
    """
    lang = get_current_language()
    
    # Sample routes data for demonstration
    sample_routes = [
        {
            'id': 1,
            'name': 'Bergen to Stavanger',
            'origin': 'Bergen',
            'destination': 'Stavanger', 
            'total_distance_nm': 106.5,
            'duration_days': 0.5,
            'legs': [{'id': 1, 'name': 'Bergen-Haugesund'}, {'id': 2, 'name': 'Haugesund-Stavanger'}],
            'description': 'Coastal route with fjord navigation',
            'status': 'active',
            'created_at': '2024-01-15'
        },
        {
            'id': 2, 
            'name': 'Oslo to Kristiansand',
            'origin': 'Oslo',
            'destination': 'Kristiansand',
            'total_distance_nm': 143.2,
            'duration_days': 0.8,
            'legs': [{'id': 3, 'name': 'Oslo-Larvik'}, {'id': 4, 'name': 'Larvik-Kragerø'}, {'id': 5, 'name': 'Kragerø-Kristiansand'}],
            'description': 'Main south-north corridor',
            'status': 'active',
            'created_at': '2024-01-10'
        },
        {
            'id': 3,
            'name': 'Trondheim to Bodø',
            'origin': 'Trondheim', 
            'destination': 'Bodø',
            'total_distance_nm': 321.7,
            'duration_days': 1.5,
            'legs': [{'id': 6, 'name': 'Trondheim-Rørvik'}, {'id': 7, 'name': 'Rørvik-Sandnessjøen'}, {'id': 8, 'name': 'Sandnessjøen-Bodø'}],
            'description': 'Arctic coastal route',
            'status': 'planning',
            'created_at': '2024-01-05'
        }
    ]
    
    # Calculate statistics
    total_distance = sum(route['total_distance_nm'] for route in sample_routes)
    total_legs = sum(len(route['legs']) for route in sample_routes)
    active_routes = len([r for r in sample_routes if r['status'] == 'active'])
    
    return render_template('routes.html', 
                         routes=sample_routes, 
                         lang=lang,
                         total_distance=total_distance,
                         total_legs=total_legs,
                         active_routes=active_routes)

@routes_bp.route('/api/routes')
def get_routes():
    """
    API Endpoint: Get all routes as JSON
    """
    # Sample data - in production, this would come from database
    routes_data = [
        {
            'id': 1,
            'name': 'Bergen to Stavanger',
            'description': 'Coastal route with fjord navigation',
            'duration_days': 0.5,
            'total_distance_nm': 106.5,
            'origin': 'Bergen',
            'destination': 'Stavanger',
            'status': 'active'
        },
        {
            'id': 2,
            'name': 'Oslo to Kristiansand', 
            'description': 'Main south-north corridor',
            'duration_days': 0.8,
            'total_distance_nm': 143.2,
            'origin': 'Oslo',
            'destination': 'Kristiansand',
            'status': 'active'
        },
        {
            'id': 3,
            'name': 'Trondheim to Bodø',
            'description': 'Arctic coastal route',
            'duration_days': 1.5,
            'total_distance_nm': 321.7,
            'origin': 'Trondheim',
            'destination': 'Bodø',
            'status': 'planning'
        }
    ]
    
    return jsonify(routes_data)

@routes_bp.route('/api/routes/<int:route_id>')
def get_route(route_id):
    """
    API Endpoint: Get specific route by ID
    """
    # Sample route data
    sample_route = {
        'id': route_id,
        'name': f'Route {route_id}',
        'description': f'Detailed information about route {route_id}',
        'duration_days': 1.0,
        'total_distance_nm': 150.0,
        'origin': 'Port A',
        'destination': 'Port B',
        'status': 'active',
        'legs': [
            {'id': 1, 'name': 'Leg 1', 'distance_nm': 50, 'duration_hours': 5},
            {'id': 2, 'name': 'Leg 2', 'distance_nm': 100, 'duration_hours': 10}
        ]
    }
    
    return jsonify(sample_route)

@routes_bp.route('/create', methods=['GET'])
def create_route_form():
    """
    Display form for creating new route
    """
    lang = get_current_language()
    return render_template('create_route.html', lang=lang)

@routes_bp.route('/create', methods=['POST'])
def create_route():
    """
    API Endpoint: Create new route
    """
    data = request.get_json()
    # In production, save to database
    return jsonify({'success': True, 'message': 'Route created', 'route_id': 999})

@routes_bp.route('/list')
def list_routes():
    """
    Alternative routes listing endpoint
    """
    return view_routes()