# backend/routes/maritime_routes.py - Maritime routes for BergNavn application
# Updated with MET Norway integration, AIS data science, and real-time analytics
from flask import Blueprint, render_template, request, jsonify, current_app
import requests
import os
import time
from datetime import datetime
from backend.utils.translations import translate  # Translation utility

# Use unique blueprint name to avoid conflicts
maritime_bp = Blueprint('maritime_bp', __name__)

@maritime_bp.route('/')
def maritime_dashboard():
    """
    Maritime Dashboard - Real-time tracking for Kristiansand ↔ Oslo route
    Enhanced with Data Science analytics and live AIS data
    """
    # Get language from request parameters or use default
    lang = request.args.get('lang', 'en')
    
    # Ensure valid language
    if lang not in ['en', 'no']:
        lang = 'en'
    
    return render_template('maritime_dashboard.html', lang=lang)

@maritime_bp.route('/api/weather-pro')
def get_maritime_weather_pro():
    """
    ENHANCED: Maritime weather data with MET Norway primary + OpenWeather fallback
    Provides reliable weather data for route optimization and fuel calculations
    """
    try:
        lat = request.args.get('lat', 58.1467, type=float)  # Kristiansand default
        lon = request.args.get('lon', 8.0980, type=float)
        location_name = request.args.get('location', 'Kristiansand')
        
        # PRIMARY: MET Norway API - Most reliable for maritime data
        met_headers = {
            'User-Agent': 'BergNavnMaritime/3.0 (framgangsrik747@gmail.com)',
            'Accept': 'application/json'
        }
        met_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
        
        try:
            met_response = requests.get(met_url, headers=met_headers, timeout=10)
            
            if met_response.status_code == 200:
                met_data = met_response.json()
                current_weather = met_data['properties']['timeseries'][0]['data']['instant']['details']
                
                weather_info = {
                    'status': 'success',
                    'source': 'MET Norway',
                    'data': {
                        'temperature': current_weather.get('air_temperature', 0),
                        'wind_speed': current_weather.get('wind_speed', 0),
                        'wind_direction': current_weather.get('wind_direction', 0),
                        'wind_gust': current_weather.get('wind_speed_of_gust', 0),
                        'humidity': current_weather.get('relative_humidity', 0),
                        'pressure': current_weather.get('air_pressure_at_sea_level', 0),
                        'condition': 'Maritime data',  # MET Norway doesn't provide descriptions like OpenWeather
                        'icon': '🌊',  # Maritime-specific icon
                        'location': location_name,
                        'timestamp': datetime.now().isoformat(),
                        'data_quality': 'high'  # For data science analytics
                    }
                }
                return jsonify(weather_info)
                
        except requests.exceptions.Timeout:
            print("MET Norway timeout, falling back to OpenWeather")
        except Exception as e:
            print(f"MET Norway error: {e}, falling back to OpenWeather")

        # FALLBACK: OpenWeather API
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'No weather API available - MET Norway failed and OpenWeather key missing'
            }), 500
            
        ow_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        ow_response = requests.get(ow_url, timeout=10)
        
        if ow_response.status_code == 200:
            data = ow_response.json()
            weather_info = {
                'status': 'success',
                'source': 'OpenWeather (fallback)',
                'data': {
                    'temperature': data['main']['temp'],
                    'wind_speed': data['wind']['speed'],
                    'wind_direction': data['wind'].get('deg', 0),
                    'wind_gust': data['wind'].get('gust', data['wind']['speed'] * 1.3),
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'condition': data['weather'][0]['description'],
                    'icon': map_weather_icon(data['weather'][0]['main']),
                    'location': location_name,
                    'timestamp': datetime.now().isoformat(),
                    'data_quality': 'medium'  # Lower quality for fallback
                }
            }
            return jsonify(weather_info)
        else:
            return jsonify({
                'status': 'error',
                'message': f'All weather APIs failed. Last error: {ow_response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Weather service unavailable: {str(e)}'
        }), 500

