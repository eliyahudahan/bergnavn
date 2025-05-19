from flask import Blueprint, jsonify
from backend import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "details": str(e)}), 500
