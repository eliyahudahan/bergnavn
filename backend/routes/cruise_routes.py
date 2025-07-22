from flask import Blueprint, request, jsonify, render_template
from backend.controllers.cruise_controller import (
    create_cruise,
    get_all_cruises,
    delete_cruise_by_id
)
from backend.models.cruise import Cruise

cruise_blueprint = Blueprint('cruise', __name__)

@cruise_blueprint.route('/cruises', methods=['POST'])
def create():
    data = request.get_json()
    return create_cruise(data)

@cruise_blueprint.route('/cruises', methods=['GET'])
def get_all():
    return get_all_cruises()

@cruise_blueprint.route('/cruises/view', methods=['GET'])
def view_cruises():
    cruises = Cruise.query.all()
    return render_template('cruises.html', cruises=cruises)

@cruise_blueprint.route('/cruises/<int:cruise_id>', methods=['DELETE'])
def delete(cruise_id):
    return delete_cruise_by_id(cruise_id)





