"""
Tests for cruise service functionality.
Tests cover cruise creation, management, and related operations.
"""

import pytest
from datetime import datetime
from app import create_app
from backend.extensions import db
from backend.services.cruise_service import CruiseService


@pytest.fixture(scope='module')
def test_app():
    """Create test application with testing configuration."""
    app = create_app('testing')
    with app.app_context():
        yield app


@pytest.fixture(scope='module')
def test_client(test_app):
    """Create test client for making HTTP requests."""
    return test_app.test_client()


@pytest.fixture(scope='module')
def init_database(test_app):
    """Initialize test database with all tables."""
    # Setup: create all tables
    db.create_all()

    yield db  # This provides the db object to the test

    # Teardown: clean up
    db.session.remove()
    db.drop_all()


@pytest.fixture
def cruise_service():
    """Create CruiseService instance for testing."""
    return CruiseService()


def test_create_cruise(init_database, cruise_service):
    """
    Test creating a new cruise with basic data.
    Verifies cruise creation and basic attribute assignment.
    """
    # Sample cruise data for creating a new cruise record
    data = {
        "title": "Test Cruise",
        "description": "Short trip to sea",
        "departure_date": "2025-06-01T09:00:00",
        "return_date": "2025-06-02T18:00:00",
        "origin": "Copenhagen",
        "destination": "Hamburg",
        "origin_lat": 55.6761,
        "origin_lon": 12.5683,
        "price": 120.0,
        "capacity": 50
    }

    # Act: Create cruise using the service
    cruise = cruise_service.create_cruise(data)

    # Assert: Verify cruise was created successfully
    assert cruise.id is not None
    assert cruise.origin == "Copenhagen"
    assert cruise.title == "Test Cruise"
    assert cruise.price == 120.0
    assert cruise.capacity == 50


def test_get_all_cruises(init_database, cruise_service):
    """
    Test retrieving all cruises from the service.
    """
    # First create a cruise with unique title to avoid conflicts
    unique_title = f"Test Cruise for List {datetime.now().timestamp()}"
    data = {
        "title": unique_title,
        "departure_date": "2025-06-01T09:00:00",
        "return_date": "2025-06-02T18:00:00",
        "origin": "Oslo",
        "destination": "Bergen",
        "price": 100.0,
        "capacity": 40
    }
    cruise_service.create_cruise(data)

    # Act: Get all cruises
    cruises = cruise_service.get_all_cruises()

    # Assert
    assert isinstance(cruises, list)
    assert len(cruises) >= 1
    
    # Find our specific cruise in the list
    test_cruise = next((c for c in cruises if c['title'] == unique_title), None)
    assert test_cruise is not None
    assert test_cruise['title'] == unique_title