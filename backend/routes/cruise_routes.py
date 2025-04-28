from flask import Blueprint, request, jsonify
from backend import db
from backend.models.cruise import Cruise
from datetime import datetime

# Define the Blueprint for cruises
cruise_blueprint = Blueprint('cruise', __name__)

# Route for creating a new cruise
@cruise_blueprint.route('/cruises', methods=['POST'])
def create_cruise():
    data = request.get_json()  # Get the JSON data from the request
    try:
        # Create a new cruise object from the data
        new_cruise = Cruise(
            title=data['title'],
            description=data.get('description'),
            departure_date=datetime.fromisoformat(data['departure_date']),
            return_date=datetime.fromisoformat(data['return_date']),
            price=data['price']
        )
        db.session.add(new_cruise)  # Add the new cruise to the session
        db.session.commit()  # Commit the session to the database
        return jsonify({'message': 'Cruise created successfully'}), 201  # Respond with success message
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Respond with error message in case of failure

# Route for getting all cruises
@cruise_blueprint.route('/cruises', methods=['GET'])
def get_cruises():
    cruises = Cruise.query.all()  # Get all cruises from the database
    cruises_data = [{
        'id': cruise.id,
        'title': cruise.title,
        'description': cruise.description,
        'departure_date': cruise.departure_date,
        'return_date': cruise.return_date,
        'price': cruise.price
    } for cruise in cruises]  # Convert each cruise to a dictionary
    
    return jsonify(cruises_data), 200  # Return the list of cruises as JSON with a 200 status code