@maritime_bp.route('/api/ships-live')
def get_live_ships():
    """
    ENHANCED: Live AIS data with Data Science enrichment
    Provides real-time ship positions with fuel efficiency analytics
    """
    try:
        # Get ships from AIS service (if available) or use enhanced mock data
        ships_data = []
        
        # Try to get real AIS data first
        if hasattr(current_app, 'ais_service') and current_app.ais_service.is_connected:
            ships_data = current_app.ais_service.ships_data
        else:
            # Enhanced mock data with realistic maritime patterns
            ships_data = generate_enhanced_mock_ships()
        
        # Data Science: Enrich ships with analytics
        enriched_ships = []
        for ship in ships_data:
            enriched_ship = {
                **ship,
                'data_science_metrics': calculate_ship_metrics(ship)
            }
            enriched_ships.append(enriched_ship)
        
        # Fleet-level analytics
        fleet_analytics = calculate_fleet_analytics(enriched_ships)
        
        return jsonify({
            'status': 'live' if hasattr(current_app, 'ais_service') and current_app.ais_service.is_connected else 'enhanced_simulation',
            'ships_count': len(enriched_ships),
            'ships': enriched_ships,
            'fleet_analytics': fleet_analytics,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'Kystverket AIS' if hasattr(current_app, 'ais_service') and current_app.ais_service.is_connected else 'Enhanced simulation'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ships data error: {str(e)}'
        }), 500

@maritime_bp.route('/api/analytics/fuel-optimization')
def get_fuel_optimization():
    """
    DATA SCIENCE: Fuel optimization analytics based on real-time data
    Calculates potential fuel savings and optimization recommendations
    """
    try:
        # Get current ships and weather data
        ships_response = get_live_ships()
        ships_data = ships_response.get_json()['ships'] if ships_response.status_code == 200 else []
        
        weather_response = get_maritime_weather_pro()
        weather_data = weather_response.get_json()['data'] if weather_response.status_code == 200 else {}
        
        # Calculate optimization potential
        optimization_results = calculate_fuel_optimization(ships_data, weather_data)
        
        return jsonify({
            'status': 'success',
            'optimization': optimization_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Fuel optimization error: {str(e)}'
        }), 500

@maritime_bp.route('/api/alerts')
def get_system_alerts():
    """
    ALERT SYSTEM: Real-time alerts based on data analytics
    Provides operational alerts for fleet management
    """
    try:
        ships_response = get_live_ships()
        ships_data = ships_response.get_json()['ships'] if ships_response.status_code == 200 else []
        
        weather_response = get_maritime_weather_pro()
        weather_data = weather_response.get_json()['data'] if weather_response.status_code == 200 else {}
        
        alerts = generate_system_alerts(ships_data, weather_data)
        
        return jsonify({
            'status': 'success',
            'alerts': alerts,
            'alert_count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Alerts system error: {str(e)}'
        }), 500

