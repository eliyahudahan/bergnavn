from flask import Blueprint, request, jsonify, render_template
from backend.models.route import Route, RouteLeg
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
                    'departure_city': leg.departure_city,
                    'arrival_city': leg.arrival_city,
                    'distance_nm': leg.distance_nm,
                    'estimated_time_days': leg.estimated_time_days,
                    'order': leg.order
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
        total_distance_nm=data.get('total_distance_nm')
    )
    db.session.add(new_route)
    db.session.commit()
    return jsonify({'message': 'Route created', 'id': new_route.id}), 201

@routes_bp.route('/<int:route_id>/legs', methods=['POST'])
def add_route_leg(route_id):
    route = Route.query.get_or_404(route_id)
    data = request.json

    new_leg = RouteLeg(
        route_id=route.id,
        departure_city=data['departure_city'],
        arrival_city=data['arrival_city'],
        distance_nm=data.get('distance_nm'),
        estimated_time_days=data.get('estimated_time_days'),
        order=data.get('order')
    )
    db.session.add(new_leg)
    db.session.commit()

    return jsonify({'message': 'Leg added', 'leg_id': new_leg.id}), 201

@routes_bp.route('/view')
def view_routes():
    routes = Route.query.options(db.joinedload(Route.legs)).all()
    return render_template('routes.html', routes=routes)


