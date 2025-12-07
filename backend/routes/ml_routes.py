# backend/routes/ml_routes.py
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from typing import Any, Dict

from backend.middleware.api_key_auth import require_api_key
from backend.ml.recommendation_engine import EmpiricalRouteRecommender

# Safe import for optimize_vessel_async
try:
    from backend.services.fuel_optimizer_service import optimize_vessel_async
except Exception:
    optimize_vessel_async = None

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")


def _json_response(status: str, data: Any = None, message: str = "", code: int = 200):
    """Standard JSON response format."""
    payload = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "request_id": getattr(g, "request_id", None),
    }
    if data is not None:
        payload["data"] = data
    if message:
        payload["message"] = message
    return jsonify(payload), code


def _json_safe_error(msg: str):
    """Return a safe non-crashing error response."""
    return _json_response("error", message=msg, code=200)


# -------------------------------------------------------------------
#       ROUTE RECOMMENDATIONS (EMPIRICAL ENGINE)
# -------------------------------------------------------------------
@ml_bp.route("/recommend", methods=["POST"])
def get_recommendations():
    """Return empirical route recommendations."""
    data = request.get_json(silent=True) or {}

    try:
        recommender = EmpiricalRouteRecommender()
        vessel_data = data.get("vessel", {})
        weather_data = data.get("weather", {})
        max_rec = data.get("max_recommendations", 3)

        recs = recommender.recommend_optimal_routes(
            vessel_data, weather_data, max_rec
        )

        formatted = []
        for r in recs:
            formatted.append({
                "route_id": r.route_id,
                "origin": r.origin,
                "destination": r.destination,
                "estimated_duration_hours": r.estimated_duration_hours,
                "duration_confidence_interval": r.duration_confidence_interval,
                "fuel_consumption_tons": r.fuel_consumption_tons,
                "fuel_confidence_interval": r.fuel_confidence_interval,
                "weather_risk_score": r.weather_risk_score,
                "eem_savings_potential": r.eem_savings_potential,
                "recommendation_confidence": r.recommendation_confidence,
                "data_sources": r.data_sources,
            })

        return _json_response("success", formatted)

    except Exception as e:
        return _json_safe_error(f"Recommendation engine failed: {e}")


# -------------------------------------------------------------------
#       EMPIRICAL FUEL & SPEED OPTIMIZER
# -------------------------------------------------------------------
@ml_bp.route("/optimize", methods=["POST"])
@require_api_key
async def optimize_speed():
    """Optimize vessel speed and fuel using empirical cubic model."""
    if optimize_vessel_async is None:
        return _json_safe_error("Fuel optimization service unavailable.")

    payload = request.get_json(silent=True) or {}

    if "ais" not in payload or "weather" not in payload:
        return _json_safe_error("Missing required keys: 'ais' and 'weather'.")

    vessel = payload.get("ais", {})
    weather = payload.get("weather", {})
    vessel["request_id"] = getattr(g, "request_id", None)

    try:
        result = await optimize_vessel_async(vessel, weather)
        return _json_response("success", result)
    except Exception as e:
        safe_default = {
            "optimized_speed_knots": 10,
            "fuel_tons_estimate": 0.0,
            "warning": f"Optimizer failed; returned default result ({e})."
        }
        return _json_response("success", safe_default)


# -------------------------------------------------------------------
#       ROUTE LISTING
# -------------------------------------------------------------------
@ml_bp.route("/available-routes", methods=["GET"])
def get_available_routes():
    """List all empirical routes."""
    try:
        recommender = EmpiricalRouteRecommender()
        keys = recommender.get_available_routes()

        formatted = []
        for key in keys:
            origin, destination = key.split("_")
            formatted.append({
                "route_key": key,
                "origin": origin,
                "destination": destination,
                "display_name": f"{origin.title()} → {destination.title()}"
            })

        return _json_response("success", formatted)

    except Exception as e:
        return _json_safe_error(f"Failed to load routes: {e}")


# -------------------------------------------------------------------
#       ROUTE DETAILS
# -------------------------------------------------------------------
@ml_bp.route("/route-details/<route_key>", methods=["GET"])
def get_route_details(route_key):
    """Return empirical details for one route."""
    try:
        recommender = EmpiricalRouteRecommender()
        info = recommender.route_data.get(route_key)

        if not info:
            return _json_safe_error(f"Route '{route_key}' not found.")

        origin, destination = route_key.split("_")
        info["route_key"] = route_key
        info["origin"] = origin
        info["destination"] = destination
        info["display_name"] = f"{origin.title()} → {destination.title()}"

        return _json_response("success", info)

    except Exception as e:
        return _json_safe_error(f"Failed to load route details: {e}")
