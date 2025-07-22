from flask import Blueprint, render_template
from backend.models.route import Route
from backend.services.route_evaluator import evaluate_route

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    routes = Route.query.all()
    voyages = []
    for r in routes:
        eval_result = evaluate_route(r.id)
        voyages.append({
            "id": r.id,
            "name": r.name,
            "status": eval_result.get("status", "Unknown"),
            "color": eval_result.get("color", "secondary")
        })
    return render_template("dashboard.html", voyages=voyages)
