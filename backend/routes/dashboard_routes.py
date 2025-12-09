from flask import Blueprint, render_template
from backend.models.route import Route
from backend.services.route_evaluator import evaluate_route
from backend.utils.helpers import get_current_language  # ✅ Import language helper

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route("/")
def dashboard():
    # Get current language from query/session
    lang = get_current_language()

    # Fetch all routes from the database
    routes = Route.query.all()
    voyages = []

    # Run evaluation for each route and prepare data for the dashboard
    for r in routes:
        eval_result = evaluate_route(r.id)
        voyages.append({
            "id": r.id,
            "name": r.name,
            "status": eval_result.get("status", "Unknown"),
            "color": eval_result.get("color", "secondary")
        })

    # Render the dashboard template with routes and language
    return render_template("maritime_split/dashboard_base.html", lang="en")