@maritime_bp.route('/api/route/eta-enhanced')
def calculate_enhanced_eta():
    """
    ENHANCED: ETA calculation with weather and performance factors
    Uses Data Science for accurate arrival time predictions
    """
    try:
        # Get real-time data for accurate calculation
        weather_response = get_maritime_weather_pro()
        weather_data = weather_response.get_json()['data'] if weather_response.status_code == 200 else {}
        
        # Base route parameters
        base_distance = 250  # nautical miles
        base_speed = 12  # knots
        
        # Enhanced calculation with weather factors
        wind_impact = calculate_wind_impact(weather_data)
        current_impact = calculate_current_impact()
        performance_factor = calculate_performance_factor()
        
        total_impact = 1.0 + wind_impact + current_impact + performance_factor
        adjusted_eta = (base_distance / base_speed) * total_impact
        
        return jsonify({
            'status': 'success',
            'data': {
                'base_eta_hours': round(base_distance / base_speed, 1),
                'adjusted_eta_hours': round(adjusted_eta, 1),
                'distance_nautical_miles': base_distance,
                'average_speed_knots': base_speed,
                'weather_impact_percent': round(wind_impact * 100, 1),
                'current_impact_percent': round(current_impact * 100, 1),
                'performance_impact_percent': round(performance_factor * 100, 1),
                'total_impact_percent': round((total_impact - 1.0) * 100, 1),
                'confidence_score': 0.85,  # Data science confidence metric
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Enhanced ETA calculation error: {str(e)}'
        }), 500

# =============================================================================
# DATA SCIENCE HELPER FUNCTIONS
# =============================================================================

def calculate_ship_metrics(ship):
    """
    Calculate Data Science metrics for individual ships
    Returns fuel efficiency, schedule adherence, and optimization scores
    """
    speed = ship.get('sog', 10)
    optimal_speed = 12  # Knots - most fuel-efficient speed
    
    # Fuel efficiency score (0-100)
    speed_deviation = abs(speed - optimal_speed)
    fuel_efficiency = max(0, 100 - (speed_deviation * 8))
    
    # Schedule adherence (based on ETA consistency)
    schedule_adherence = 85 if 10 <= speed <= 14 else 60
    
    # Optimization potential (0-100)
    optimization_potential = min(100, speed_deviation * 12)
    
    return {
        'fuel_efficiency_score': round(fuel_efficiency),
        'schedule_adherence_score': schedule_adherence,
        'optimization_potential': round(optimization_potential),
        'recommended_speed': optimal_speed,
        'current_vs_optimal': round(speed - optimal_speed, 1)
    }

def calculate_fleet_analytics(ships):
    """
    Calculate fleet-level analytics for performance monitoring
    """
    if not ships:
        return {}
    
    total_ships = len(ships)
    avg_fuel_efficiency = sum(s['data_science_metrics']['fuel_efficiency_score'] for s in ships) / total_ships
    avg_optimization_potential = sum(s['data_science_metrics']['optimization_potential'] for s in ships) / total_ships
    
    # Calculate ships needing optimization
    ships_needing_optimization = len([s for s in ships if s['data_science_metrics']['optimization_potential'] > 30])
    
    # Estimated fuel savings (simplified model)
    potential_fuel_savings = avg_optimization_potential * 0.15  # 0.15% per point
    
    return {
        'total_ships': total_ships,
        'average_fuel_efficiency': round(avg_fuel_efficiency, 1),
        'average_optimization_potential': round(avg_optimization_potential, 1),
        'ships_needing_optimization': ships_needing_optimization,
        'potential_fuel_savings_percent': round(potential_fuel_savings, 1),
        'estimated_monthly_savings_usd': round(potential_fuel_savings * 5000, 2),  # Based on $5k monthly fuel
        'performance_grade': 'A' if avg_fuel_efficiency > 80 else 'B' if avg_fuel_efficiency > 60 else 'C'
    }

def calculate_fuel_optimization(ships, weather_data):
    """
    Calculate fuel optimization recommendations based on current conditions
    """
    optimization_opportunities = []
    total_potential_savings = 0
    
    for ship in ships:
        metrics = ship.get('data_science_metrics', {})
        potential_saving = metrics.get('optimization_potential', 0) * 0.12  # 0.12% fuel saving per point
        
        if potential_saving > 5:  # Only show meaningful optimizations
            optimization_opportunities.append({
                'ship_name': ship.get('name', 'Unknown'),
                'current_speed': ship.get('sog', 0),
                'recommended_speed': metrics.get('recommended_speed', 12),
                'potential_saving_percent': round(potential_saving, 1),
                'action': 'Adjust speed' if ship.get('sog', 0) > metrics.get('recommended_speed', 12) else 'Maintain course'
            })
            total_potential_savings += potential_saving
    
    return {
        'optimization_opportunities': optimization_opportunities,
        'total_potential_savings_percent': round(total_potential_savings, 1),
        'opportunities_count': len(optimization_opportunities),
        'estimated_impact': 'High' if total_potential_savings > 10 else 'Medium' if total_potential_savings > 5 else 'Low'
    }

def generate_system_alerts(ships, weather_data):
    """
    Generate operational alerts based on real-time data analysis
    """
    alerts = []
    
    # Weather alerts
    if weather_data.get('wind_speed', 0) > 15:
        alerts.append({
            'type': 'weather_alert',
            'priority': 'high',
            'message': f"High winds: {weather_data['wind_speed']} m/s - Consider route adjustment",
            'timestamp': datetime.now().isoformat()
        })
    
    # Ship performance alerts
    for ship in ships:
        metrics = ship.get('data_science_metrics', {})
        
        if metrics.get('fuel_efficiency_score', 0) < 60:
            alerts.append({
                'type': 'performance_alert',
                'priority': 'medium',
                'ship': ship.get('name', 'Unknown'),
                'message': f"Low fuel efficiency: {metrics['fuel_efficiency_score']}/100 - Speed adjustment recommended",
                'timestamp': datetime.now().isoformat()
            })
        
        if ship.get('sog', 0) < 5:
            alerts.append({
                'type': 'operational_alert',
                'priority': 'low',
                'ship': ship.get('name', 'Unknown'),
                'message': f"Very low speed: {ship['sog']} knots - Check for issues",
                'timestamp': datetime.now().isoformat()
            })
    
    return alerts

def generate_enhanced_mock_ships():
    """
    Generate realistic mock ship data for development and testing
    Simulates real AIS patterns for Kristiansand-Oslo route
    """
    base_time = datetime.now()
    ships = []
    
    route_variants = [
        {'name': 'VICTORIA WILSON', 'mmsi': '257158400', 'type': 'Cargo', 'base_speed': 14.2},
        {'name': 'KRISTIANSAND FJORD', 'mmsi': '258225000', 'type': 'Passenger', 'base_speed': 8.5},
        {'name': 'OSLO CARRIER', 'mmsi': '259187300', 'type': 'Container', 'base_speed': 16.8},
        {'name': 'SKAGERRAK TRADER', 'mmsi': '257894500', 'type': 'Tanker', 'base_speed': 11.3}
    ]
    
    for i, variant in enumerate(route_variants):
        # Simulate progressive movement along route
        progress = ((base_time.minute + (i * 15)) % 60) / 60.0
        
        if i % 2 == 0:  # Kristiansand to Oslo
            start_lat, start_lon = 58.1467, 8.0980
            end_lat, end_lon = 59.9139, 10.7522
            destination = 'OSLO'
        else:  # Oslo to Kristiansand
            start_lat, start_lon = 59.9139, 10.7522
            end_lat, end_lon = 58.1467, 8.0980
            destination = 'KRISTIANSAND'
        
        current_lat = start_lat + (end_lat - start_lat) * progress
        current_lon = start_lon + (end_lon - start_lon) * progress
        
        # Add some realistic variation
        current_lat += (i * 0.01) - 0.02
        current_lon += ((i * 0.015) - 0.03)
        
        ship = {
            'mmsi': variant['mmsi'],
            'name': variant['name'],
            'type': variant['type'],
            'lat': round(current_lat, 4),
            'lon': round(current_lon, 4),
            'sog': variant['base_speed'] + (i * 0.3) - 0.6,  # Speed variation
            'cog': 45 + (i * 30),  # Course variation
            'heading': 50 + (i * 40),
            'destination': destination,
            'timestamp': base_time.isoformat(),
            'status': 'Underway'
        }
        ships.append(ship)
    
    return ships

def calculate_wind_impact(weather_data):
    """
    Calculate wind impact on voyage time
    Positive = favorable wind, Negative = adverse wind
    """
    wind_speed = weather_data.get('wind_speed', 0)
    wind_direction = weather_data.get('wind_direction', 0)
    
    # Simplified model: headwind increases time, tailwind decreases
    # Assume route direction ~45 degrees (NE from Kristiansand to Oslo)
    route_direction = 45
    wind_relative = abs(wind_direction - route_direction)
    
    if wind_relative < 90:  # Headwind
        return wind_speed * 0.015  # 1.5% time increase per m/s headwind
    else:  # Tailwind
        return -wind_speed * 0.01  # 1% time decrease per m/s tailwind

def calculate_current_impact():
    """
    Calculate ocean current impact (simplified for demonstration)
    In production, this would use real current data
    """
    return 0.02  # 2% typical current impact

def calculate_performance_factor():
    """
    Calculate vessel performance factor based on age/type
    Simplified for demonstration
    """
    return -0.01  # 1% improvement for modern vessels

def map_weather_icon(condition):
    """
    Map OpenWeather condition to appropriate emoji icon
    """
    icon_map = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Fog': '🌫️',
        'Smoke': '💨',
        'Dust': '💨',
        'Sand': '💨',
        'Ash': '💨',
        'Squall': '💨',
        'Tornado': '🌪️'
    }
    return icon_map.get(condition, '🌡️')  # Default icon for unknown conditions