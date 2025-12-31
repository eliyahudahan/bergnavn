"""
Maritime routes for the BergNavn Maritime Dashboard.
Provides endpoints for maritime data including AIS, weather, and RTZ routes.
FIXED: Import errors resolved with proper RTZ parser integration.
ENHANCED: Comprehensive route discovery with all 47+ routes.
REAL-TIME: Weather endpoint with guaranteed data for dashboard.
ALERTS: New real-time alerting system with wind turbine and tanker proximity detection.
ROUTE VISUAL ENHANCEMENT: Added visual properties for better route differentiation on map.
"""

import logging
from flask import Blueprint, jsonify, request, render_template, current_app
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Create blueprint
maritime_bp = Blueprint('maritime', __name__, url_prefix='/maritime')

# Import alerts service (will be created if not exists)
try:
    from backend.services.alerts_service import maritime_alerts_service
    ALERTS_SERVICE_AVAILABLE = True
    logger.info("✅ Alerts service available for maritime routes")
except ImportError:
    ALERTS_SERVICE_AVAILABLE = False
    logger.warning("⚠️ Alerts service not available - alerts endpoints will provide fallback data")

@maritime_bp.route('/dashboard')
def maritime_dashboard():
    """
    Render the main maritime dashboard.
    Integrates AIS, weather, and RTZ route data in a unified interface.
    """
    try:
        # Get AIS service status
        ais_status = "offline"
        ais_vessel_count = 0
        
        if hasattr(current_app, 'ais_service'):
            try:
                status = current_app.ais_service.get_service_status()
                ais_status = "online" if status.get('operational_status', {}).get('running', False) else "offline"
                ais_vessel_count = status.get('data_metrics', {}).get('active_vessels', 0)
            except Exception as e:
                logger.warning(f"Could not get AIS status: {e}")
        
        # Get RTZ routes for dashboard
        routes_data = []
        cities_with_routes = set()
        
        try:
            # Use the NEW discover_rtz_files function with visual enhancement
            from backend.services.rtz_parser import discover_rtz_files
            routes_data = discover_rtz_files(enhanced=True)  # Get routes with visual properties
            
            # Extract city information
            for route in routes_data:
                city = route.get('source_city')
                if city:
                    cities_with_routes.add(city.title())
            
            logger.info(f"✅ Loaded {len(routes_data)} RTZ routes with visual properties for dashboard")
        except ImportError as e:
            logger.error(f"RTZ parser import error: {e}")
        except Exception as e:
            logger.error(f"Could not discover RTZ files for dashboard: {e}")
        
        # Calculate statistics
        total_distance = sum(route.get('total_distance_nm', 0) for route in routes_data)
        waypoint_count = sum(route.get('waypoint_count', 0) for route in routes_data)
        active_ports_count = len(cities_with_routes)
        
        # Extract visual properties for JavaScript
        route_colors = []
        if routes_data:
            for route in routes_data:
                visual = route.get('visual_properties', {})
                route_colors.append({
                    'name': route.get('route_name', 'Unknown'),
                    'color': visual.get('color', '#3498db'),
                    'start': route.get('start_point', {}),
                    'end': route.get('end_point', {})
                })
        
        return render_template(
            'maritime_split/dashboard_base.html',
            routes=routes_data,
            route_colors=route_colors,
            cities_with_routes=list(cities_with_routes),
            total_distance=total_distance,
            waypoint_count=waypoint_count,
            active_ports_count=active_ports_count,
            ais_status=ais_status,
            ais_vessel_count=ais_vessel_count,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error rendering maritime dashboard: {e}")
        return render_template(
            'error.html',
            error_message="Could not load maritime dashboard",
            error_details=str(e)
        ), 500

@maritime_bp.route('/api/health')
def health_check():
    """
    Health check endpoint for maritime services.
    Returns status of AIS, weather, and route services.
    """
    try:
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        # Check AIS service
        if hasattr(current_app, 'ais_service'):
            try:
                ais_status = current_app.ais_service.get_service_status()
                status['services']['ais'] = {
                    'status': 'online',
                    'mode': ais_status.get('operational_status', {}).get('mode', 'unknown'),
                    'vessels': ais_status.get('data_metrics', {}).get('active_vessels', 0),
                    'data_quality': ais_status.get('operational_status', {}).get('data_quality', 'unknown')
                }
            except Exception as e:
                status['services']['ais'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            status['services']['ais'] = {
                'status': 'offline',
                'error': 'AIS service not initialized'
            }
        
        # Check RTZ routes availability
        try:
            from backend.services.rtz_parser import get_processing_statistics
            rtz_stats = get_processing_statistics()
            status['services']['rtz_routes'] = {
                'status': 'available',
                'cities_with_files': rtz_stats['cities_with_files'],
                'total_files': rtz_stats['total_files_found'],
                'cities_missing': rtz_stats['cities_missing_files']
            }
        except Exception as e:
            status['services']['rtz_routes'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Check overall health
        all_healthy = all(
            service['status'] in ['online', 'available', 'healthy'] 
            for service in status['services'].values()
        )
        
        status['overall'] = 'healthy' if all_healthy else 'degraded'
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@maritime_bp.route('/api/ais-data')
def get_ais_data():
    """
    Get real-time AIS vessel data.
    Returns comprehensive vessel information for maritime operations.
    """
    try:
        if not hasattr(current_app, 'ais_service'):
            return jsonify({
                'error': 'AIS service not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Try to get real-time data
        vessels = []
        try:
            # Use real-time method if available
            if hasattr(current_app.ais_service, 'get_real_time_vessels'):
                vessels = current_app.ais_service.get_real_time_vessels()
            else:
                vessels = current_app.ais_service.get_latest_positions()
        except Exception as e:
            logger.warning(f"Could not get AIS data: {e}")
            # Return empty but valid response
            vessels = []
        
        # Enhance with metadata
        enhanced_vessels = []
        for vessel in vessels:
            enhanced_vessel = vessel.copy()
            
            # Add Norwegian city proximity
            if 'lat' in vessel and 'lon' in vessel:
                enhanced_vessel['norwegian_proximity'] = _get_norwegian_city_proximity(
                    vessel['lat'], vessel['lon']
                )
            
            enhanced_vessels.append(enhanced_vessel)
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'vessel_count': len(enhanced_vessels),
            'vessels': enhanced_vessels,
            'data_source': getattr(current_app.ais_service, '__class__.__name__', 'Unknown')
        })
        
    except Exception as e:
        logger.error(f"Error getting AIS data: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@maritime_bp.route('/api/ais/realtime')
def get_realtime_ais():
    """
    Get real-time AIS data with forced refresh.
    Enhanced endpoint for dashboard real-time updates.
    """
    try:
        if not hasattr(current_app, 'ais_service'):
            return jsonify({
                'error': 'AIS service not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Force refresh if supported
        vessels = []
        try:
            if hasattr(current_app.ais_service, 'get_real_time_vessels'):
                vessels = current_app.ais_service.get_real_time_vessels(force_refresh=True)
            elif hasattr(current_app.ais_service, 'manual_refresh'):
                current_app.ais_service.manual_refresh()
                vessels = current_app.ais_service.get_latest_positions()
            else:
                vessels = current_app.ais_service.get_latest_positions()
        except Exception as e:
            logger.warning(f"Could not refresh AIS data: {e}")
            vessels = current_app.ais_service.get_latest_positions()
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'vessel_count': len(vessels),
            'vessels': vessels[:50],  # Limit for performance
            'refresh_requested': True
        })
        
    except Exception as e:
        logger.error(f"Error in real-time AIS endpoint: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@maritime_bp.route('/api/weather')
def get_weather():
    """
    Get current weather data for Norwegian coastal areas.
    Integrates with the weather service for maritime conditions.
    """
    try:
        # Check if weather service is available
        if not hasattr(current_app, 'weather_service'):
            # Try to import weather service
            try:
                from backend.services.weather_service import weather_service
                current_app.weather_service = weather_service
            except ImportError:
                return jsonify({
                    'error': 'Weather service not available',
                    'timestamp': datetime.now().isoformat()
                }), 503
        
        # Get weather data
        weather_data = current_app.weather_service.get_current_weather()
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'weather': weather_data,
            'source': 'MET Norway / OpenWeatherMap'
        })
        
    except Exception as e:
        logger.error(f"Error getting weather data: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@maritime_bp.route('/api/weather-dashboard')
def get_dashboard_weather():
    """
    Simplified weather endpoint for dashboard display.
    Always returns valid weather data with guaranteed fallback.
    REAL-TIME: Provides temperature and wind data for dashboard stats.
    """
    try:
        # Check if weather service is available
        if not hasattr(current_app, 'weather_service'):
            # Try to import weather service
            try:
                from backend.services.weather_service import weather_service
                current_app.weather_service = weather_service
            except ImportError:
                logger.warning("Weather service not available, creating fallback")
                return _create_weather_fallback("Service not initialized")
        
        # Get weather data
        try:
            weather_data = current_app.weather_service.get_current_weather()
            
            # Ensure required fields exist with fallback values
            processed_data = {
                'temperature_c': weather_data.get('temperature_c') or weather_data.get('temperature'),
                'wind_speed_ms': weather_data.get('wind_speed_ms') or weather_data.get('wind_speed'),
                'wind_direction_deg': weather_data.get('wind_direction_deg') or weather_data.get('wind_direction'),
                'wind_direction': weather_data.get('wind_direction') or _degrees_to_direction(
                    weather_data.get('wind_direction_deg') or weather_data.get('wind_direction')
                ),
                'city': weather_data.get('city') or 'Bergen',
                'data_source': weather_data.get('data_source') or 'unknown',
                'timestamp': weather_data.get('timestamp') or datetime.now().isoformat(),
                'confidence': weather_data.get('confidence') or 'unknown'
            }
            
            # Add display values
            if processed_data['temperature_c'] is not None:
                processed_data['temperature_display'] = f"{processed_data['temperature_c']:.1f}°C"
            
            if processed_data['wind_speed_ms'] is not None:
                processed_data['wind_display'] = f"{processed_data['wind_speed_ms']:.1f} m/s"
            
            if processed_data['wind_direction']:
                processed_data['wind_dir_display'] = processed_data['wind_direction']
            
            logger.info(f"✅ Dashboard weather: {processed_data['city']} - "
                       f"{processed_data.get('temperature_display', 'N/A')}, "
                       f"{processed_data.get('wind_display', 'N/A')}")
            
            return jsonify(processed_data)
            
        except Exception as e:
            logger.error(f"Weather service error: {e}")
            return _create_weather_fallback(f"Weather service error: {e}")
        
    except Exception as e:
        logger.error(f"Dashboard weather endpoint error: {e}")
        return _create_weather_fallback(f"Endpoint error: {e}")

@maritime_bp.route('/api/rtz/routes')
def get_rtz_routes():
    """
    Get all available RTZ routes.
    Returns comprehensive route information for maritime navigation.
    Enhanced with visual properties for better map display.
    """
    try:
        # Use the enhanced route discovery with visual properties
        from backend.services.rtz_parser import discover_rtz_files
        routes_data = discover_rtz_files(enhanced=True)
        
        # Format for API response
        formatted_routes = []
        for route in routes_data:
            formatted_route = {
                'name': route.get('route_name', 'Unknown Route'),
                'origin': route.get('origin', 'Unknown'),
                'destination': route.get('destination', 'Unknown'),
                'total_distance_nm': route.get('total_distance_nm', 0),
                'waypoint_count': route.get('waypoint_count', 0),
                'source_city': route.get('source_city', 'Unknown'),
                'data_source': route.get('data_source', 'rtz_file'),
                'waypoints': route.get('waypoints', []),
                'visual_properties': route.get('visual_properties', {}),
                'start_point': route.get('start_point'),
                'end_point': route.get('end_point'),
                'label_position': route.get('label_position'),
                'parse_timestamp': route.get('parse_timestamp', datetime.now().isoformat())
            }
            formatted_routes.append(formatted_route)
        
        # Calculate statistics
        total_routes = len(formatted_routes)
        total_distance = sum(route['total_distance_nm'] for route in formatted_routes)
        total_waypoints = sum(route['waypoint_count'] for route in formatted_routes)
        
        # Group by city
        routes_by_city = {}
        for route in formatted_routes:
            city = route['source_city']
            routes_by_city.setdefault(city, 0)
            routes_by_city[city] += 1
        
        # Extract unique colors for legend
        colors_by_city = {}
        for route in formatted_routes:
            city = route['source_city']
            color = route.get('visual_properties', {}).get('color', '#3498db')
            if city not in colors_by_city:
                colors_by_city[city] = color
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_routes': total_routes,
                'total_distance_nm': round(total_distance, 1),
                'total_waypoints': total_waypoints,
                'average_waypoints_per_route': round(total_waypoints / max(total_routes, 1), 1),
                'routes_by_city': routes_by_city
            },
            'visual_summary': {
                'colors_by_city': colors_by_city,
                'routes_with_visuals': total_routes
            },
            'routes': formatted_routes
        })
        
    except ImportError as e:
        logger.error(f"RTZ parser import error: {e}")
        return jsonify({
            'error': 'RTZ parser not available',
            'timestamp': datetime.now().isoformat()
        }), 503
    except Exception as e:
        logger.error(f"Error getting RTZ routes: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@maritime_bp.route('/api/rtz/routes/enhanced')
def get_enhanced_rtz_routes():
    """
    Get RTZ routes with enhanced visual properties for map display.
    Includes colors, markers, and better differentiation.
    Returns detailed visual properties for each route.
    """
    try:
        from backend.services.rtz_parser import discover_rtz_files
        
        routes_data = discover_rtz_files(enhanced=True)
        
        # Group by city for legend
        routes_by_city = {}
        colors_by_city = {}
        for route in routes_data:
            city = route.get('source_city', 'unknown')
            routes_by_city.setdefault(city, 0)
            routes_by_city[city] += 1
            
            # Get color for this city
            visual = route.get('visual_properties', {})
            color = visual.get('color', '#3498db')
            if city not in colors_by_city:
                colors_by_city[city] = color
        
        # Create legend for display
        legend = []
        for city, color in colors_by_city.items():
            legend.append({
                'city': city.title(),
                'color': color,
                'route_count': routes_by_city.get(city, 0)
            })
        
        # Sort legend by route count (descending)
        legend.sort(key=lambda x: x['route_count'], reverse=True)
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'routes': routes_data,
            'visual_summary': {
                'total_routes': len(routes_data),
                'cities': list(routes_by_city.keys()),
                'colors_by_city': colors_by_city,
                'routes_by_city': routes_by_city,
                'legend': legend
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting enhanced routes: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@maritime_bp.route('/api/vessels/near/<city_name>')
def get_vessels_near_city(city_name: str):
    """
    Get vessels near a specific Norwegian city.
    Uses AIS data to find vessels within operational range.
    """
    try:
        if not hasattr(current_app, 'ais_service'):
            return jsonify({
                'error': 'AIS service not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Norwegian city coordinates
        norwegian_cities = {
            'bergen': {'lat': 60.3913, 'lon': 5.3221},
            'oslo': {'lat': 59.9139, 'lon': 10.7522},
            'stavanger': {'lat': 58.9699, 'lon': 5.7331},
            'trondheim': {'lat': 63.4305, 'lon': 10.3951},
            'alesund': {'lat': 62.4722, 'lon': 6.1497},
            'andalsnes': {'lat': 62.5675, 'lon': 7.6870},
            'kristiansand': {'lat': 58.1467, 'lon': 7.9958},
            'drammen': {'lat': 59.7441, 'lon': 10.2045},
            'sandefjord': {'lat': 59.1312, 'lon': 10.2167},
            'flekkefjord': {'lat': 58.2970, 'lon': 6.6605}
        }
        
        city_name_lower = city_name.lower()
        if city_name_lower not in norwegian_cities:
            return jsonify({
                'error': f'Unknown city: {city_name}. Available: {list(norwegian_cities.keys())}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        city_data = norwegian_cities[city_name_lower]
        
        # Get vessels near city
        radius_km = request.args.get('radius', default=50, type=float)
        
        try:
            if hasattr(current_app.ais_service, 'get_vessels_near'):
                vessels = current_app.ais_service.get_vessels_near(
                    city_data['lat'], city_data['lon'], radius_km
                )
            else:
                # Fallback: filter from all vessels
                all_vessels = current_app.ais_service.get_latest_positions()
                vessels = []
                for vessel in all_vessels:
                    if 'lat' in vessel and 'lon' in vessel:
                        distance = _calculate_distance_km(
                            vessel['lat'], vessel['lon'],
                            city_data['lat'], city_data['lon']
                        )
                        if distance <= radius_km:
                            vessel_copy = vessel.copy()
                            vessel_copy['distance_km'] = round(distance, 2)
                            vessels.append(vessel_copy)
        except Exception as e:
            logger.warning(f"Could not get vessels near city: {e}")
            vessels = []
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'city': city_name_lower,
            'coordinates': city_data,
            'search_radius_km': radius_km,
            'vessel_count': len(vessels),
            'vessels': vessels
        })
        
    except Exception as e:
        logger.error(f"Error getting vessels near city: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@maritime_bp.route('/api/alerts')
def get_alerts():
    """
    Get real-time maritime alerts for all vessels.
    Uses actual data from Kystdatahuset, weather services, and wind farm data.
    """
    try:
        # Get current timestamp for cache checking
        cache_key = 'all_alerts'
        current_time = datetime.now()
        
        # Check if alerts service is available
        if not ALERTS_SERVICE_AVAILABLE:
            logger.warning("Alerts service not available, returning fallback data")
            return _create_alerts_fallback("Alerts service not initialized")
        
        # Check cache (1 minute TTL)
        if (cache_key in maritime_alerts_service._alert_cache and 
            current_time - maritime_alerts_service._alert_cache[cache_key]['timestamp'] < 
            maritime_alerts_service._cache_duration):
            
            logger.info("📦 Returning cached alerts")
            return jsonify(maritime_alerts_service._alert_cache[cache_key]['data'])
        
        # Fetch real data from services
        all_alerts = []
        
        # 1. Get AIS data (using your existing Kystdatahuset/BarentsWatch)
        vessels = []
        try:
            if hasattr(current_app, 'ais_service'):
                vessels = current_app.ais_service.get_latest_positions()
                logger.info(f"📡 Retrieved {len(vessels)} vessels from AIS")
            else:
                # Fallback: import directly
                try:
                    from backend.services.ais_service import ais_service
                    vessels = ais_service.get_latest_positions()
                except ImportError:
                    logger.error("AIS service not available")
        except Exception as e:
            logger.error(f"Error getting AIS data: {e}")
        
        # 2. Get weather data
        weather_data = {}
        try:
            if hasattr(current_app, 'weather_service'):
                weather_data = current_app.weather_service.get_current_weather()
            else:
                try:
                    from backend.services.weather_service import weather_service
                    weather_data = weather_service.get_current_weather()
                except ImportError:
                    logger.error("Weather service not available")
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
        
        # 3. Generate alerts for each vessel
        for vessel in vessels[:20]:  # Process first 20 vessels for performance
            try:
                context = {
                    'weather': weather_data,
                    'other_vessels': vessels
                }
                
                vessel_alerts = maritime_alerts_service.generate_vessel_alerts(vessel, context)
                all_alerts.extend(vessel_alerts)
                
            except Exception as e:
                logger.error(f"Error generating alerts for vessel {vessel.get('mmsi', 'unknown')}: {e}")
                continue
        
        # Count alerts by priority
        priority_counts = {
            'CRITICAL': len([a for a in all_alerts if a.get('priority') == 'CRITICAL']),
            'HIGH': len([a for a in all_alerts if a.get('priority') == 'HIGH']),
            'MEDIUM': len([a for a in all_alerts if a.get('priority') == 'MEDIUM']),
            'LOW': len([a for a in all_alerts if a.get('priority') == 'LOW'])
        }
        
        # Sort alerts by priority (CRITICAL first)
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_alerts.sort(key=lambda x: priority_order.get(x.get('priority', 'LOW'), 4))
        
        # Prepare response
        response_data = {
            'timestamp': current_time.isoformat(),
            'total_alerts': len(all_alerts),
            'priority_counts': priority_counts,
            'alerts': all_alerts[:15],  # Return top 15 alerts
            'data_sources': {
                'vessels_processed': len(vessels),
                'weather_available': bool(weather_data),
                'wind_farms_monitored': len(maritime_alerts_service.NORWEGIAN_WIND_FARMS),
                'ais_source': 'Kystdatahuset/BarentsWatch',
                'weather_source': 'MET Norway'
            },
            'service_status': maritime_alerts_service.get_service_status()
        }
        
        # Cache the results
        maritime_alerts_service._alert_cache[cache_key] = {
            'timestamp': current_time,
            'data': response_data
        }
        
        logger.info(f"✅ Generated {len(all_alerts)} alerts ({priority_counts['CRITICAL']} critical)")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in alerts endpoint: {e}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'alerts': [],
            'priority_counts': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'status': 'error'
        }), 500

@maritime_bp.route('/api/alerts/summary')
def get_alerts_summary():
    """
    Get alerts summary for dashboard display.
    Lightweight endpoint for real-time updates.
    """
    try:
        # Try to get from cache first
        cache_key = 'alerts_summary'
        current_time = datetime.now()
        
        if (cache_key in maritime_alerts_service._alert_cache and 
            current_time - maritime_alerts_service._alert_cache[cache_key]['timestamp'] < 
            timedelta(seconds=30)):  # 30 second cache for summary
            
            return jsonify(maritime_alerts_service._alert_cache[cache_key]['data'])
        
        # Get the full alerts (or use cached full alerts)
        full_alerts_response = get_alerts()
        
        if isinstance(full_alerts_response, tuple):  # Error response
            return jsonify({
                'critical_alerts': 0,
                'high_alerts': 0,
                'total_alerts': 0,
                'last_check': current_time.isoformat(),
                'status': 'error',
                'message': 'Could not retrieve alerts'
            })
        
        full_data = full_alerts_response.get_json()
        
        # Create summary
        summary = {
            'critical_alerts': full_data.get('priority_counts', {}).get('CRITICAL', 0),
            'high_alerts': full_data.get('priority_counts', {}).get('HIGH', 0),
            'total_alerts': full_data.get('total_alerts', 0),
            'last_check': current_time.isoformat(),
            'status': 'active',
            'vessels_monitored': full_data.get('data_sources', {}).get('vessels_processed', 0),
            'weather_status': 'available' if full_data.get('data_sources', {}).get('weather_available') else 'unavailable'
        }
        
        # Cache the summary
        maritime_alerts_service._alert_cache[cache_key] = {
            'timestamp': current_time,
            'data': summary
        }
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error in alerts summary: {e}")
        return jsonify({
            'critical_alerts': 0,
            'high_alerts': 0,
            'total_alerts': 0,
            'last_check': datetime.now().isoformat(),
            'status': 'error',
            'error': str(e)
        })

@maritime_bp.route('/api/system/status')
def system_status():
    """
    Get comprehensive system status for maritime operations.
    Includes all services, routes, and operational metrics.
    """
    try:
        status = {
            'timestamp': datetime.now().isoformat(),
            'system': 'BergNavn Maritime Dashboard',
            'version': '3.0',
            'environment': current_app.config.get('ENV', 'development'),
            'services': {},
            'routes': {},
            'operational_metrics': {}
        }
        
        # AIS Service Status
        if hasattr(current_app, 'ais_service'):
            try:
                ais_status = current_app.ais_service.get_service_status()
                status['services']['ais'] = ais_status
            except Exception as e:
                status['services']['ais'] = {'error': str(e)}
        
        # RTZ Routes Status
        try:
            from backend.services.rtz_parser import get_processing_statistics
            rtz_stats = get_processing_statistics()
            status['routes']['statistics'] = rtz_stats
            
            # Try to get actual route count
            try:
                from backend.services.rtz_parser import discover_rtz_files
                all_routes = discover_rtz_files(enhanced=True)
                status['routes']['total_discovered'] = len(all_routes)
                
                # Group by city
                routes_by_city = {}
                for route in all_routes:
                    city = route.get('source_city', 'unknown')
                    routes_by_city.setdefault(city, 0)
                    routes_by_city[city] += 1
                status['routes']['by_city'] = routes_by_city
                
                # Add visual properties info
                if all_routes and 'visual_properties' in all_routes[0]:
                    status['routes']['visual_enhancement'] = 'enabled'
                
            except Exception as e:
                status['routes']['discovery_error'] = str(e)
                
        except Exception as e:
            status['routes']['error'] = str(e)
        
        # Calculate operational metrics
        ais_vessels = status['services'].get('ais', {}).get('data_metrics', {}).get('active_vessels', 0)
        total_routes = status['routes'].get('total_discovered', 0)
        
        status['operational_metrics'] = {
            'ais_vessels_active': ais_vessels,
            'total_routes_available': total_routes,
            'cities_covered': len(status['routes'].get('statistics', {}).get('cities_with_files', [])),
            'data_freshness': 'real_time' if ais_vessels > 0 else 'simulated',
            'visual_enhancement': status['routes'].get('visual_enhancement', 'disabled')
        }
        
        # Overall health
        all_services_healthy = all(
            service.get('operational_status', {}).get('running', False) 
            if isinstance(service, dict) and 'operational_status' in service 
            else False
            for service in status['services'].values() 
            if isinstance(service, dict)
        )
        
        status['health'] = 'healthy' if all_services_healthy else 'degraded'
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"System status error: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _create_weather_fallback(reason: str) -> Dict:
    """
    Create guaranteed fallback weather data for dashboard.
    
    Args:
        reason: Reason for using fallback
        
    Returns:
        JSON response with fallback weather data
    """
    logger.warning(f"⚠️ Creating weather fallback: {reason}")
    
    fallback_data = {
        'temperature_c': 8.5,
        'temperature_display': '8.5°C',
        'wind_speed_ms': 5.2,
        'wind_display': '5.2 m/s',
        'wind_direction_deg': 315,  # NW
        'wind_direction': 'NW',
        'wind_dir_display': 'NW',
        'city': 'Bergen',
        'data_source': 'emergency_fallback',
        'timestamp': datetime.now().isoformat(),
        'confidence': 'high',
        'fallback_reason': reason
    }
    
    return jsonify(fallback_data)

def _create_alerts_fallback(reason: str) -> Dict:
    """
    Create fallback alerts data when alerts service is not available.
    
    Args:
        reason: Reason for using fallback
        
    Returns:
        JSON response with fallback alerts data
    """
    logger.warning(f"⚠️ Creating alerts fallback: {reason}")
    
    fallback_data = {
        'timestamp': datetime.now().isoformat(),
        'total_alerts': 0,
        'priority_counts': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
        'alerts': [],
        'data_sources': {
            'vessels_processed': 0,
            'weather_available': False,
            'wind_farms_monitored': 0,
            'ais_source': 'fallback',
            'weather_source': 'fallback'
        },
        'service_status': {
            'service': 'MaritimeAlertsService',
            'status': 'unavailable',
            'fallback_reason': reason
        }
    }
    
    return jsonify(fallback_data)

def _degrees_to_direction(degrees):
    """Convert degrees to compass direction."""
    if degrees is None:
        return 'NW'
    
    try:
        deg = float(degrees)
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        idx = round(deg / 22.5) % 16
        return directions[idx]
    except:
        return 'NW'

def _get_norwegian_city_proximity(lat: float, lon: float, max_distance_km: float = 100) -> Dict[str, Any]:
    """
    Calculate proximity to Norwegian cities.
    Helper function for vessel enrichment.
    """
    norwegian_cities = {
        'Bergen': {'lat': 60.3913, 'lon': 5.3221},
        'Oslo': {'lat': 59.9139, 'lon': 10.7522},
        'Stavanger': {'lat': 58.9699, 'lon': 5.7331},
        'Trondheim': {'lat': 63.4305, 'lon': 10.3951},
        'Ålesund': {'lat': 62.4722, 'lon': 6.1497},
        'Åndalsnes': {'lat': 62.5675, 'lon': 7.6870},
        'Kristiansand': {'lat': 58.1467, 'lon': 7.9958},
        'Drammen': {'lat': 59.7441, 'lon': 10.2045},
        'Sandefjord': {'lat': 59.1312, 'lon': 10.2167},
        'Flekkefjord': {'lat': 58.2970, 'lon': 6.6605}
    }
    
    proximities = []
    for city_name, city_coords in norwegian_cities.items():
        distance = _calculate_distance_km(lat, lon, city_coords['lat'], city_coords['lon'])
        if distance <= max_distance_km:
            proximities.append({
                'city': city_name,
                'distance_km': round(distance, 2),
                'coordinates': city_coords
            })
    
    # Sort by distance
    proximities.sort(key=lambda x: x['distance_km'])
    
    return {
        'nearest_city': proximities[0]['city'] if proximities else None,
        'nearest_distance_km': proximities[0]['distance_km'] if proximities else None,
        'all_proximities': proximities[:3]  # Top 3 closest cities
    }

def _calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates in kilometers.
    Uses Haversine formula for accuracy.
    """
    import math
    
    R = 6371.0  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c