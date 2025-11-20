"""
Basic model tests for BergNavn maritime application.
Tests cover fundamental database operations and model validation.
"""

import sys
import os
import pytest

# Add project root to PYTHONPATH to import create_app from app.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app import create_app
from backend.models.port import Port
from backend import db


@pytest.fixture(scope='module')
def test_app():
    """
    Create Flask application in 'testing' mode and push context.
    """
    app = create_app('testing')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture(scope='module')
def init_database(test_app):
    """
    Run db.create_all() within application context and cleanup after.
    """
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()


def test_create_port(init_database):
    """
    Basic smoke test for Port model:
    Creation, saving, and retrieval with required coordinates.
    """
    # Create new instance with required latitude/longitude
    port = Port(
        name='Copenhagen', 
        country='Denmark',
        latitude=55.6761,  # Required field
        longitude=12.5683  # Required field
    )
    db.session.add(port)
    db.session.commit()

    # Verify the port was created successfully
    assert port.id is not None
    assert port.name == 'Copenhagen'
    assert port.country == 'Denmark'
    assert port.latitude == 55.6761
    assert port.longitude == 12.5683


def test_port_string_representation(init_database):
    """
    Test that Port string representation is meaningful.
    """
    port = Port(
        name='Oslo', 
        country='Norway',
        latitude=59.9139,
        longitude=10.7522
    )
    
    # Test string representation contains key information
    port_str = str(port)
    # The string representation should contain the port name and coordinates
    assert 'Oslo' in port_str
    assert '59.9139' in port_str  # latitude
    assert '10.7522' in port_str  # longitude