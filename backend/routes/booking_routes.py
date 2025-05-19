from flask import Blueprint, request, jsonify
from backend.models.booking import Booking
from backend import db

booking_blueprint = Blueprint('booking', __name__)

@booking_blueprint.route('/book', methods=['POST'])
def create_booking():
    data = request.get_json()

    try:
        user_id = data['user_id']
        cruise_id = data['cruise_id']
        num_of_people = data['num_of_people']
        total_price = data['total_price']

        # Create new booking
        booking = Booking(user_id=user_id, cruise_id=cruise_id, num_of_people=num_of_people, total_price=total_price)
        db.session.add(booking)
        db.session.commit()

        return jsonify({"message": "Booking created successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
