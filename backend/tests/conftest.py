import os
import sys
import pytest
from datetime import datetime

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
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
    return app

@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield

@pytest.fixture(autouse=True)
def seed_test_data(app):
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Ports
        bergen = Port(name="Bergen", latitude=60.39299, longitude=5.32415, country="Norway", is_active=True)
        oslo = Port(name="Oslo", latitude=59.9139, longitude=10.7522, country="Norway", is_active=True)
        trondheim = Port(name="Trondheim", latitude=63.4305, longitude=10.3951, country="Norway", is_active=True)

        db.session.add_all([bergen, oslo, trondheim])
        db.session.commit()

        # Route
        norwegian_route = Route(id=1, name="Norwegian Fjords", is_active=True)
        db.session.add(norwegian_route)
        db.session.commit()

        # Voyage legs
        legs = [(bergen, oslo), (oslo, trondheim)]
        for dep, arr in legs:
            leg = VoyageLeg(
                route_id=norwegian_route.id,
                departure_port_id=dep.id,
                arrival_port_id=arr.id,
                is_active=True,
                is_critical=False,
            )
            db.session.add(leg)
        db.session.commit()

        # Weather simulation
        bad_weather = WeatherStatus(
            port_id=trondheim.id,
            alert_level="red",
            is_active=True,
            datetime=datetime.utcnow(),
        )
        db.session.add(bad_weather)
        db.session.commit()
