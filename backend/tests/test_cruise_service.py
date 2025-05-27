import pytest
from datetime import datetime, UTC
from app import create_app
from backend.extensions import db
from backend.services.cruise_service import create_cruise_with_clock


@pytest.fixture(scope='module')
def test_app():
    app = create_app('testing')
    with app.app_context():
        yield app


@pytest.fixture(scope='module')
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture(scope='module')
def init_database(test_app):
    # Setup: create all tables
    db.create_all()

    yield db  # This provides the db object to the test

    # Teardown: clean up
    db.session.remove()
    db.drop_all()


def test_create_cruise_with_clock(init_database):
    # Sample cruise data for creating a new cruise record
    data = {
        "title": "Test Cruise",
        "description": "Short trip to sea",
        "departure_date": datetime(2025, 6, 1, 9, 0),
        "return_date": datetime(2025, 6, 2, 18, 0),
        "origin": "Copenhagen",
        "destination": "Hamburg",
        "origin_lat": 55.6761,
        "origin_lon": 12.5683,
        "price": 120.0,
        "capacity": 50
    }

    # Act
    cruise = create_cruise_with_clock(data)

    # Assert
    assert cruise.id is not None
    assert cruise.clock is not None
    assert cruise.clock.timezone is not None
    assert cruise.origin == "Copenhagen"
    assert cruise.title == "Test Cruise"


