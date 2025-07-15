import pytest
from datetime import datetime
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
    """מנקה ומטעין מחדש נתוני בדיקה לפני כל טסט."""
    with app.app_context():
        # איפוס הדאטהבייס
        db.drop_all()
        db.create_all()

        # יצירת פורטים ריאליים
        stockholm = Port(name="Stockholm", is_active=True)
        visby = Port(name="Visby", is_active=True)
        riga = Port(name="Riga", is_active=True)
        klaipeda = Port(name="Klaipeda", is_active=True)
        gdansk = Port(name="Gdansk", is_active=True)
        warnemuende = Port(name="Warnemuende", is_active=True)
        copenhagen = Port(name="Copenhagen", is_active=True)

        db.session.add_all([stockholm, visby, riga, klaipeda, gdansk, warnemuende, copenhagen])
        db.session.commit()

        # יצירת מסלול פעיל
        baltic_route = Route(id=5, name="Baltic Highlights", is_active=True)
        db.session.add(baltic_route)
        db.session.commit()

        # יצירת legs בין הפורטים
        legs = [
            (stockholm, visby),
            (visby, riga),
            (riga, klaipeda),
            (klaipeda, gdansk),
            (gdansk, warnemuende),
            (warnemuende, copenhagen),
        ]
        for dep, arr in legs:
            leg = VoyageLeg(
                route_id=baltic_route.id,
                departure_port_id=dep.id,
                arrival_port_id=arr.id,
                is_active=True,
                is_critical=False
            )
            db.session.add(leg)

        db.session.commit()

        # סימולציית מזג אוויר אדום ב־Gdansk
        bad_weather = WeatherStatus(
            port_id=gdansk.id,
            alert_level="red",
            is_active=True,
            datetime=datetime.utcnow()
        )
        db.session.add(bad_weather)
        db.session.commit()

