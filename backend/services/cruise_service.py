# backend/services/cruise_service.py

from backend import db
from backend.models.cruise import Cruise
from backend.models.clock import Clock
from backend.services.timezone_service import get_timezone_from_city
from datetime import datetime, UTC

def create_cruise_with_clock(data):
    # יצירת אובייקט Cruise מתוך המידע שהתקבל
    cruise = Cruise(
        title=data["title"],
        description=data.get("description"),
        departure_date=data["departure_date"],
        return_date=data["return_date"],
        origin=data.get("origin"),
        destination=data["destination"],
        origin_lat=data.get("origin_lat"),
        origin_lon=data.get("origin_lon"),
        price=data["price"],
        capacity=data.get("capacity", 0),  # ברירת מחדל אם לא נשלח
        is_active=True
    )

    db.session.add(cruise)
    db.session.flush()  # כדי לקבל cruise.id לפני שמוסיפים clock

    # חישוב time zone לפי העיר
    timezone_str = get_timezone_from_city(cruise.origin)
    if timezone_str:
        clock = Clock(
            cruise_id=cruise.id,
            timezone=timezone_str,
            created_at=datetime.now(UTC)
        )
        db.session.add(clock)

    db.session.commit()
    return cruise
