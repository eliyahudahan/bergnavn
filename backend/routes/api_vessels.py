"""
Real-time Vessel API Endpoints
Uses multiple maritime data sources with smart fallback.
Environment variables required from .env:
- USE_KYSTVERKET_AIS: true/false
- USE_KYSTDATAHUSET_AIS: true/false
- BARENTSWATCH_CLIENT_ID: BarentsWatch API client ID
- BARENTSWATCH_CLIENT_SECRET: BarentsWatch API client secret
- KYSTVERKET_AIS_HOST, KYSTVERKET_AIS_PORT: Kystverket AIS connection
"""

import logging
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timezone
import random

logger = logging.getLogger(__name__)

# Create blueprint
vessels_bp = Blueprint('vessels_api', __name__, url_prefix='/maritime/api/vessels')


def _create_fallback_vessel(lat=60.3913, lon=5.3221):
    """Create empirical fallback vessel data when all APIs fail"""
    vessel_types = ['Cargo', 'Tanker', 'Passenger', 'Fishing']
    port_names = ['Bergen', 'Oslo', 'Stavanger', 'Trondheim', 'Ålesund']
    
    return {
        'mmsi': f'257{random.randint(100000, 999999)}',
        'name': f'MS NORWAY {random.randint(1, 99)}',
        'lat': lat + random.uniform(-0.1, 0.1),
        'lon': lon + random.uniform(-0.1, 0.1),
        'speed_knots': round(random.uniform(5, 15), 1),
        'course': random.uniform(0, 360),
        'heading': random.uniform(0, 360),
        'type': random.choice(vessel_types),
        'destination': random.choice(port_names),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_source': 'empirical_fallback',
        'is_empirical': False,
        'fallback_reason': 'All real-time APIs unavailable'
    }


def _get_empirical_vessel_from_services():
    """
    Try to get a real vessel from available empirical services
    Returns empirical vessel if found, None otherwise
    """
    try:
        # Try Kystdatahuset first (Norwegian open AIS)
        if current_app.config.get('USE_KYSTDATAHUSET_AIS', False):
            try:
                from backend.services.kystdatahuset_adapter import kystdatahuset_adapter
                bergen_vessels = kystdatahuset_adapter.get_vessels_near_city('bergen', radius_km=20)
                if bergen_vessels:
                    vessel = bergen_vessels[0]
                    vessel['data_source'] = 'kystdatahuset'
                    vessel['is_empirical'] = True
                    vessel['source_url'] = 'https://www.kystdatahuset.no/api/v1/ais'
                    return vessel
            except Exception as e:
                logger.debug(f"Kystdatahuset unavailable: {e}")
        
        # Try BarentsWatch AIS
        try:
            from backend.services.barentswatch_service import barentswatch_service
            # Bergen area bounding box
            bbox = "5.2,60.3,5.4,60.5"
            vessels = barentswatch_service.get_vessel_positions(bbox=bbox, limit=5)
            if vessels:
                vessel = vessels[0]
                return {
                    'mmsi': str(vessel.get('mmsi', '')),
                    'name': vessel.get('name', 'Unknown'),
                    'lat': vessel.get('latitude', 60.3913),
                    'lon': vessel.get('longitude', 5.3221),
                    'speed_knots': vessel.get('speed', 0),
                    'course': vessel.get('course', 0),
                    'heading': vessel.get('heading', 0),
                    'type': vessel.get('shipType', 'Unknown'),
                    'data_source': 'barentswatch',
                    'is_empirical': True,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'source_url': 'https://www.barentswatch.no/bwapi/'
                }
        except Exception as e:
            logger.debug(f"BarentsWatch unavailable: {e}")
        
        # Try empirical maritime service (already combines sources)
        try:
            from backend.services.empirical_ais_service import empirical_maritime_service
            vessel = empirical_maritime_service.get_bergen_vessel_empirical()
            if vessel:
                return vessel
        except Exception as e:
            logger.debug(f"Empirical service unavailable: {e}")
        
        return None
        
    except ImportError as e:
        logger.warning(f"Service import failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting empirical vessel: {e}")
        return None


