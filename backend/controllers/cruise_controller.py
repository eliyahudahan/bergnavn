"""
Controller for managing cruises.
Delegates all business logic to CruiseService.
Provides RESTful endpoints for CRUD operations and rendering pages.
"""

from flask import Blueprint, request, jsonify, render_template
from backend.services.cruise_service import CruiseService
from backend.models.cruise import Cruise
from backend.utils.helpers import get_current_language

# Blueprint for cruise routes
cruise_bp = Blueprint('cruise', __name__, url_prefix='/cruises')

# Initialize the Cruise service
cruise_service = CruiseService()


@cruise_bp.route('/', methods=['POST'])
def create_cruise():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    try:
        cruise_service.create_cruise(data)
        return jsonify({'message': 'Cruise created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@cruise_bp.route('/', methods=['GET'])
def get_all_cruises():
    try:
        cruises_data = cruise_service.get_all_cruises()
        return jsonify(cruises_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@cruise_bp.route('/view', methods=['GET'])
def view_cruises():
    """
    Renders cruises.html template with all cruises.
    Ensures each cruise object has attributes accessed by Jinja.
    """
    try:
        lang = get_current_language()
        cruises = Cruise.query.all()  # returns SQLAlchemy objects

        # Optionally, convert to list of dicts if needed:
        cruises_list = [
            {
                "title": c.title,
                "description": c.description,
                "departure_date": c.departure_date,
                "return_date": c.return_date,
                "price": c.price
            } for c in cruises
        ]

        return render_template('cruises.html', cruises=cruises_list, lang=lang)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cruise_bp.route('/<int:cruise_id>', methods=['DELETE'])
def delete_cruise(cruise_id):
    try:
        deleted = cruise_service.delete_cruise_by_id(cruise_id)
        if not deleted:
            return jsonify({'error': 'Cruise not found'}), 404
        return jsonify({'message': f'Cruise with ID {cruise_id} deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
