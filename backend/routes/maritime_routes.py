# backend/routes/maritime_routes.py
# English comments only inside file.
from flask import Blueprint, jsonify, current_app, render_template, request, session

# Blueprint name MUST be 'maritime' so templates using url_for('maritime.dashboard') work.
maritime_bp = Blueprint('maritime', __name__, url_prefix='/maritime')

@maritime_bp.route('/api/live-ships')
def live_ships():
    """
    Return current ships list. Uses app.ais_service if available,
    otherwise returns an empty list.
    """
    try:
        ais = getattr(current_app, "ais_service", None)
        if ais is None:
            return jsonify({'status': 'error', 'error': 'AIS service not attached'}), 500

        # prefer method if exists, otherwise fall back to attribute ships_data
        if hasattr(ais, "get_latest_positions"):
            vessels = ais.get_latest_positions()
        else:
            # ships_data should be a list of vessel dicts kept by the AIS service
            vessels = getattr(ais, "ships_data", []) or []

        return jsonify({
            'status': 'success',
            'count': len(vessels),
            'vessels': vessels
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@maritime_bp.route('/api/optimizer')
def optimizer():
    """
    Simple optimizer placeholder. Returns JSON used by dashboard.
    """
    try:
        result = {
            'status': 'success',
            'recommended_speed': 16.2,
            'fuel_saving_estimate': 8.5,
            'message': 'AI fuel optimization model (placeholder)'
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@maritime_bp.route('/api/alerts')
def alerts():
    """
    Return simple alerts list for dashboard.
    """
    alerts_list = [
        {'type': 'info', 'message': 'System nominal'},
        {'type': 'weather', 'message': 'Monitoring storms in North Sea'}
    ]
    return jsonify({'status': 'success', 'alerts': alerts_list})

@maritime_bp.route('/dashboard')
def dashboard():
    """
    Render the maritime dashboard UI (uses maritime_split/dashboard_base.html).
    Pass 'lang' to template from query param, session, or default 'en'.
    """
    lang = request.args.get('lang') or session.get('lang') or 'en'
    return render_template("maritime_split/dashboard_base.html", lang=lang)
