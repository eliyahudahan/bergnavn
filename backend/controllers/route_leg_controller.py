from flask import Blueprint, request, jsonify
from backend.services.route_leg_service import create_route
from datetime import datetime

route_leg_bp = Blueprint("route_leg", __name__)

@route_leg_bp.route("/", methods=["POST"])
def create_full_route():
    data = request.get_json()

    cruise_id = data.get("cruise_id")
    legs = data.get("legs")
    departure_time = data.get("departure_time")

    if not cruise_id or not legs:
        return jsonify({"error": "Missing cruise_id or legs"}), 400

    try:
        parsed_departure_time = datetime.fromisoformat(departure_time) if departure_time else None
        created_legs = create_route(cruise_id, legs, cruise_departure_time=parsed_departure_time)

        return jsonify({
            "message": f"{len(created_legs)} route legs created",
            "legs": [
                {
                    "from": leg.departure_port.name,
                    "to": leg.arrival_port.name,
                    "departure": leg.departure_time.isoformat(),
                    "arrival": leg.arrival_time.isoformat()
                }
                for leg in created_legs
            ]
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