@vessels_bp.route('/kystverket', methods=['GET'])
def get_kystverket_vessels():
    """
    Get vessels from Kystverket AIS service.
    
    Query parameters:
    - port: Port name (default: 'bergen')
    - limit: Maximum vessels to return (default: 1)
    
    Returns:
    - JSON with vessel data and service status
    """
    try:
        port = request.args.get('port', 'bergen')
        limit = request.args.get('limit', 1, type=int)
        
        # Import the Kystverket service
        try:
            from backend.services.kystverket_ais_service import kystverket_ais_service
        except ImportError as e:
            logger.error(f"Kystverket service not available: {e}")
            return jsonify({
                'status': 'error',
                'message': 'Kystverket AIS service not available',
                'recommendation': 'Check if kystverket_ais_service.py exists in backend/services/'
            }), 503
        
        # Get vessels from Kystverket
        vessels = kystverket_ais_service.get_vessels_near_port(port, limit)
        
        # Get service status
        service_status = kystverket_ais_service.get_service_status()
        
        # Prepare response
        response = {
            'status': 'success',
            'data_source': 'kystverket_ais',
            'service_status': service_status,
            'vessels': vessels,
            'count': len(vessels),
            'port': port,
            'limit': limit,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': {
                'service_enabled': service_status.get('enabled', False),
                'valid_configuration': service_status.get('valid_configuration', False),
                'connection_active': service_status.get('connection_active', False),
                'vessels_in_cache': service_status.get('vessels_in_cache', 0)
            }
        }
        
        # Log the result
        if vessels:
            vessel_names = [v.get('name', 'Unknown') for v in vessels]
            logger.info(f"✅ Kystverket: Found {len(vessels)} vessel(s) near {port}: {', '.join(vessel_names)}")
        else:
            logger.info(f"📭 Kystverket: No vessels found near {port}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error in get_kystverket_vessels: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get Kystverket vessel data',
            'error': str(e)[:200],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'recommendation': 'Check Kystverket service configuration and connection'
        }), 500


