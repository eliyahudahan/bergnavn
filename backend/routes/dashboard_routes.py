from flask import Blueprint, render_template
from backend.services.route_evaluator import evaluate_route
from backend.models.route import Route

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    # משיכת כל המסלולים (לדוגמה)
    routes = Route.query.all()
    voyages = []
    for r in routes:
        eval_result = evaluate_route(r.id)
        voyages.append({
            "id": r.id,
            "name": r.name,
            "status": eval_result["status"],
            "color": eval_result["color"]
        })
    return render_template("dashboard.html", voyages=voyages)
