# backend/routes/maritime_routes.py
from flask import Blueprint, jsonify, current_app, render_template

maritime_bp = Blueprint('maritime_bp', __name__, url_prefix='/maritime')

# ---------------------------
#   Real-time Live Ships API
# ---------------------------
@maritime_bp.route('/api/live-ships')
def live_ships():
    try:
        ais = current_app.ais_service
        vessels = ais.get_latest_positions()

        return jsonify({
            'status': 'success',
            'count': len(vessels),
            'vessels': vessels
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------
#   Fuel Optimization API
# ---------------------------
@maritime_bp.route('/api/optimizer')
def optimizer():
    try:
        result = {
            'recommended_speed': 16.2,
            'fuel_saving_estimate': 8.5,
            'note': 'AI fuel optimization model (placeholder)'
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------
#   Alerts API
# ---------------------------
@maritime_bp.route('/api/alerts')
def alerts():
    alerts_list = [
        {'type': 'info', 'message': 'System nominal'},
        {'type': 'weather', 'message': 'Monitoring storms in North Sea'}
    ]
    return jsonify(alerts_list)


# ---------------------------
#   Maritime Dashboard Page
# ---------------------------
@maritime_bp.route('/dashboard')
def dashboard():
    return render_template("maritime_dashboard.html", lang="en")
