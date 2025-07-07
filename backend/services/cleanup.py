from backend.models import WeatherStatus
from backend.extensions import db
from datetime import datetime, timedelta

def deactivate_old_weather_status(days=30):
    threshold_date = datetime.utcnow() - timedelta(days=days)

    old_records = WeatherStatus.query.filter(
        WeatherStatus.datetime < threshold_date,
        WeatherStatus.is_active == True
    ).all()

    for record in old_records:
        record.is_active = False

    db.session.commit()
    print(f"Deactivated {len(old_records)} old weather status records.")
