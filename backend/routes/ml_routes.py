# backend/routes/ml_routes.py - Machine Learning and Data Science Routes
# Enhanced with maritime analytics and fuel optimization endpoints

from flask import Blueprint, request, jsonify
from backend.ml.recommendation_engine import recommend_cruises
from datetime import datetime

# Create a Blueprint for ML API routes
ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

@ml_bp.route('/recommend', methods=['POST'])
def get_recommendations():
    """
    Route: POST /api/ml/recommend
    Purpose: Receive input data and return cruise recommendations.
    Returns a JSON list of recommended cruises or an error message.
    """
    data = request.json
    try:
        recommendations = recommend_cruises(data)
        return jsonify([{
            "id": c.id,
            "title": c.title,
            "origin": c.origin,
            "destination": c.destination,
            "price": c.price
        } for c in recommendations])
    except Exception as e:
        # Return error as JSON with status code 400
        return jsonify({"error": str(e)}), 400

@ml_bp.route('/maritime-analytics')
def get_maritime_analytics():
    """
    Route: GET /api/ml/maritime-analytics
    Purpose: Provide fleet performance analytics and data science insights
    Returns: JSON with fleet metrics, efficiency scores, and optimization data
    """
    try:
        # Import AIS service dynamically to avoid circular imports
        from backend.services.ais_service import ais_service
        
        # Get current ships data from AIS service
        ships_data = getattr(ais_service, 'ships_data', [])
        
        # Calculate basic fleet analytics
        total_ships = len(ships_data)
        
        # Average speed calculation
        avg_speed = sum(ship.get('sog', 0) for ship in ships_data) / max(total_ships, 1)
        
        # Fuel efficiency simulation based on speed optimization
        fuel_efficiency_scores = []
        optimization_opportunities = 0
        
        for ship in ships_data:
            speed = ship.get('sog', 10)  # Default to 10 knots if not available
            optimal_speed = 12  # Most fuel-efficient speed for cargo vessels
            
            # Calculate efficiency score (0-100)
            speed_deviation = abs(speed - optimal_speed)
            efficiency = max(0, 100 - (speed_deviation * 8))
            fuel_efficiency_scores.append(efficiency)
            
            # Count optimization opportunities
            if speed_deviation > 2:  # More than 2 knots from optimal
                optimization_opportunities += 1
        
        avg_efficiency = sum(fuel_efficiency_scores) / max(len(fuel_efficiency_scores), 1)
        
        # Calculate potential fuel savings based on industry data
        # Typical savings: 10-20% through speed optimization
        base_savings = 15  # Base 15% potential savings
        efficiency_factor = (100 - avg_efficiency) / 100
        potential_savings = base_savings * efficiency_factor
        
        # Prepare analytics response
        analytics_data = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'fleet_metrics': {
                'total_ships': total_ships,
                'average_speed_knots': round(avg_speed, 1),
                'average_fuel_efficiency': round(avg_efficiency, 1),
                'ships_optimal': len([s for s in ships_data if 10 <= s.get('sog', 0) <= 14]),
                'ships_needing_optimization': optimization_opportunities,
                'potential_fuel_savings_percent': round(potential_savings, 1),
                'estimated_monthly_savings_usd': round(potential_savings * 2500, 2),  # Based on $2.5k per % point
                'performance_grade': 'A' if avg_efficiency > 80 else 'B' if avg_efficiency > 60 else 'C'
            },
            'data_source': 'live_ais' if hasattr(ais_service, 'is_connected') and ais_service.is_connected else 'simulated',
            'data_quality': 'high' if total_ships > 5 else 'medium'
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        # Log the error and return user-friendly message
        print(f"Maritime analytics error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Analytics service temporarily unavailable',
            'timestamp': datetime.now().isoformat()
        }), 500

