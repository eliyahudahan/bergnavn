# backend/routes/ml_routes.py
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from typing import Any, Dict
from backend.middleware.api_key_auth import require_api_key
from backend.services.fuel_optimizer_service import optimize_vessel_async
from backend.ml.recommendation_engine import recommend_cruises

ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

def _json_response(status: str, data: Any = None, message: str = "", code: int = 200):
    payload = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "request_id": getattr(g, "request_id", None)
    }
    if data is not None:
        payload["data"] = data
    if message:
        payload["message"] = message
    return jsonify(payload), code

@ml_bp.route('/recommend', methods=['POST'])
def get_recommendations():
    data = request.get_json(silent=True) or {}
    try:
        recommendations = recommend_cruises(data)
        result = [{
            "id": c.id,
            "title": c.title,
            "origin": c.origin,
            "destination": c.destination,
            "price": c.price
        } for c in recommendations]
        return _json_response("success", result)
    except Exception as e:
        return _json_response("error", message=str(e), code=400)

@ml_bp.route('/optimize', methods=['POST'])
@require_api_key
async def optimize_speed():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    if not payload or 'ais' not in payload or 'weather' not in payload:
        return _json_response("error", message="Invalid payload, expected keys 'ais' and 'weather'", code=400)

    vessel_data: Dict[str, Any] = payload['ais']
    weather_data: Dict[str, Any] = payload['weather']
    vessel_data['request_id'] = getattr(g, "request_id", None)

    try:
        result = await optimize_vessel_async(vessel_data, weather_data)
        return _json_response("success", result)
    except Exception as e:
        return _json_response("error", message="Optimization failed", code=500)
