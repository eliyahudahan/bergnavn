from flask import Blueprint, jsonify
from backend import db

# Blueprint for system / health endpoints
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """
    Endpoint: Health check
    Purpose:
        - Verify DB connectivity by executing a simple query.
        - Return JSON status: "ok" if successful, "error" if failed.
    """
    try:
        db.session.execute('SELECT 1')  # Simple DB query to check connection
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "details": str(e)}), 500
