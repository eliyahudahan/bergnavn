# backend/routes/ml_routes.py

from flask import Blueprint, request, jsonify
from backend.ml.recommendation_engine import recommend_cruises

# Create a Blueprint for ML API routes
ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

@ml_bp.route('/recommend', methods=['POST'])
def get_recommendations():
    """
    Route: POST /api/ml/recommend
    Purpose: Receive input data and return cruise recommendations.
    Returns a JSON list of recommended cruises or an error message.
    """
    data = request.json
    try:
        recommendations = recommend_cruises(data)
        return jsonify([{
            "id": c.id,
            "title": c.title,
            "origin": c.origin,
            "destination": c.destination,
            "price": c.price
        } for c in recommendations])
    except Exception as e:
        # Return error as JSON with status code 400
        return jsonify({"error": str(e)}), 400
