from flask import Blueprint, request, jsonify, render_template
from backend import db
from backend.models.cruise import Cruise
from datetime import datetime

# Define the Blueprint for cruises
cruise_blueprint = Blueprint('cruise', __name__)

# Route for creating a new cruise (POST)
@cruise_blueprint.route('/cruises', methods=['POST'])
def create_cruise():
    data = request.get_json()  # Get JSON from request
    try:
        new_cruise = Cruise(
            title=data['title'],
            description=data.get('description'),
            departure_date=datetime.fromisoformat(data['departure_date']),
            return_date=datetime.fromisoformat(data['return_date']),
            price=data['price']
        )
        db.session.add(new_cruise)
        db.session.commit()
        return jsonify({'message': 'Cruise created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Route for getting all cruises as JSON (GET)
@cruise_blueprint.route('/cruises', methods=['GET'])
def get_cruises():
    cruises = Cruise.query.all()
    cruises_data = [{
        'id': cruise.id,
        'title': cruise.title,
        'description': cruise.description,
        'departure_date': cruise.departure_date.isoformat() if cruise.departure_date else None,
        'return_date': cruise.return_date.isoformat() if cruise.return_date else None,
        'price': cruise.price
    } for cruise in cruises]
    return jsonify(cruises_data), 200

# Route for rendering HTML page with cruises (GET)
@cruise_blueprint.route('/cruises/view', methods=['GET'])
def view_cruises():
    cruises = Cruise.query.all()  # Query all cruises from DB
    return render_template('cruises.html', cruises=cruises)




