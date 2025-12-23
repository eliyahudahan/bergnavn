# backend/routes/recommendation_routes.py
"""
API endpoints for the Recommendation Engine.
Provides vessel safety recommendations based on risk assessment.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
recommendation_bp = Blueprint('recommendation', __name__, url_prefix='/api')

# Try to import the recommendation engine
try:
    from backend.services.recommendation_engine import recommendation_engine, generate_recommendation
    ENGINE_AVAILABLE = True
    logger.info("✅ Recommendation engine imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import recommendation engine: {e}")
    ENGINE_AVAILABLE = False
    # Create a dummy engine for graceful degradation
    recommendation_engine = None
    generate_recommendation = None

@recommendation_bp.route('/recommendation/<string:mmsi>', methods=['GET'])
def get_recommendation(mmsi):
    """
    Get safety recommendation for a specific vessel.
    
    Args:
        mmsi: Vessel MMSI (string, can have leading zeros)
    
    Returns:
        JSON recommendation with risk assessment and actionable advice
    """
    # Check if engine is available
    if not ENGINE_AVAILABLE:
        return jsonify({
            'status': 'error',
            'message': 'Recommendation engine not available',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503  # Service Unavailable
    
    try:
        # Validate MMSI format
        if not mmsi or not mmsi.isdigit():
            return jsonify({
                'status': 'error',
                'message': 'Invalid MMSI format. Must be numeric digits only.',
                'mmsi_received': mmsi,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        # Convert to int for processing
        mmsi_int = int(mmsi)
        
        # Validate MMSI length (typically 9 digits for ships)
        if len(mmsi) != 9:
            logger.warning(f"MMSI {mmsi} has unusual length ({len(mmsi)} digits)")
        
        logger.info(f"Generating recommendation for MMSI: {mmsi}")
        
        # Generate recommendation using the engine
        result = generate_recommendation(mmsi_int)
        
        # Add request metadata
        result['request_metadata'] = {
            'mmsi_requested': mmsi,
            'endpoint': '/api/recommendation/<mmsi>',
            'request_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Return with appropriate status code
        if result.get('status') == 'error':
            status_code = 404 if 'not found' in result.get('message', '').lower() else 500
            return jsonify(result), status_code
        else:
            return jsonify(result), 200
            
    except ValueError as e:
        logger.error(f"Value error processing MMSI {mmsi}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Invalid MMSI format: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Error generating recommendation for MMSI {mmsi}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@recommendation_bp.route('/recommendation/batch', methods=['POST'])
def get_batch_recommendations():
    """
    Get recommendations for multiple vessels in a single request.
    
    Expected JSON body:
    {
        "vessels": ["259123000", "258456000", "257789000"],
        "include_metadata": true  # optional
    }
    
    Returns:
        JSON array of recommendation results
    """
    if not ENGINE_AVAILABLE:
        return jsonify({
            'status': 'error',
            'message': 'Recommendation engine not available',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'vessels' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing "vessels" array in request body',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        vessels = data['vessels']
        include_metadata = data.get('include_metadata', True)
        
        if not isinstance(vessels, list):
            return jsonify({
                'status': 'error',
                'message': '"vessels" must be an array of MMSI strings',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        if len(vessels) > 50:  # Limit batch size
            return jsonify({
                'status': 'error',
                'message': 'Batch size limited to 50 vessels per request',
                'vessels_received': len(vessels),
                'max_allowed': 50,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        logger.info(f"Processing batch recommendation request for {len(vessels)} vessels")
        
        results = []
        successful = 0
        failed = 0
        
        for mmsi in vessels:
            try:
                # Validate each MMSI
                if not isinstance(mmsi, str) or not mmsi.isdigit():
                    results.append({
                        'status': 'error',
                        'message': f'Invalid MMSI format: {mmsi}',
                        'vessel_mmsi': str(mmsi),
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                    failed += 1
                    continue
                
                mmsi_int = int(mmsi)
                result = generate_recommendation(mmsi_int)
                
                if include_metadata:
                    result['batch_index'] = len(results)
                    result['batch_total'] = len(vessels)
                
                results.append(result)
                
                if result.get('status') == 'success':
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.warning(f"Failed to process vessel {mmsi} in batch: {e}")
                results.append({
                    'status': 'error',
                    'message': f'Failed to process vessel {mmsi}: {str(e)}',
                    'vessel_mmsi': str(mmsi),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                failed += 1
        
        # Compile batch response
        batch_response = {
            'status': 'success',
            'batch_summary': {
                'total_vessels': len(vessels),
                'successful': successful,
                'failed': failed,
                'success_rate': f"{(successful/len(vessels))*100:.1f}%" if vessels else "0%"
            },
            'results': results,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'processing_time_ms': (datetime.now(timezone.utc) - request_start).total_seconds() * 1000
            if 'request_start' in locals() else 0
        }
        
        return jsonify(batch_response), 200
        
    except Exception as e:
        logger.error(f"Error in batch recommendations: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@recommendation_bp.route('/recommendation/status', methods=['GET'])
def recommendation_status():
    """
    Get status and statistics of the recommendation engine.
    
    Returns:
        JSON with engine status, version, and statistics
    """
    if not ENGINE_AVAILABLE:
        return jsonify({
            'status': 'service_unavailable',
            'message': 'Recommendation engine not loaded',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503
    
    try:
        # Get basic engine information
        status_info = {
            'status': 'operational',
            'engine_name': 'Maritime Recommendation Engine',
            'version': '1.0.0',
            'api_version': '1.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'capabilities': [
                'vessel_risk_assessment',
                'hazard_proximity_detection',
                'weather_impact_analysis',
                'roi_estimation',
                'actionable_recommendations'
            ],
            'dependencies': {
                'risk_engine': recommendation_engine is not None,
                'ais_service': hasattr(recommendation_engine, 'ais_service') and recommendation_engine.ais_service is not None,
                'barentswatch_service': hasattr(recommendation_engine, 'barentswatch_service') and recommendation_engine.barentswatch_service is not None
            }
        }
        
        # Add statistics if available
        if hasattr(recommendation_engine, 'recommendation_history'):
            history = recommendation_engine.recommendation_history
            status_info['statistics'] = {
                'recommendations_generated': len(history),
                'history_size_limit': 1000,
                'oldest_entry': history[0]['timestamp'] if history else None,
                'newest_entry': history[-1]['timestamp'] if history else None
            }
        
        # Add performance metrics
        status_info['performance'] = {
            'batch_processing_supported': True,
            'max_batch_size': 50,
            'response_format': 'json',
            'caching': 'in_memory'
        }
        
        return jsonify(status_info), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendation status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@recommendation_bp.route('/recommendation/test', methods=['GET'])
def test_recommendation():
    """
    Test endpoint with sample vessel data.
    Useful for development and integration testing.
    
    Query parameters:
        - use_real_data: true/false (default: true)
        - vessel_index: 0-2 (default: 0) for sample vessels
    """
    if not ENGINE_AVAILABLE:
        # Provide sample response when engine is unavailable
        return jsonify({
            'status': 'success',
            'vessel': {
                'mmsi': '259123000',
                'name': 'COASTAL TRADER (TEST)',
                'position': {'lat': 60.392, 'lon': 5.324},
                'speed': 12.5,
                'course': 45
            },
            'risk_assessment': {
                'risks': [
                    {
                        'type': 'HAZARD_PROXIMITY',
                        'severity': 'MEDIUM',
                        'message': 'Vessel within 850m of Hywind Tampen (wind_turbine)',
                        'details': {
                            'hazard_name': 'Hywind Tampen',
                            'hazard_type': 'wind_turbine',
                            'distance_meters': 850,
                            'safe_distance_meters': 500
                        }
                    }
                ],
                'summary': {
                    'total_risks': 1,
                    'by_severity': {'HIGH': 0, 'MEDIUM': 1, 'LOW': 0},
                    'highest_severity': 'MEDIUM'
                }
            },
            'recommendations': {
                'all_recommendations': [
                    {
                        'id': 'test_rec_001',
                        'risk_type': 'HAZARD_PROXIMITY',
                        'severity': 'MEDIUM',
                        'action': 'reduce_speed_and_monitor',
                        'message': 'Reduce speed and monitor distance to Hywind Tampen',
                        'priority': 2
                    }
                ],
                'primary_recommendation': {
                    'id': 'test_rec_001',
                    'risk_type': 'HAZARD_PROXIMITY',
                    'severity': 'MEDIUM',
                    'action': 'reduce_speed_and_monitor',
                    'message': 'Reduce speed and monitor distance to Hywind Tampen',
                    'priority': 2
                },
                'count': 1
            },
            'estimated_impact': {
                'fuel_savings_kg': 937.5,
                'time_savings_minutes': -30,
                'cost_savings_nok': 7968.75,
                'confidence': 'medium',
                'calculation_basis': 'Norwegian Maritime Authority averages'
            },
            'metadata': {
                'engine_version': '1.0',
                'data_sources': ['Test Data'],
                'note': 'Engine unavailable - using test data'
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    
    try:
        # Use real engine if available
        use_real_data = request.args.get('use_real_data', 'true').lower() == 'true'
        
        if use_real_data:
            # Test with a real vessel from your system
            sample_vessels = ['259123000', '258456000', '257789000']
            vessel_index = int(request.args.get('vessel_index', 0))
            
            if vessel_index < 0 or vessel_index >= len(sample_vessels):
                vessel_index = 0
            
            mmsi = sample_vessels[vessel_index]
            result = generate_recommendation(int(mmsi))
            
            # Mark as test response
            result['test_data'] = True
            result['test_vessel_index'] = vessel_index
            
            return jsonify(result), 200
        else:
            # Return the same test data as above
            return test_recommendation()  # This will use the fallback above
            
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Test failed: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@recommendation_bp.route('/recommendation/history', methods=['GET'])
def recommendation_history():
    """
    Get recent recommendation history (last 50 entries).
    Requires authentication in production.
    
    Query parameters:
        - limit: number of entries (default: 50, max: 100)
        - vessel_mmsi: filter by specific vessel
    """
    if not ENGINE_AVAILABLE or not hasattr(recommendation_engine, 'recommendation_history'):
        return jsonify({
            'status': 'error',
            'message': 'Recommendation history not available',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 404
    
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        vessel_mmsi = request.args.get('vessel_mmsi')
        
        history = recommendation_engine.recommendation_history
        
        # Filter by vessel if specified
        if vessel_mmsi:
            filtered_history = [
                entry for entry in history 
                if entry.get('vessel_mmsi') == vessel_mmsi
            ]
        else:
            filtered_history = history
        
        # Get most recent entries
        recent_history = filtered_history[-limit:]
        
        return jsonify({
            'status': 'success',
            'history': recent_history,
            'total_entries': len(filtered_history),
            'limit_applied': limit,
            'vessel_filter': vessel_mmsi if vessel_mmsi else 'none',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error accessing recommendation history: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500