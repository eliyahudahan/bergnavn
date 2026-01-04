"""
Simulation Routes for BergNavn
Adds ship simulation capabilities to existing system
"""

from flask import Blueprint, jsonify, request
from backend.simulation.integrated_simulator import get_simulator

# Create blueprint for simulation routes
simulation_bp = Blueprint('simulation', __name__, url_prefix='/api/simulation')

@simulation_bp.route('/status', methods=['GET'])
def get_simulation_status():
    """
    Get current simulation status.
    
    Returns:
        JSON with simulation status
    """
    simulator = get_simulator()
    return jsonify({
        'status': 'success',
        'simulation': simulator.get_status(),
        'timestamp': datetime.now().isoformat()
    })

@simulation_bp.route('/start', methods=['POST'])
def start_simulation():
    """
    Start the simulation.
    
    Request body (optional):
        {
            "route_name": "Bergen to Oslo"
        }
    
    Returns:
        JSON with start confirmation
    """
    data = request.json or {}
    route_name = data.get('route_name', 'Bergen to Oslo')
    
    simulator = get_simulator(route_name)
    success = simulator.start_simulation()
    
    return jsonify({
        'status': 'started' if success else 'already_running',
        'message': 'Simulation started successfully' if success else 'Simulation already running',
        'route': route_name,
        'ship': simulator.ship_name
    })

@simulation_bp.route('/stop', methods=['POST'])
def stop_simulation():
    """
    Stop the simulation.
    
    Returns:
        JSON with stop confirmation
    """
    simulator = get_simulator()
    simulator.stop_simulation()
    
    return jsonify({
        'status': 'stopped',
        'message': 'Simulation stopped'
    })

@simulation_bp.route('/control/speed', methods=['POST'])
def control_speed():
    """
    Change ship speed.
    
    Request body:
        {
            "delta": 5.0  # Positive to increase, negative to decrease
        }
    
    Returns:
        JSON with new speed
    """
    data = request.json
    if not data or 'delta' not in data:
        return jsonify({'error': 'Missing delta parameter'}), 400
    
    try:
        delta = float(data['delta'])
    except ValueError:
        return jsonify({'error': 'Delta must be a number'}), 400
    
    simulator = get_simulator()
    new_speed = simulator.change_speed(delta)
    
    return jsonify({
        'action': 'speed_change',
        'delta': delta,
        'new_speed': new_speed,
        'message': f'Speed changed to {new_speed:.1f} knots'
    })

@simulation_bp.route('/control/course', methods=['POST'])
def control_course():
    """
    Change ship course.
    
    Request body:
        {
            "delta": 15.0  # Degrees to change course
        }
    
    Returns:
        JSON with new heading
    """
    data = request.json
    if not data or 'delta' not in data:
        return jsonify({'error': 'Missing delta parameter'}), 400
    
    try:
        delta = float(data['delta'])
    except ValueError:
        return jsonify({'error': 'Delta must be a number'}), 400
    
    simulator = get_simulator()
    new_heading = simulator.change_course(delta)
    
    return jsonify({
        'action': 'course_change',
        'delta': delta,
        'new_heading': new_heading,
        'message': f'Course changed to {new_heading:.1f}°'
    })

@simulation_bp.route('/decision', methods=['POST'])
def record_decision():
    """
    Record an operator decision.
    
    Request body:
        {
            "decision_type": "speed_change",
            "decision_data": {"delta": -5},
            "notes": "Reducing speed due to weather"
        }
    
    Returns:
        JSON with recorded decision
    """
    data = request.json
    if not data or 'decision_type' not in data:
        return jsonify({'error': 'Missing decision_type'}), 400
    
    simulator = get_simulator()
    
    decision = simulator.record_operator_decision(
        decision_type=data['decision_type'],
        decision_data=data.get('decision_data', {}),
        notes=data.get('notes', '')
    )
    
    return jsonify({
        'status': 'recorded',
        'decision': decision,
        'total_decisions': len(simulator.operator_decisions)
    })

@simulation_bp.route('/decisions', methods=['GET'])
def get_decisions():
    """
    Get all recorded operator decisions.
    
    Query parameters:
        limit: Maximum number of decisions to return (default: 50)
    
    Returns:
        JSON with decisions
    """
    limit = request.args.get('limit', 50, type=int)
    
    simulator = get_simulator()
    decisions = simulator.get_operator_decisions(limit=limit)
    
    return jsonify({
        'count': len(decisions),
        'limit': limit,
        'decisions': decisions
    })

@simulation_bp.route('/position-history', methods=['GET'])
def get_position_history():
    """
    Get position history.
    
    Returns:
        JSON with position history
    """
    simulator = get_simulator()
    history = simulator.get_position_history()
    
    return jsonify({
        'count': len(history),
        'positions': history
    })

@simulation_bp.route('/routes/available', methods=['GET'])
def get_available_routes():
    """
    Get available RTZ routes for simulation.
    
    Returns:
        JSON with available routes
    """
    try:
        from backend.services.rtz_parser import discover_rtz_files
        
        all_routes = discover_rtz_files(enhanced=False)
        bergen_routes = [r for r in all_routes if r.get('source_city') == 'bergen']
        
        simplified_routes = []
        for route in bergen_routes[:10]:  # Limit to 10 routes
            simplified_routes.append({
                'name': route.get('route_name'),
                'origin': route.get('origin'),
                'destination': route.get('destination'),
                'distance_nm': route.get('total_distance_nm'),
                'waypoints': route.get('waypoint_count', 0),
                'source_city': route.get('source_city')
            })
        
        return jsonify({
            'status': 'success',
            'count': len(simplified_routes),
            'routes': simplified_routes
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'routes': []
        }), 500

@simulation_bp.route('/reset', methods=['POST'])
def reset_simulation():
    """
    Reset simulation to initial state.
    
    Returns:
        JSON with reset confirmation
    """
    simulator = get_simulator()
    simulator.reset_simulation()
    
    return jsonify({
        'status': 'reset',
        'message': 'Simulation reset to initial state'
    })

@simulation_bp.route('/test', methods=['GET'])
def test_simulation():
    """
    Test endpoint to verify simulation is working.
    
    Returns:
        JSON with test results
    """
    simulator = get_simulator()
    
    return jsonify({
        'status': 'operational',
        'simulator': {
            'initialized': True,
            'ship_name': simulator.ship_name,
            'ship_id': simulator.ship_id,
            'route_loaded': bool(simulator.route_data),
            'waypoints_count': len(simulator.waypoints),
            'services_connected': {
                'weather': bool(simulator.weather_service),
                'risk_engine': bool(simulator.risk_engine),
                'alerts_service': bool(simulator.alerts_service)
            }
        },
        'message': 'Simulation system is operational',
        'timestamp': datetime.now().isoformat()
    })


# Import datetime for JSON serialization
from datetime import datetime
