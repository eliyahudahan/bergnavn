from datetime import datetime
from flask import Blueprint, request, jsonify
from backend import db
from backend.models.cruise import Cruise

# Define the Blueprint for cruise-related routes
cruise_bp = Blueprint('cruise', __name__)

# Function to get all cruises from the database
def get_all_cruises():
    return Cruise.query.all()

# Route for creating a new cruise
@cruise_bp.route('/cruises', methods=['POST'])
def create_cruise():
    data = request.get_json()  # Get the data from the request in JSON format
    try:
        # Create a new cruise object using the data from the request
        new_cruise = Cruise(
            title=data['title'],
            description=data.get('description'),  # Use get to handle missing description gracefully
            departure_date=datetime.fromisoformat(data['departure_date']),  # Convert string to datetime object
            return_date=datetime.fromisoformat(data['return_date']),  # Convert string to datetime object
            price=data['price']
        )
        db.session.add(new_cruise)  # Add the new cruise to the database session
        db.session.commit()  # Commit the session to save changes to the database
        return jsonify({'message': 'Cruise created successfully'}), 201  # Return success response
    except Exception as e:
        # Return an error message in case of failure
        return jsonify({'error': str(e)}), 400

