from flask import Blueprint, render_template
from backend.models import WeatherStatus, Route
from sqlalchemy import desc, and_, func
from backend.extensions import db
from backend.utils.helpers import get_current_language  # ✅ Import language helper

# Blueprint for weather-related pages
weather_bp = Blueprint('weather', __name__, url_prefix='/weather')

@weather_bp.route('/')
def weather_dashboard():
    """
    UI Endpoint: Weather Dashboard
    Purpose:
        - Display the latest active weather statuses per port.
        - Show all active routes with their ordered legs.
        - Include current language for i18n.
    """
    # Subquery: get the latest datetime for each port_id (only active records)
    subquery = (
        db.session.query(
            WeatherStatus.port_id,
            func.max(WeatherStatus.datetime).label('max_datetime')
        )
        .filter(WeatherStatus.is_active == True)
        .group_by(WeatherStatus.port_id)
        .subquery()
    )

    # Query: fetch only the most recent WeatherStatus entries
    latest_statuses = (
        db.session.query(WeatherStatus)
        .join(
            subquery,
            and_(
                WeatherStatus.port_id == subquery.c.port_id,
                WeatherStatus.datetime == subquery.c.max_datetime
            )
        )
        .all()
    )

    # Query: fetch all active routes with legs ordered by leg_order
    routes = (
        Route.query
        .filter(Route.is_active == True)
        .order_by(Route.id)
        .all()
    )

    # Ensure each route's legs are sorted by leg_order
    for route in routes:
        route.legs.sort(key=lambda leg: leg.leg_order)

    # Get current language for rendering templates
    lang = get_current_language()

    return render_template(
        'weather_dashboard.html',
        statuses=latest_statuses,
        routes=routes,
        lang=lang
    )