@vessels_bp.route('/real-time', methods=['GET'])
def get_real_time_vessel():
    """
    Get ONE real vessel from available sources with smart priority
    
    Priority order:
    1. Kystverket (new - highest priority if available)
    2. Kystdatahuset
    3. BarentsWatch
    4. Empirical Service
    5. Fallback simulation
    
    Query parameters:
    - city: Norwegian city name (default: bergen)
    - radius_km: Search radius in kilometers (default: 20)
    - source: Force specific source (optional)
    """
    try:
        # Get query parameters
        city = request.args.get('city', 'bergen').lower()
        radius_km = float(request.args.get('radius_km', 20))
        force_source = request.args.get('source', '').lower()
        
        # If forcing a source, use that
        if force_source:
            if force_source == 'kystverket':
                response = get_kystverket_vessels()
                return response
            elif force_source == 'kystdatahuset':
                return _get_kystdatahuset_vessel(city, radius_km)
            elif force_source == 'barentswatch':
                return _get_barentswatch_vessel(city, radius_km)
            elif force_source == 'empirical':
                return _get_empirical_vessel()
        
        # Smart priority order
        sources_tried = []
        
        # 1. Try Kystverket first (new highest priority)
        try:
            from backend.services.kystverket_ais_service import kystverket_ais_service
            service_status = kystverket_ais_service.get_service_status()
            
            if service_status.get('valid_configuration', False) and service_status.get('enabled', False):
                vessels = kystverket_ais_service.get_vessels_near_port(city, limit=1)
                if vessels:
                    vessel = vessels[0]
                    sources_tried.append('kystverket')
                    
                    response = {
                        'status': 'success',
                        'source': 'kystverket_ais',
                        'vessel': vessel,
                        'is_realtime': vessel.get('is_realtime', False),
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'sources_tried': sources_tried,
                        'metadata': {
                            'city_requested': city,
                            'radius_km': radius_km,
                            'service_status': service_status
                        }
                    }
                    
                    logger.info(f"✅ Using Kystverket vessel: {vessel.get('name')}")
                    return jsonify(response)
        except Exception as e:
            sources_tried.append(f'kystverket (failed: {str(e)[:50]})')
            logger.debug(f"Kystverket unavailable: {e}")
        
        # 2. Try Kystdatahuset
        empirical_vessel = _get_empirical_vessel_from_services()
        if empirical_vessel:
            sources_tried.append('kystdatahuset')
            
            response = {
                'status': 'success',
                'source': empirical_vessel.get('data_source', 'unknown'),
                'vessel': empirical_vessel,
                'is_empirical': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'sources_tried': sources_tried,
                'metadata': {
                    'city_requested': city,
                    'radius_km': radius_km,
                    'api_endpoint': '/maritime/api/vessels/real-time',
                    'environment_configured': {
                        'kystdatahuset': current_app.config.get('USE_KYSTDATAHUSET_AIS', False),
                        'barentswatch': bool(current_app.config.get('BARENTSWATCH_CLIENT_ID')),
                        'kystverket': bool(current_app.config.get('USE_KYSTVERKET_AIS', False))
                    }
                }
            }
            
            logger.info(f"✅ Real-time vessel from {empirical_vessel.get('data_source')}: {empirical_vessel.get('name')}")
            return jsonify(response)
        
        # 3. Fallback to empirical simulated vessel
        sources_tried.append('empirical_fallback')
        fallback_vessel = _create_fallback_vessel()
        response = {
            'status': 'fallback',
            'source': 'empirical_simulation',
            'vessel': fallback_vessel,
            'is_empirical': False,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sources_tried': sources_tried,
            'message': 'Using empirical fallback data - real-time APIs unavailable',
            'metadata': {
                'warning': 'Real-time data sources unavailable',
                'fallback_reason': 'All APIs failed or offline',
                'environment_check': {
                    'kystverket_enabled': current_app.config.get('USE_KYSTVERKET_AIS', False),
                    'kystdatahuset_enabled': current_app.config.get('USE_KYSTDATAHUSET_AIS', False),
                    'barentswatch_configured': bool(current_app.config.get('BARENTSWATCH_CLIENT_ID'))
                }
            }
        }
        
        logger.warning(f"⚠️ Using fallback vessel: {fallback_vessel.get('name')} (tried: {', '.join(sources_tried)})")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error in get_real_time_vessel: {e}")
        # Ultimate fallback
        fallback = _create_fallback_vessel()
        return jsonify({
            'status': 'error',
            'vessel': fallback,
            'is_empirical': False,
            'error': str(e)[:100],
            'message': 'Emergency fallback - server error occurred',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })


