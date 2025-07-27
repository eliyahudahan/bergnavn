from flask import Blueprint, render_template
from backend.models.route import Route
from backend.services.route_evaluator import evaluate_route

# הגדרת ה‑Blueprint
dashboard_bp = Blueprint('dashboard_bp', __name__)

# הנתיב הראשי עבור הדשבורד
@dashboard_bp.route("/")
def dashboard():
    # שליפת כל המסלולים מה‑DB
    routes = Route.query.all()
    voyages = []

    # הרצת הערכת מסלול עבור כל מסלול
    for r in routes:
        eval_result = evaluate_route(r.id)
        voyages.append({
            "id": r.id,
            "name": r.name,
            "status": eval_result.get("status", "Unknown"),
            "color": eval_result.get("color", "secondary")
        })

    # החזרת התבנית עם הנתונים
    return render_template("dashboard.html", voyages=voyages)

