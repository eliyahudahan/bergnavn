import sys
import os

# Ensure PYTHONPATH includes the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from backend.services.route_evaluator import evaluate_route

# Test 1: Route does not exist in DB
def test_route_not_found(mocker):
    mocker.patch('backend.services.route_evaluator.Route.query.get', return_value=None)
    result = evaluate_route(999)
    assert result == {"status": "NOT_FOUND"}

# Test 2: Route exists but has no legs
def test_route_with_no_legs(mocker):
    mock_route = mocker.Mock()
    mock_route.legs = []
    mocker.patch('backend.services.route_evaluator.Route.query.get', return_value=mock_route)
    result = evaluate_route(1)
    assert result == {"status": "NO_LEGS"}

# Test 3: Valid route, all ports active, no weather issues
def test_route_ok(mocker):
    mock_leg = mocker.Mock()
    mock_leg.departure_port_id = 1
    mock_leg.arrival_port_id = 2
    mock_leg.leg_order = 1

    mock_route = mocker.Mock()
    mock_route.legs = [mock_leg]
    mock_route.name = "Baltic Explorer"

    mock_status = mocker.Mock()
    mock_status.is_active = True
    mock_status.alert_level = "green"
    mock_status.port.name = "Riga"

    mocker.patch('backend.services.route_evaluator.Route.query.get', return_value=mock_route)
    mocker.patch('backend.services.route_evaluator.WeatherStatus.query.filter_by',
                 return_value=mocker.Mock(order_by=lambda _: mocker.Mock(first=lambda: mock_status)))

    result = evaluate_route(2)
    assert result == {"status": "OK"}

# Test 4: One port is inactive (e.g. closed for maintenance)
def test_route_with_inactive_port(mocker):
    mock_leg = mocker.Mock()
    mock_leg.departure_port_id = 1
    mock_leg.arrival_port_id = 2

    mock_route = mocker.Mock()
    mock_route.legs = [mock_leg]
    mock_route.name = "Scandinavian Circle"

    mock_status = mocker.Mock()
    mock_status.is_active = False
    mock_status.alert_level = "green"
    mock_status.port.name = "Gdansk"

    mocker.patch('backend.services.route_evaluator.Route.query.get', return_value=mock_route)
    mocker.patch('backend.services.route_evaluator.WeatherStatus.query.filter_by',
                 return_value=mocker.Mock(order_by=lambda _: mocker.Mock(first=lambda: mock_status)))

    result = evaluate_route(3)
    assert result['status'] == "REROUTE_NEEDED"
    assert "Port Gdansk inactive" in result['issues']

# Test 5: Severe weather alert (e.g. red alert)
def test_route_with_severe_weather(mocker):
    mock_leg = mocker.Mock()
    mock_leg.departure_port_id = 1
    mock_leg.arrival_port_id = 2

    mock_route = mocker.Mock()
    mock_route.legs = [mock_leg]
    mock_route.name = "Nordic Winds"

    mock_status = mocker.Mock()
    mock_status.is_active = True
    mock_status.alert_level = "red"
    mock_status.port.name = "Tallinn"

    mocker.patch('backend.services.route_evaluator.Route.query.get', return_value=mock_route)
    mocker.patch('backend.services.route_evaluator.WeatherStatus.query.filter_by',
                 return_value=mocker.Mock(order_by=lambda _: mocker.Mock(first=lambda: mock_status)))

    result = evaluate_route(4)
    assert result['status'] == "REROUTE_NEEDED"
    assert "Alert at Tallinn: red" in result['issues']

# Test 6: Both inactive port and black weather alert
def test_route_with_both_issues(mocker):
    mock_leg = mocker.Mock()
    mock_leg.departure_port_id = 1
    mock_leg.arrival_port_id = 2

    mock_route = mocker.Mock()
    mock_route.legs = [mock_leg]
    mock_route.name = "Worst Case Baltic"

    def get_mock_status(port_id):
        status = mocker.Mock()
        if port_id == 1:
            status.is_active = False
            status.alert_level = "green"
            status.port.name = "Klaipeda"
        else:
            status.is_active = True
            status.alert_level = "black"
            status.port.name = "Helsinki"
        return status

    def filter_by_side_effect(**kwargs):
        port_id = kwargs.get("port_id")
        return mocker.Mock(order_by=lambda _: mocker.Mock(first=lambda: get_mock_status(port_id)))

    mocker.patch('backend.services.route_evaluator.Route.query.get', return_value=mock_route)
    mocker.patch('backend.services.route_evaluator.WeatherStatus.query.filter_by',
                 side_effect=filter_by_side_effect)

    result = evaluate_route(5)
    assert result['status'] == "REROUTE_NEEDED"
    assert "Port Klaipeda inactive" in result['issues']
    assert "Alert at Helsinki: black" in result['issues']

