# backend/routes/ml_routes.py
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from typing import Any, Dict
from backend.middleware.api_key_auth import require_api_key
from backend.services.fuel_optimizer_service import optimize_vessel_async
from backend.ml.recommendation_engine import EmpiricalRouteRecommender

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
    """
    Get empirical route recommendations based on vessel data and weather
    """
    data = request.get_json(silent=True) or {}
    try:
        # Initialize the empirical route recommender
        recommender = EmpiricalRouteRecommender()
        
        # Extract parameters with defaults
        vessel_data = data.get('vessel', {})
        weather_forecast = data.get('weather', {})
        max_recommendations = data.get('max_recommendations', 3)
        
        # Get empirical route recommendations
        recommendations = recommender.recommend_optimal_routes(
            vessel_data, weather_forecast, max_recommendations
        )
        
        # Convert recommendations to JSON-serializable format
        result = []
        for rec in recommendations:
            result.append({
                "route_id": rec.route_id,
                "origin": rec.origin,
                "destination": rec.destination,
                "estimated_duration_hours": rec.estimated_duration_hours,
                "duration_confidence_interval": rec.duration_confidence_interval,
                "fuel_consumption_tons": rec.fuel_consumption_tons,
                "fuel_confidence_interval": rec.fuel_confidence_interval,
                "weather_risk_score": rec.weather_risk_score,
                "eem_savings_potential": rec.eem_savings_potential,
                "recommendation_confidence": rec.recommendation_confidence,
                "data_sources": rec.data_sources
            })
        
        return _json_response("success", result)
        
    except Exception as e:
        return _json_response("error", message=str(e), code=400)

@ml_bp.route('/optimize', methods=['POST'])
@require_api_key
async def optimize_speed():
    """
    Optimize vessel speed and route using empirical fuel optimization
    """
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

@ml_bp.route('/available-routes', methods=['GET'])
def get_available_routes():
    """
    Get list of all available routes with empirical data
    """
    try:
        recommender = EmpiricalRouteRecommender()
        routes = recommender.get_available_routes()
        
        # Format routes for better display
        formatted_routes = []
        for route_key in routes:
            origin, destination = route_key.split('_')
            formatted_routes.append({
                "route_key": route_key,
                "origin": origin,
                "destination": destination,
                "display_name": f"{origin.title()} → {destination.title()}"
            })
        
        return _json_response("success", formatted_routes)
        
    except Exception as e:
        return _json_response("error", message=str(e), code=400)

@ml_bp.route('/route-details/<route_key>', methods=['GET'])
def get_route_details(route_key):
    """
    Get detailed empirical data for a specific route
    """
    try:
        recommender = EmpiricalRouteRecommender()
        route_data = recommender.route_data.get(route_key)
        
        if not route_data:
            return _json_response("error", message=f"Route '{route_key}' not found", code=404)
        
        # Add route key to response
        route_data['route_key'] = route_key
        origin, destination = route_key.split('_')
        route_data['origin'] = origin
        route_data['destination'] = destination
        route_data['display_name'] = f"{origin.title()} → {destination.title()}"
        
        return _json_response("success", route_data)
        
    except Exception as e:
        return _json_response("error", message=str(e), code=400)