"""
Controller for managing routes, route legs, waypoints, and hazard zones.
All business logic is delegated to route_service.
"""

from flask import Blueprint, request, jsonify
from backend.services.route_service import RouteService

route_bp = Blueprint('route_bp', __name__, url_prefix='/routes')

# Initialize the service
route_service = RouteService()

@route_bp.route('/upload', methods=['POST'])
def upload_route_file():
    """
    Upload a new RTZ file and create base routes.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    try:
        route_service.process_rtz_file(file)
        return jsonify({'message': 'RTZ file processed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@route_bp.route('/base_routes', methods=['GET'])
def list_base_routes():
    """
    List all base routes.
    """
    routes = route_service.get_all_base_routes()
    return jsonify(routes), 200

@route_bp.route('/base_routes/<int:route_id>', methods=['GET'])
def get_base_route(route_id):
    """
    Get a single base route with its legs and waypoints.
    """
    route = route_service.get_base_route_with_details(route_id)
    if not route:
        return jsonify({'error': 'Route not found'}), 404
    return jsonify(route), 200