def _get_kystdatahuset_vessel(city, radius_km):
    """Get vessel specifically from Kystdatahuset"""
    try:
        if current_app.config.get('USE_KYSTDATAHUSET_AIS', False):
            from backend.services.kystdatahuset_adapter import kystdatahuset_adapter
            vessels = kystdatahuset_adapter.get_vessels_near_city(city, radius_km=radius_km)
            if vessels:
                vessel = vessels[0]
                vessel['data_source'] = 'kystdatahuset'
                vessel['is_empirical'] = True
                
                return jsonify({
                    'status': 'success',
                    'source': 'kystdatahuset',
                    'vessel': vessel,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
    except Exception as e:
        logger.debug(f"Kystdatahuset specific call failed: {e}")
    
    # Fallback
    fallback = _create_fallback_vessel()
    return jsonify({
        'status': 'fallback',
        'source': 'kystdatahuset_fallback',
        'vessel': fallback,
        'message': 'Kystdatahuset unavailable, using fallback',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


def _get_barentswatch_vessel(city, radius_km):
    """Get vessel specifically from BarentsWatch"""
    try:
        from backend.services.barentswatch_service import barentswatch_service
        
        # Get coordinates for city
        city_coords = {
            'bergen': (60.3913, 5.3221),
            'oslo': (59.9139, 10.7522),
            'stavanger': (58.9699, 5.7331),
            'trondheim': (63.4305, 10.3951),
        }
        
        if city in city_coords:
            lat, lon = city_coords[city]
            # Create bbox
            bbox = f"{lon-0.1},{lat-0.1},{lon+0.1},{lat+0.1}"
            vessels = barentswatch_service.get_vessel_positions(bbox=bbox, limit=1)
            
            if vessels:
                vessel = vessels[0]
                return jsonify({
                    'status': 'success',
                    'source': 'barentswatch',
                    'vessel': {
                        'mmsi': str(vessel.get('mmsi', '')),
                        'name': vessel.get('name', 'Unknown'),
                        'lat': vessel.get('latitude', lat),
                        'lon': vessel.get('longitude', lon),
                        'speed_knots': vessel.get('speed', 0),
                        'course': vessel.get('course', 0),
                        'type': vessel.get('shipType', 'Unknown'),
                        'data_source': 'barentswatch',
                        'is_empirical': True
                    },
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
    except Exception as e:
        logger.debug(f"BarentsWatch specific call failed: {e}")
    
    # Fallback
    fallback = _create_fallback_vessel()
    return jsonify({
        'status': 'fallback',
        'source': 'barentswatch_fallback',
        'vessel': fallback,
        'message': 'BarentsWatch unavailable, using fallback',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


def _get_empirical_vessel():
    """Get vessel from empirical service"""
    try:
        from backend.services.empirical_ais_service import empirical_maritime_service
        vessel = empirical_maritime_service.get_bergen_vessel_empirical()
        if vessel:
            return jsonify({
                'status': 'success',
                'source': 'empirical_service',
                'vessel': vessel,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    except Exception as e:
        logger.debug(f"Empirical service specific call failed: {e}")
    
    # Fallback
    fallback = _create_fallback_vessel()
    return jsonify({
        'status': 'fallback',
        'source': 'empirical_fallback',
        'vessel': fallback,
        'message': 'Empirical service unavailable, using fallback',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@vessels_bp.route('/empirical-status', methods=['GET'])
def get_empirical_status():
    """
    Check status of all empirical data sources
    Useful for debugging and monitoring
    """
    status = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment_config': {
            'USE_KYSTVERKET_AIS': current_app.config.get('USE_KYSTVERKET_AIS', False),
            'USE_KYSTDATAHUSET_AIS': current_app.config.get('USE_KYSTDATAHUSET_AIS', False),
            'BARENTSWATCH_CLIENT_ID_set': bool(current_app.config.get('BARENTSWATCH_CLIENT_ID')),
            'BARENTSWATCH_CLIENT_SECRET_set': bool(current_app.config.get('BARENTSWATCH_CLIENT_SECRET')),
            'MET_USER_AGENT_set': bool(current_app.config.get('MET_USER_AGENT'))
        },
        'data_sources': {},
        'recommendations': []
    }
    
    # Check Kystverket (new)
    try:
        from backend.services.kystverket_ais_service import kystverket_ais_service
        service_status = kystverket_ais_service.get_service_status()
        status['data_sources']['kystverket'] = service_status
        if service_status.get('valid_configuration') and not service_status.get('enabled'):
            status['recommendations'].append('Kystverket configured but disabled. Set USE_KYSTVERKET_AIS=true in .env')
    except Exception as e:
        status['data_sources']['kystverket'] = {
            'available': False,
            'error': str(e),
            'status': 'not_configured'
        }
        status['recommendations'].append('Kystverket service not available. Ensure kystverket_ais_service.py exists')
    
    # Check Kystdatahuset
    try:
        from backend.services.kystdatahuset_adapter import kystdatahuset_adapter
        test_vessels = kystdatahuset_adapter.get_vessels_near_city('bergen', radius_km=10)
        status['data_sources']['kystdatahuset'] = {
            'available': True,
            'vessels_found': len(test_vessels),
            'status': 'operational' if test_vessels else 'no_data'
        }
    except Exception as e:
        status['data_sources']['kystdatahuset'] = {
            'available': False,
            'error': str(e),
            'status': 'unavailable'
        }
        if current_app.config.get('USE_KYSTDATAHUSET_AIS', False):
            status['recommendations'].append('Kystdatahuset configured but unavailable. Check KYSTDATAHUSET_USER_AGENT in .env')
    
    # Check BarentsWatch
    try:
        from backend.services.barentswatch_service import barentswatch_service
        service_status = barentswatch_service.get_service_status()
        status['data_sources']['barentswatch'] = {
            'available': True,
            'token_valid': service_status['authentication']['token_valid'],
            'scope': service_status['authentication']['current_scope'],
            'status': 'operational'
        }
    except Exception as e:
        status['data_sources']['barentswatch'] = {
            'available': False,
            'error': str(e),
            'status': 'unavailable'
        }
        if current_app.config.get('BARENTSWATCH_CLIENT_ID'):
            status['recommendations'].append('BarentsWatch credentials set but service unavailable')
    
    # Check empirical service
    try:
        from backend.services.empirical_ais_service import empirical_maritime_service
        empirical_status = empirical_maritime_service.get_service_status()
        status['data_sources']['empirical_maritime_service'] = empirical_status
    except Exception as e:
        status['data_sources']['empirical_maritime_service'] = {
            'available': False,
            'error': str(e),
            'status': 'unavailable'
        }
    
    # Overall assessment
    operational_sources = []
    for name, source in status['data_sources'].items():
        if source.get('available') and source.get('status') in ['operational', 'connected']:
            operational_sources.append(name)
    
    status['overall_assessment'] = {
        'operational_sources': operational_sources,
        'total_sources': len(status['data_sources']),
        'readiness': 'ready' if len(operational_sources) > 0 else 'not_ready',
        'primary_source': 'kystverket' if 'kystverket' in operational_sources else 
                         'kystdatahuset' if 'kystdatahuset' in operational_sources else
                         'barentswatch' if 'barentswatch' in operational_sources else
                         'empirical' if 'empirical_maritime_service' in operational_sources else
                         'none',
        'recommendation': 'All good' if len(operational_sources) > 0 else 
                         'Check environment variables and restart application'
    }
    
    return jsonify(status)


@vessels_bp.route('/test/<source>', methods=['GET'])
def test_vessel_source(source):
    """
    Test a specific vessel data source
    Available sources: kystverket, kystdatahuset, barentswatch, empirical, all
    """
    source = source.lower()
    results = {}
    
    if source in ['kystverket', 'all']:
        try:
            from backend.services.kystverket_ais_service import kystverket_ais_service
            vessels = kystverket_ais_service.get_vessels_near_port('bergen', limit=2)
            results['kystverket'] = {
                'success': True,
                'vessels_found': len(vessels),
                'sample': vessels[0] if vessels else None,
                'service_status': kystverket_ais_service.get_service_status()
            }
        except Exception as e:
            results['kystverket'] = {
                'success': False,
                'error': str(e),
                'recommendation': 'Check USE_KYSTVERKET_AIS, KYSTVERKET_AIS_HOST, KYSTVERKET_AIS_PORT in .env'
            }
    
    if source in ['kystdatahuset', 'all']:
        try:
            from backend.services.kystdatahuset_adapter import kystdatahuset_adapter
            vessels = kystdatahuset_adapter.get_vessels_near_city('bergen', radius_km=20)
            results['kystdatahuset'] = {
                'success': True,
                'vessels_found': len(vessels),
                'sample': vessels[0] if vessels else None,
                'endpoint_used': 'https://www.kystdatahuset.no/api/v1/ais/vessels'
            }
        except Exception as e:
            results['kystdatahuset'] = {
                'success': False,
                'error': str(e),
                'recommendation': 'Check KYSTDATAHUSET_USER_AGENT in .env'
            }
    
    if source in ['barentswatch', 'all']:
        try:
            from backend.services.barentswatch_service import barentswatch_service
            bbox = "5.2,60.3,5.4,60.5"
            vessels = barentswatch_service.get_vessel_positions(bbox=bbox, limit=3)
            results['barentswatch'] = {
                'success': True,
                'vessels_found': len(vessels),
                'sample': vessels[0] if vessels else None,
                'scope': 'ais'
            }
        except Exception as e:
            results['barentswatch'] = {
                'success': False,
                'error': str(e),
                'recommendation': 'Check BARENTSWATCH_CLIENT_ID and BARENTSWATCH_CLIENT_SECRET in .env'
            }
    
    if source in ['empirical', 'all']:
        vessel = _get_empirical_vessel_from_services()
        results['empirical_service'] = {
            'success': vessel is not None,
            'vessel_found': vessel is not None,
            'vessel': vessel,
            'is_empirical': vessel.get('is_empirical', False) if vessel else False
        }
    
    return jsonify({
        'test_source': source,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'results': results,
        'environment_check': {
            'USE_KYSTVERKET_AIS': current_app.config.get('USE_KYSTVERKET_AIS', False),
            'USE_KYSTDATAHUSET_AIS': current_app.config.get('USE_KYSTDATAHUSET_AIS', False),
            'BARENTSWATCH_CLIENT_ID_set': bool(current_app.config.get('BARENTSWATCH_CLIENT_ID'))
        }
    })


@vessels_bp.route('/all-sources', methods=['GET'])
def get_all_sources_vessels():
    """
    Get vessels from ALL available sources for comparison
    Useful for testing and data quality assessment
    """
    port = request.args.get('port', 'bergen')
    results = {}
    
    # Collect from all sources
    sources = ['kystverket', 'kystdatahuset', 'barentswatch']
    
    for source in sources:
        try:
            if source == 'kystverket':
                from backend.services.kystverket_ais_service import kystverket_ais_service
                vessels = kystverket_ais_service.get_vessels_near_port(port, limit=3)
                results[source] = {
                    'count': len(vessels),
                    'vessels': vessels[:2],  # Limit to 2 for response size
                    'status': 'success'
                }
            elif source == 'kystdatahuset':
                from backend.services.kystdatahuset_adapter import kystdatahuset_adapter
                vessels = kystdatahuset_adapter.get_vessels_near_city(port, radius_km=20)
                results[source] = {
                    'count': len(vessels),
                    'vessels': vessels[:2],
                    'status': 'success'
                }
            elif source == 'barentswatch':
                from backend.services.barentswatch_service import barentswatch_service
                # Approximate bbox for port
                bbox = "5.2,60.3,5.4,60.5" if port == 'bergen' else "10.6,59.8,10.8,60.0"
                vessels = barentswatch_service.get_vessel_positions(bbox=bbox, limit=3)
                results[source] = {
                    'count': len(vessels),
                    'vessels': vessels[:2],
                    'status': 'success'
                }
        except Exception as e:
            results[source] = {
                'count': 0,
                'error': str(e),
                'status': 'failed'
            }
    
    # Summary
    total_vessels = sum(r['count'] for r in results.values() if 'count' in r)
    successful_sources = [s for s, r in results.items() if r.get('status') == 'success']
    
    response = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'port': port,
        'results': results,
        'summary': {
            'total_vessels_across_sources': total_vessels,
            'successful_sources': successful_sources,
            'successful_source_count': len(successful_sources),
            'primary_recommendation': successful_sources[0] if successful_sources else 'none'
        }
    }
    
    return jsonify(response)


# Add to app.py registration
def register_vessel_routes(app):
    """Register vessel API routes with Flask app"""
    app.register_blueprint(vessels_bp)
    logger.info("✅ Vessel API routes registered")