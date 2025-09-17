"""
Service layer for Cruise operations.
Handles business logic, database interactions, and related entities (e.g., Clock).
"""

from backend.extensions import db
from backend.models.cruise import Cruise
from backend.models.clock import Clock
from backend.services.timezone_service import get_timezone_from_city
from datetime import datetime, timezone

class CruiseService:
    """
    Service class for Cruise management.
    """

    def create_cruise(self, data):
        """
        Create a new cruise and associated Clock if timezone is available.
        """
        # Create Cruise object from input data
        cruise = Cruise(
            title=data["title"],
            description=data.get("description"),
            departure_date=datetime.fromisoformat(data["departure_date"]),
            return_date=datetime.fromisoformat(data["return_date"]),
            origin=data.get("origin"),
            destination=data.get("destination"),
            origin_lat=data.get("origin_lat"),
            origin_lon=data.get("origin_lon"),
            price=data["price"],
            capacity=data.get("capacity", 0),  # default if not provided
            is_active=True
        )

        db.session.add(cruise)
        db.session.flush()  # Obtain cruise.id before adding Clock

        # Determine timezone for the cruise origin and create Clock
        timezone_str = get_timezone_from_city(cruise.origin)
        if timezone_str:
            clock = Clock(
                cruise_id=cruise.id,
                timezone=timezone_str,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(clock)

        db.session.commit()
        return cruise

    def get_all_cruises(self):
        """
        Retrieve all cruises from the database.
        Returns a list of dictionaries suitable for JSON serialization.
        """
        cruises = Cruise.query.all()
        return [
            {
                'id': cruise.id,
                'title': cruise.title,
                'description': cruise.description,
                'departure_date': cruise.departure_date.isoformat() if cruise.departure_date else None,
                'return_date': cruise.return_date.isoformat() if cruise.return_date else None,
                'origin': cruise.origin,
                'destination': cruise.destination,
                'origin_lat': cruise.origin_lat,
                'origin_lon': cruise.origin_lon,
                'price': cruise.price,
                'capacity': cruise.capacity,
                'is_active': cruise.is_active
            }
            for cruise in cruises
        ]

    def delete_cruise_by_id(self, cruise_id):
        """
        Delete a cruise by ID.
        Returns True if deleted, False if not found.
        """
        cruise = Cruise.query.get(cruise_id)
        if not cruise:
            return False
        db.session.delete(cruise)
        db.session.commit()
        return True
