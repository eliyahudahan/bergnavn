from flask import Blueprint, request, jsonify, render_template
from backend.controllers.cruise_controller import (
    create_cruise,
    get_all_cruises,
    delete_cruise_by_id
)
from backend.models.cruise import Cruise
from backend.utils.helpers import get_current_language  # <-- added for language support

# Create blueprint for cruise routes
cruise_blueprint = Blueprint('cruise', __name__)

@cruise_blueprint.route('/cruises', methods=['POST'])
def create():
    """Route: Create cruise (JSON)"""
    data = request.get_json()
    return create_cruise(data)

@cruise_blueprint.route('/cruises', methods=['GET'])
def get_all():
    """Route: Return all cruises (JSON)"""
    return get_all_cruises()

@cruise_blueprint.route('/cruises/view', methods=['GET'])
def view_cruises():
    """
    Route: Show all cruises page
    Purpose: Render cruises.html template with all cruises
    """
    lang = get_current_language()  # <-- get language from query/session
    cruises = Cruise.query.all()
    return render_template('cruises.html', cruises=cruises, lang=lang)

@cruise_blueprint.route('/cruises/<int:cruise_id>', methods=['DELETE'])
def delete(cruise_id):
    """Route: Delete cruise by ID (JSON)"""
    return delete_cruise_by_id(cruise_id)
