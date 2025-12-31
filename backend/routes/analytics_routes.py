# backend/routes/analytics_routes.py
"""
ANALYTICS ROUTES - endpoints for business intelligence dashboards
Enhanced with Data Science portfolio features
Provides fleet performance analytics and methanol transition analysis
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from scipy import stats
import logging

logger = logging.getLogger(__name__)
analytics_bp = Blueprint('analytics_bp', __name__)

# Try to import optimizer if available
try:
    from backend.ml.enhanced_fuel_optimizer import EnhancedFuelOptimizer
    optimizer = EnhancedFuelOptimizer()
    OPTIMIZER_AVAILABLE = True
except ImportError:
    OPTIMIZER_AVAILABLE = False
    logger.warning("Fuel optimizer not available")

def get_live_ships_data():
    """Get real AIS data or fallback to mock"""
    try:
        if hasattr(current_app, 'ais_service'):
            return current_app.ais_service.get_latest_positions()[:20]
    except:
        pass
    
    # Fallback mock data
    return [
        {'mmsi': '257158400', 'name': 'VICTORIA WILSON', 'type': 'container', 'sog': 14.2, 'lat': 58.1467, 'lon': 8.0980},
        {'mmsi': '258225000', 'name': 'KRISTIANSAND FJORD', 'type': 'passenger', 'sog': 8.5, 'lat': 58.5, 'lon': 9.0},
        {'mmsi': '259187300', 'name': 'OSLO CARRIER', 'type': 'tanker', 'sog': 11.3, 'lat': 59.0, 'lon': 10.0},
        {'mmsi': '259652100', 'name': 'BERGEN TRADER', 'type': 'cargo', 'sog': 12.1, 'lat': 60.3913, 'lon': 5.3221},
        {'mmsi': '257845200', 'name': 'STAVANGER EXPRESS', 'type': 'container', 'sog': 16.5, 'lat': 58.9699, 'lon': 5.7331}
    ]

def get_weather_data():
    """Get real weather data or fallback"""
    try:
        if hasattr(current_app, 'weather_service'):
            return current_app.weather_service.get_current_weather()
    except:
        pass
    
    return {'wind_speed': 8.5, 'wind_direction': 45, 'wave_height': 1.2, 'temperature': 9.0}

@analytics_bp.route('/api/analytics/fleet-performance')
def get_fleet_performance():
    """Fleet-wide performance analytics for business intelligence"""
    try:
        ships_data = get_live_ships_data()
        
        analytics = {
            'total_ships': len(ships_data),
            'average_efficiency': 0,
            'performance_breakdown': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0},
            'optimization_opportunities': []
        }
        
        if OPTIMIZER_AVAILABLE:
            total_efficiency = 0
            for ship in ships_data:
                weather = get_weather_data()
                performance = optimizer.calculate_optimal_speed_profile(ship, weather)
                score = performance.efficiency_score
                total_efficiency += score
                
                if score >= 90: analytics['performance_breakdown']['excellent'] += 1
                elif score >= 70: analytics['performance_breakdown']['good'] += 1
                elif score >= 50: analytics['performance_breakdown']['fair'] += 1
                else: 
                    analytics['performance_breakdown']['poor'] += 1
                    analytics['optimization_opportunities'].append({
                        'ship_name': ship.get('name', 'Unknown'),
                        'current_efficiency': score,
                        'potential_savings': round(100 - score, 1)
                    })
            
            analytics['average_efficiency'] = round(total_efficiency / len(ships_data), 1)
        
        return jsonify({'status': 'success', 'analytics': analytics})
        
    except Exception as e:
        logger.error(f"Fleet analytics error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/api/analytics/methanol-transition')
def get_methanol_transition_analysis():
    """Methanol transition ROI analysis"""
    try:
        if OPTIMIZER_AVAILABLE:
            sample_vessel = {'type': 'container', 'fuel_consumption_annual': 5000}
            roi_analysis = optimizer.calculate_methanol_roi(sample_vessel, 5000)
            return jsonify({'status': 'success', 'methanol_analysis': roi_analysis})
        else:
            return jsonify({'status': 'success', 'message': 'Optimizer not available'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/api/analytics/route-statistics')
def get_route_statistics():
    """Data Science portfolio endpoint - Statistical analysis of routes"""
    try:
        from backend.services.rtz_parser import discover_rtz_files
        routes_data = discover_rtz_files()
        
        if not routes_data:
            return jsonify({'status': 'error', 'message': 'No routes found'}), 404
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(routes_data)
        
        # Descriptive statistics
        stats = {
            'total_routes': len(df),
            'avg_distance_nm': float(df['total_distance_nm'].mean()),
            'std_distance': float(df['total_distance_nm'].std()),
            'median_waypoints': int(df['waypoint_count'].median()),
            'distance_skewness': float(stats.skew(df['total_distance_nm'].dropna())),
            'distance_kurtosis': float(stats.kurtosis(df['total_distance_nm'].dropna()))
        }
        
        # Outlier detection using Isolation Forest
        features = df[['total_distance_nm', 'waypoint_count']].fillna(0)
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        outlier_predictions = iso_forest.fit_predict(features)
        outlier_indices = np.where(outlier_predictions == -1)[0]
        
        outlier_routes = []
        for idx in outlier_indices[:5]:  # Return top 5 outliers
            route = routes_data[idx]
            outlier_routes.append({
                'name': route.get('route_name', f'Route_{idx}'),
                'distance': route.get('total_distance_nm', 0),
                'waypoints': route.get('waypoint_count', 0),
                'city': route.get('source_city', 'unknown')
            })
        
        # Route clustering
        clusters = None
        if len(routes_data) > 3:
            cluster_features = []
            for route in routes_data:
                if route.get('waypoints'):
                    wps = route['waypoints']
                    if len(wps) >= 3:
                        cluster_features.append([
                            wps[0]['lat'], wps[0]['lon'],
                            wps[-1]['lat'], wps[-1]['lon']
                        ])
            
            if cluster_features and len(cluster_features) > 1:
                clustering = DBSCAN(eps=2.0, min_samples=2)
                clusters = clustering.fit_predict(cluster_features)
        
        # Histogram data for visualization
        distances = [r['total_distance_nm'] for r in routes_data if r.get('total_distance_nm')]
        hist, bins = np.histogram(distances, bins=10)
        
        return jsonify({
            'status': 'success',
            'descriptive_stats': stats,
            'outlier_analysis': {
                'total_outliers': len(outlier_indices),
                'outlier_percentage': round(len(outlier_indices) / len(routes_data) * 100, 1),
                'sample_outliers': outlier_routes
            },
            'clustering': {
                'n_clusters': len(set(clusters)) if clusters is not None else 0,
                'cluster_info': 'DBSCAN clustering applied' if clusters is not None else 'Not enough data'
            },
            'visualizations': {
                'histogram': {'values': hist.tolist(), 'bins': bins.tolist()},
                'scatter_data': [
                    {
                        'x': r['total_distance_nm'],
                        'y': r.get('waypoint_count', 0),
                        'city': r.get('source_city', 'unknown'),
                        'name': r.get('route_name', '')[:30]
                    }
                    for r in routes_data if r.get('total_distance_nm')
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Route statistics error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/api/analytics/vessel-predictions')
def get_vessel_predictions():
    """Predictive analytics endpoint for Data Science portfolio"""
    try:
        ships_data = get_live_ships_data()
        
        if not ships_data:
            return jsonify({'status': 'error', 'message': 'No vessel data'}), 404
        
        # Simple prediction model (simulated)
        df = pd.DataFrame(ships_data)
        
        # Add simulated features for demo
        if 'sog' in df.columns:
            df['estimated_arrival_hours'] = np.random.uniform(2, 48, len(df))
            df['fuel_efficiency_score'] = np.random.uniform(50, 95, len(df))
            df['maintenance_priority'] = np.random.choice(['Low', 'Medium', 'High'], len(df))
        
        predictions = []
        for idx, ship in enumerate(ships_data[:5]):  # Return top 5
            predictions.append({
                'vessel_name': ship.get('name', f'Vessel_{idx}'),
                'type': ship.get('type', 'unknown'),
                'current_speed': ship.get('sog', 0),
                'predicted_arrival_hours': round(np.random.uniform(2, 48), 1),
                'fuel_efficiency': round(np.random.uniform(60, 95), 1),
                'risk_score': round(np.random.uniform(1, 10), 1)
            })
        
        return jsonify({
            'status': 'success',
            'predictive_analytics': {
                'total_vessels_analyzed': len(ships_data),
                'average_predicted_efficiency': round(np.mean([p['fuel_efficiency'] for p in predictions]), 1),
                'high_risk_vessels': len([p for p in predictions if p['risk_score'] > 7]),
                'vessel_predictions': predictions
            }
        })
        
    except Exception as e:
        logger.error(f"Vessel predictions error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500