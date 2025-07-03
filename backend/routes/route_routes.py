from flask import Blueprint, request, jsonify, render_template
from backend.services.route_leg_service import create_route_leg
from backend.models.route import Route
from backend.models.voyage_leg import VoyageLeg
from backend import db

routes_bp = Blueprint('routes_bp', __name__)

@routes_bp.route('/', methods=['GET'])
def get_routes():
    routes = Route.query.filter_by(is_active=True).all()
    return jsonify([
        {
            'id': r.id,
            'name': r.name,
            'description': r.description,
            'duration_days': r.duration_days,
            'total_distance_nm': r.total_distance_nm,
            'legs': [
                {
                    'id': leg.id,
                    'departure_port_id': leg.departure_port_id,
                    'arrival_port_id': leg.arrival_port_id,
                    'distance_nm': leg.distance_nm,
                    'order': leg.leg_order
                }
                for leg in r.legs
            ]
        }
        for r in routes
    ])

@routes_bp.route('/', methods=['POST'])
def create_route():
    data = request.json

    new_route = Route(
        name=data['name'],
        description=data.get('description'),
        duration_days=data.get('duration_days'),
        total_distance_nm=0
    )
    db.session.add(new_route)
    db.session.commit()

    total_distance = 0
    for i, leg in enumerate(data.get('legs', []), start=1):
        created_leg = create_route_leg(
            route_id=new_route.id,
            departure_name=leg['from'],
            arrival_name=leg['to'],
            leg_order=i
        )
        total_distance += created_leg.distance_nm or 0

    new_route.total_distance_nm = round(total_distance, 2)
    db.session.commit()

    return jsonify({'message': 'Route created with legs', 'id': new_route.id}), 201


@routes_bp.route('/<int:route_id>/legs', methods=['POST'])
def add_route_leg(route_id):
    route = Route.query.get_or_404(route_id)
    data = request.json

    new_leg = VoyageLeg(
        route_id=route.id,
        departure_port_id=data.get('departure_port_id'),
        arrival_port_id=data.get('arrival_port_id'),
        leg_order=data.get('leg_order'),
        distance_nm=data.get('distance_nm')
    )
    db.session.add(new_leg)
    db.session.commit()

    return jsonify({'message': 'Leg added', 'leg_id': new_leg.id}), 201


@routes_bp.route('/view')
def view_routes():
    routes = Route.query.options(db.joinedload(Route.legs)).all()
    return render_template('routes.html', routes=routes)

