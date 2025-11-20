# backend/tests/conftest.py
import os
import sys
import pytest
from datetime import datetime, UTC

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import create_app
from backend.extensions import db
from backend.models.route import Route
from backend.models.voyage_leg import VoyageLeg
from backend.models.port import Port
from backend.models.weather_status import WeatherStatus

@pytest.fixture(scope="session")
def app():
    """Create application for the tests."""
    app = create_app(testing=True)
    
    with app.app_context():
        # Create all tables - PostgreSQL supports spatial functions
        db.create_all()
        
        yield app
        
        # Cleanup after all tests
        db.drop_all()

@pytest.fixture(autouse=True)
def app_context(app):
    """Automatically provide app context for tests."""
    with app.app_context():
        yield

@pytest.fixture(autouse=True)
def seed_test_data(app):
    """Seed test data for all tests."""
    with app.app_context():
        # Clear existing data
        try:
            db.session.query(WeatherStatus).delete()
            db.session.query(VoyageLeg).delete()
            db.session.query(Route).delete()
            db.session.query(Port).delete()
            db.session.commit()
        except:
            db.session.rollback()
            # If tables don't exist, create them
            db.create_all()

        # Create test ports
        bergen = Port(
            name="Bergen", 
            latitude=60.39299, 
            longitude=5.32415, 
            country="Norway", 
            is_active=True
        )
        oslo = Port(
            name="Oslo", 
            latitude=59.9139, 
            longitude=10.7522, 
            country="Norway", 
            is_active=True
        )
        trondheim = Port(
            name="Trondheim", 
            latitude=63.4305, 
            longitude=10.3951, 
            country="Norway", 
            is_active=True
        )

        db.session.add_all([bergen, oslo, trondheim])
        db.session.commit()

        # Create test route
        norwegian_route = Route(
            id=1, 
            name="Norwegian Fjords", 
            is_active=True
        )
        db.session.add(norwegian_route)
        db.session.commit()

        # Create test voyage legs - עם כל השדות הנדרשים
        legs = [
            (bergen, oslo, "2025-01-01 08:00:00", "2025-01-01 18:00:00", 1, 120.5),
            (oslo, trondheim, "2025-01-01 19:00:00", "2025-01-02 08:00:00", 2, 250.0)
        ]
        
        for dep, arr, dep_time, arr_time, leg_order, distance in legs:
            leg = VoyageLeg(
                route_id=norwegian_route.id,
                departure_port_id=dep.id,
                arrival_port_id=arr.id,
                departure_lat=dep.latitude,
                departure_lon=dep.longitude,
                arrival_lat=arr.latitude,
                arrival_lon=arr.longitude,
                departure_time=datetime.fromisoformat(dep_time.replace(' ', 'T')),
                arrival_time=datetime.fromisoformat(arr_time.replace(' ', 'T')),
                leg_order=leg_order,
                distance_nm=distance,
                is_active=True,
            )
            db.session.add(leg)
        db.session.commit()

        # Create test weather status
        bad_weather = WeatherStatus(
            port_id=trondheim.id,
            alert_level="red",
            is_active=True,
            datetime=datetime.now(UTC),
        )
        db.session.add(bad_weather)
        db.session.commit()

        yield

        # Final cleanup
        db.session.remove()