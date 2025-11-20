"""
Tests for route evaluation service.
Tests cover route status evaluation, weather impact, and port conditions.
"""

import sys
import os
import pytest

# Ensure PYTHONPATH includes the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.services.route_evaluator import evaluate_route


def test_route_not_found(mocker):
    """
    Test evaluation of non-existent route returns appropriate status.
    """
    # Mock the database query to return None (route not found)
    mock_query = mocker.Mock()
    mock_query.get.return_value = None
    mocker.patch('backend.services.route_evaluator.Route.query', mock_query)
    
    result = evaluate_route(999)
    assert result == {"status": "NOT_FOUND", "color": "black"}


def test_route_with_no_legs(mocker):
    """
    Test route with no voyage legs returns appropriate error status.
    """
    # Mock a route with no legs
    mock_route = mocker.Mock()
    mock_route.id = 1
    mock_route.name = "Test Route"
    mock_route.is_active = True
    mock_route.legs = []  # No legs
    
    # Mock the database query
    mock_query = mocker.Mock()
    mock_query.get.return_value = mock_route
    mocker.patch('backend.services.route_evaluator.Route.query', mock_query)
    
    result = evaluate_route(1)
    # Should return NO_LEGS status
    assert result["status"] == "NO_LEGS"
    assert result["color"] == "grey"


def test_route_ok(mocker):
    """
    Test route with all conditions optimal returns OK status.
    """
    # Mock a voyage leg with all required attributes
    mock_leg = mocker.Mock()
    mock_leg.departure_port_id = 1
    mock_leg.arrival_port_id = 2
    mock_leg.leg_order = 1
    mock_leg.is_active = True

    # Mock active ports
    mock_departure_port = mocker.Mock()
    mock_departure_port.id = 1
    mock_departure_port.is_active = True
    
    mock_arrival_port = mocker.Mock()
    mock_arrival_port.id = 2  
    mock_arrival_port.is_active = True

    mock_leg.departure_port = mock_departure_port
    mock_leg.arrival_port = mock_arrival_port

    # Mock route
    mock_route = mocker.Mock()
    mock_route.id = 2
    mock_route.name = "Baltic Explorer"
    mock_route.is_active = True
    mock_route.legs = [mock_leg]

    # Mock database queries
    mock_route_query = mocker.Mock()
    mock_route_query.get.return_value = mock_route
    mocker.patch('backend.services.route_evaluator.Route.query', mock_route_query)
    
    # Mock weather query to return no active weather alerts
    mock_weather_query = mocker.Mock()
    mock_weather_query.filter_by.return_value.order_by.return_value.first.return_value = None
    mocker.patch('backend.services.route_evaluator.WeatherStatus.query', mock_weather_query)
    
    result = evaluate_route(2)
    assert result["status"] == "OK"
    assert result["color"] == "green"


def test_route_with_inactive_port(mocker):
    """
    Test route with inactive port returns reroute recommendation.
    """
    mock_leg = mocker.Mock()
    mock_leg.departure_port_id = 1
    mock_leg.arrival_port_id = 2
    mock_leg.leg_order = 1
    mock_leg.is_active = True

    # Mock inactive port
    mock_port = mocker.Mock()
    mock_port.id = 1
    mock_port.is_active = False  # Inactive port
    
    mock_leg.departure_port = mock_port
    mock_leg.arrival_port = mock_port

    mock_route = mocker.Mock()
    mock_route.id = 3
    mock_route.name = "Scandinavian Circle"
    mock_route.is_active = True
    mock_route.legs = [mock_leg]

    # Mock database queries
    mock_route_query = mocker.Mock()
    mock_route_query.get.return_value = mock_route
    mocker.patch('backend.services.route_evaluator.Route.query', mock_route_query)
    
    # Mock weather query
    mock_weather_query = mocker.Mock()
    mock_weather_query.filter_by.return_value.order_by.return_value.first.return_value = None
    mocker.patch('backend.services.route_evaluator.WeatherStatus.query', mock_weather_query)
    
    result = evaluate_route(3)
    assert result['status'] == "REROUTE_NEEDED"
    assert result['color'] == "orange"


def test_route_with_severe_weather(mocker):
    """
    Test route with severe weather returns reroute recommendation.
    """
    mock_leg = mocker.Mock()
    mock_leg.departure_port_id = 1
    mock_leg.arrival_port_id = 2
    mock_leg.leg_order = 1
    mock_leg.is_active = True

    # Mock active port
    mock_port = mocker.Mock()
    mock_port.id = 1
    mock_port.is_active = True
    
    mock_leg.departure_port = mock_port
    mock_leg.arrival_port = mock_port

    mock_route = mocker.Mock()
    mock_route.id = 4
    mock_route.name = "Nordic Winds"
    mock_route.is_active = True
    mock_route.legs = [mock_leg]

    # Mock severe weather
    mock_status = mocker.Mock()
    mock_status.is_active = True
    mock_status.alert_level = "red"  # Severe weather
    
    # Mock database queries
    mock_route_query = mocker.Mock()
    mock_route_query.get.return_value = mock_route
    mocker.patch('backend.services.route_evaluator.Route.query', mock_route_query)
    
    # Mock weather query to return severe weather
    mock_weather_result = mocker.Mock()
    mock_weather_result.first.return_value = mock_status
    mock_weather_query = mocker.Mock()
    mock_weather_query.filter_by.return_value.order_by.return_value = mock_weather_result
    mocker.patch('backend.services.route_evaluator.WeatherStatus.query', mock_weather_query)
    
    result = evaluate_route(4)
    assert result['status'] == "REROUTE_NEEDED"
    assert result['color'] == "orange"


def test_route_with_both_issues(mocker):
    """
    Test route with both inactive port and severe weather returns highest priority status.
    """
    mock_leg = mocker.Mock()
    mock_leg.departure_port_id = 1
    mock_leg.arrival_port_id = 2
    mock_leg.leg_order = 1
    mock_leg.is_active = True

    # Mock inactive port
    mock_port = mocker.Mock()
    mock_port.id = 1
    mock_port.is_active = False
    
    mock_leg.departure_port = mock_port
    mock_leg.arrival_port = mock_port

    mock_route = mocker.Mock()
    mock_route.id = 5
    mock_route.name = "Worst Case Baltic"
    mock_route.is_active = True
    mock_route.legs = [mock_leg]

    # Mock severe weather
    mock_status = mocker.Mock()
    mock_status.is_active = True
    mock_status.alert_level = "black"  # Most severe
    
    # Mock database queries
    mock_route_query = mocker.Mock()
    mock_route_query.get.return_value = mock_route
    mocker.patch('backend.services.route_evaluator.Route.query', mock_route_query)
    
    # Mock weather query
    mock_weather_result = mocker.Mock()
    mock_weather_result.first.return_value = mock_status
    mock_weather_query = mocker.Mock()
    mock_weather_query.filter_by.return_value.order_by.return_value = mock_weather_result
    mocker.patch('backend.services.route_evaluator.WeatherStatus.query', mock_weather_query)
    
    result = evaluate_route(5)
    assert result['status'] == "REROUTE_NEEDED"
    assert result['color'] == "orange"