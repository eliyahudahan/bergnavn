from flask import jsonify
from datetime import datetime
from backend.models.cruise import Cruise
from backend.extensions import db

def create_cruise(data):
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

def get_all_cruises():
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

def delete_cruise_by_id(cruise_id):
    cruise = Cruise.query.get(cruise_id)
    if not cruise:
        return jsonify({'error': 'Cruise not found'}), 404
    db.session.delete(cruise)
    db.session.commit()
    return jsonify({'message': f'Cruise with ID {cruise_id} deleted successfully'}), 200

