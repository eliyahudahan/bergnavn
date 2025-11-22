from flask import Blueprint, request, jsonify, render_template
from backend.utils.helpers import get_current_language

# Blueprint for managing routes
routes_bp = Blueprint('routes_bp', __name__)

@routes_bp.route('/routes')
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
            'legs': [{'id': 1}, {'id': 2}],
            'description': 'Coastal route with fjord navigation'
        },
        {
            'id': 2, 
            'name': 'Oslo to Kristiansand',
            'origin': 'Oslo',
            'destination': 'Kristiansand',
            'total_distance_nm': 143.2,
            'duration_days': 0.8,
            'legs': [{'id': 3}, {'id': 4}, {'id': 5}],
            'description': 'Main south-north corridor'
        },
        {
            'id': 3,
            'name': 'Trondheim to Bodø',
            'origin': 'Trondheim', 
            'destination': 'Bodø',
            'total_distance_nm': 321.7,
            'duration_days': 1.5,
            'legs': [{'id': 6}, {'id': 7}, {'id': 8}],
            'description': 'Arctic coastal route'
        }
    ]
    
    # Calculate statistics
    total_distance = sum(route['total_distance_nm'] for route in sample_routes)
    total_legs = sum(len(route['legs']) for route in sample_routes)
    
    return render_template('routes.html', 
                         routes=sample_routes, 
                         lang=lang,
                         total_distance=total_distance,
                         total_legs=total_legs)

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
            'total_distance_nm': 106.5
        },
        {
            'id': 2,
            'name': 'Oslo to Kristiansand', 
            'description': 'Main south-north corridor',
            'duration_days': 0.8,
            'total_distance_nm': 143.2
        }
    ]
    
    return jsonify(routes_data)

# Add this endpoint to fix the missing list_routes
@routes_bp.route('/routes/list')
def list_routes():
    """
    Alternative routes listing endpoint
    """
    return view_routes()