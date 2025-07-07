# backend/routes/ml_routes.py

from flask import Blueprint, request, jsonify
from backend.ml.recommendation_engine import recommend_cruises

ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

@ml_bp.route('/recommend', methods=['POST'])
def get_recommendations():
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
        return jsonify({"error": str(e)}), 400

