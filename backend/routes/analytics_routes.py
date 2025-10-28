# backend/routes/analytics_routes.py
"""
ANALYTICS ROUTES - endpoints for business intelligence dashboards
Provides fleet performance analytics and methanol transition analysis
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from backend.ml.enhanced_fuel_optimizer import EnhancedFuelOptimizer

analytics_bp = Blueprint('analytics_bp', __name__)
optimizer = EnhancedFuelOptimizer()

def get_live_ships_data():
    """
    Mock function to get live ships data
    In production, this would connect to AIS service
    """
    # This would be replaced with actual AIS service call
    return [
        {
            'mmsi': '257158400',
            'name': 'VICTORIA WILSON', 
            'type': 'container',
            'sog': 14.2,
            'lat': 58.1467,
            'lon': 8.0980
        },
        {
            'mmsi': '258225000',
            'name': 'KRISTIANSAND FJORD',
            'type': 'passenger', 
            'sog': 8.5,
            'lat': 58.5,
            'lon': 9.0
        },
        {
            'mmsi': '259187300',
            'name': 'OSLO CARRIER',
            'type': 'tanker',
            'sog': 11.3,
            'lat': 59.0,
            'lon': 10.0
        }
    ]

def get_weather_data():
    """
    Mock function to get weather data
    In production, this would connect to MET Norway service
    """
    return {
        'wind_speed': 8.5,
        'wind_direction': 45,
        'wave_height': 1.2,
        'temperature': 9.0
    }

@analytics_bp.route('/api/analytics/fleet-performance')
def get_fleet_performance():
    """
    Fleet-wide performance analytics for business intelligence
    Returns comprehensive fleet metrics and optimization opportunities
    """
    try:
        # Get data from AIS service
        ships_data = get_live_ships_data()
        
        fleet_analytics = {
            'total_ships': len(ships_data),
            'average_efficiency': 0,
            'total_fuel_savings_potential': 0,
            'ships_optimized': 0,
            'performance_breakdown': {
                'excellent': 0,  # 90-100%
                'good': 0,       # 70-89%  
                'fair': 0,       # 50-69%
                'poor': 0        # <50%
            },
            'optimization_opportunities': []
        }
        
        total_efficiency = 0
        total_savings_potential = 0
        
        for ship in ships_data:
            weather_data = get_weather_data()
            performance = optimizer.calculate_optimal_speed_profile(ship, weather_data)
            total_efficiency += performance.efficiency_score
            
            # Calculate savings potential
            savings_potential = (100 - performance.efficiency_score) * 0.15  # 0.15% per efficiency point
            total_savings_potential += savings_potential
            
            # Categorize performance
            if performance.efficiency_score >= 90:
                fleet_analytics['performance_breakdown']['excellent'] += 1
                fleet_analytics['ships_optimized'] += 1
            elif performance.efficiency_score >= 70:
                fleet_analytics['performance_breakdown']['good'] += 1
            elif performance.efficiency_score >= 50:
                fleet_analytics['performance_breakdown']['fair'] += 1
            else:
                fleet_analytics['performance_breakdown']['poor'] += 1
                
                # Add to optimization opportunities
                fleet_analytics['optimization_opportunities'].append({
                    'ship_name': ship.get('name', 'Unknown'),
                    'mmsi': ship.get('mmsi'),
                    'current_efficiency': performance.efficiency_score,
                    'recommended_speed': performance.optimal_speed,
                    'potential_savings_percent': round(savings_potential, 1),
                    'priority': 'High' if performance.efficiency_score < 40 else 'Medium'
                })
        
        if ships_data:
            fleet_analytics['average_efficiency'] = round(total_efficiency / len(ships_data), 1)
            fleet_analytics['total_fuel_savings_potential'] = round(total_savings_potential / len(ships_data), 1)
        
        return jsonify({
            'status': 'success',
            'analytics': fleet_analytics,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'Kystverket AIS + MET Norway'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/api/analytics/methanol-transition')
def get_methanol_transition_analysis():
    """
    Methanol transition ROI analysis for business decisions
    Provides comprehensive cost-benefit analysis for alternative fuels
    """
    try:
        # Sample vessel data - in production this would come from database
        sample_vessel = {
            'type': 'container',
            'name': 'Sample Container Vessel',
            'fuel_consumption_annual': 5000  # tons per year
        }
        
        roi_analysis = optimizer.calculate_methanol_roi(
            sample_vessel, 
            sample_vessel['fuel_consumption_annual']
        )
        
        return jsonify({
            'status': 'success', 
            'methanol_analysis': roi_analysis,
            'vessel_type': sample_vessel['type'],
            'annual_fuel_usage_tons': sample_vessel['fuel_consumption_annual'],
            'timestamp': datetime.now().isoformat(),
            'analysis_basis': 'Maersk operational data + IMO 2025 regulations'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/api/analytics/environmental-impact')
def get_environmental_impact():
    """
    Environmental impact analytics for sustainability reporting
    Calculates CO2 emissions and environmental footprint
    """
    try:
        ships_data = get_live_ships_data()
        
        total_co2_emissions = 0
        total_fuel_consumption = 0
        
        for ship in ships_data:
            # Estimate fuel consumption based on vessel type and speed
            vessel_type = ship.get('type', 'container')
            speed = ship.get('sog', 12.0)
            
            # Simplified fuel consumption model
            consumption_rates = {
                'tanker': 8.0,
                'container': 6.5, 
                'bulk_carrier': 7.2,
                'passenger': 4.8
            }
            
            base_consumption = consumption_rates.get(vessel_type, 6.0)
            hourly_consumption = base_consumption * (speed / 12.0) ** 3
            total_fuel_consumption += hourly_consumption
            
            # CO2 emissions: 3.114 tons CO2 per ton of fuel
            total_co2_emissions += hourly_consumption * 3.114
        
        return jsonify({
            'status': 'success',
            'environmental_metrics': {
                'total_co2_emissions_tons_hour': round(total_co2_emissions, 2),
                'total_fuel_consumption_tons_hour': round(total_fuel_consumption, 2),
                'estimated_annual_co2_tons': round(total_co2_emissions * 24 * 365, 2),
                'carbon_intensity': round(total_co2_emissions / len(ships_data), 2) if ships_data else 0,
                'ships_monitored': len(ships_data)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500