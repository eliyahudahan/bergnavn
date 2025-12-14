# backend/routes/dashboard_routes.py
from flask import Blueprint, render_template, session, jsonify
from backend.utils.helpers import get_current_language

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/')
def dashboard():
    """
    Dashboard home page (different from maritime dashboard).
    """
    lang = get_current_language()
    return render_template("dashboard/home.html", lang=lang)


@dashboard_bp.route('/overview')
def overview():
    """
    Dashboard overview page.
    """
    lang = get_current_language()
    return render_template("dashboard/overview.html", lang=lang)


@dashboard_bp.route('/analytics')
def analytics():
    """
    Analytics dashboard.
    """
    lang = get_current_language()
    return render_template("dashboard/analytics.html", lang=lang)


@dashboard_bp.route('/statistics')
def statistics():
    """
    Statistics dashboard.
    """
    lang = get_current_language()
    return render_template("dashboard/statistics.html", lang=lang)


@dashboard_bp.route('/api/metrics')
def dashboard_metrics():
    """
    API endpoint for dashboard metrics.
    """
    metrics = {
        'total_routes': 42,
        'active_routes': 28,
        'completed_today': 15,
        'avg_duration': 2.4,
        'fuel_saved': 1250,
        'co2_reduced': 3.2
    }
    return jsonify(metrics)