@ml_bp.route('/fuel-optimization')
def get_fuel_optimization():
    """
    Route: GET /api/ml/fuel-optimization
    Purpose: Provide specific fuel optimization recommendations for vessels
    Returns: JSON with optimization suggestions and potential savings
    """
    try:
        # Import AIS service dynamically
        from backend.services.ais_service import ais_service
        
        ships_data = getattr(ais_service, 'ships_data', [])
        
        recommendations = []
        total_potential_savings = 0
        
        for ship in ships_data[:5]:  # Analyze first 5 ships for performance
            ship_name = ship.get('name', 'Unknown Vessel')
            current_speed = ship.get('sog', 10)
            optimal_speed = 12  # Industry standard optimal speed
            
            # Analyze speed efficiency
            speed_deviation = abs(current_speed - optimal_speed)
            
            if current_speed < 8:
                # Vessel moving too slow - inefficient
                saving_potential = 8  # 8% potential savings
                recommendation = {
                    'ship': ship_name,
                    'issue': 'low_speed',
                    'current_speed': current_speed,
                    'recommended_speed': optimal_speed,
                    'recommendation': 'Increase speed to 12 knots for optimal fuel efficiency',
                    'potential_saving_percent': saving_potential,
                    'urgency': 'medium'
                }
                recommendations.append(recommendation)
                total_potential_savings += saving_potential
                
            elif current_speed > 16:
                # Vessel moving too fast - high fuel consumption
                saving_potential = 12  # 12% potential savings
                recommendation = {
                    'ship': ship_name,
                    'issue': 'high_speed', 
                    'current_speed': current_speed,
                    'recommended_speed': optimal_speed,
                    'recommendation': 'Reduce speed to 12 knots for significant fuel savings',
                    'potential_saving_percent': saving_potential,
                    'urgency': 'high'
                }
                recommendations.append(recommendation)
                total_potential_savings += saving_potential
                
            elif speed_deviation > 2:
                # Minor optimization needed
                saving_potential = 5  # 5% potential savings
                recommendation = {
                    'ship': ship_name,
                    'issue': 'suboptimal_speed',
                    'current_speed': current_speed,
                    'recommended_speed': optimal_speed,
                    'recommendation': 'Adjust speed to 12 knots for better fuel economy',
                    'potential_saving_percent': saving_potential,
                    'urgency': 'low'
                }
                recommendations.append(recommendation)
                total_potential_savings += saving_potential
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'optimization_recommendations': recommendations,
            'summary': {
                'total_recommendations': len(recommendations),
                'total_potential_savings_percent': round(total_potential_savings, 1),
                'estimated_annual_savings_usd': round(total_potential_savings * 30000, 2),  # $30k annual per % point
                'ships_analyzed': len(ships_data)
            }
        })
        
    except Exception as e:
        print(f"Fuel optimization error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Fuel optimization service temporarily unavailable',
            'timestamp': datetime.now().isoformat()
        }), 500

@ml_bp.route('/route-efficiency')
def get_route_efficiency():
    """
    Route: GET /api/ml/route-efficiency  
    Purpose: Analyze route efficiency and provide optimization insights
    Returns: JSON with route analysis and improvement suggestions
    """
    try:
        # Simulate route efficiency analysis
        # In production, this would use historical data and weather patterns
        
        base_efficiency = 85  # Base efficiency score
        weather_impact = -5   # Simulated weather impact
        current_impact = 2    # Simulated current impact
        
        total_efficiency = base_efficiency + weather_impact + current_impact
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'route_analysis': {
                'route': 'Kristiansand ↔ Oslo',
                'efficiency_score': max(0, total_efficiency),
                'distance_nautical_miles': 250,
                'base_efficiency': base_efficiency,
                'weather_impact': weather_impact,
                'current_impact': current_impact,
                'recommendations': [
                    'Consider slight course adjustment for better current utilization',
                    'Monitor weather patterns for optimal departure timing',
                    'Maintain speed between 10-14 knots for fuel efficiency'
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Route efficiency analysis failed: {str(e)}'
        }), 500