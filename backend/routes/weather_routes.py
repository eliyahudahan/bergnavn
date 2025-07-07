from flask import Blueprint, render_template
from backend.models import WeatherStatus, Route
from sqlalchemy import desc, and_, func
from backend.extensions import db

weather_bp = Blueprint('weather', __name__, url_prefix='/weather')

@weather_bp.route('/')
def weather_dashboard():
    # שליפת התאריך האחרון לכל port_id (רק רשומות פעילות)
    subquery = (
        db.session.query(
            WeatherStatus.port_id,
            func.max(WeatherStatus.datetime).label('max_datetime')
        )
        .filter(WeatherStatus.is_active == True)
        .group_by(WeatherStatus.port_id)
        .subquery()
    )

    # שליפת רשומות WeatherStatus העדכניות בלבד
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

    # שליפת מסלולים פעילים כולל הרגליים שלהם ממויינים לפי leg_order
    routes = (
        Route.query
        .filter(Route.is_active == True)
        .order_by(Route.id)
        .all()
    )

    # לטעון את הרגליים עם סדר, לשם כך ניתן לגשת דרך היחס 'legs' ומוודא שהרגליים ממוקדות לפי leg_order:
    for route in routes:
        route.legs.sort(key=lambda leg: leg.leg_order)

    return render_template('weather_dashboard.html', statuses=latest_statuses, routes=routes)


