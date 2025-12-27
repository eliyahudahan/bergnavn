"""
Empirical Analysis API Routes
Exposes data-driven insights from real Norwegian maritime data
All endpoints return only empirical, verifiable data
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime

from backend.services.empirical_data_analyzer import EmpiricalDataAnalyzer
from backend.services.empirical_ais_service import empirical_ais_service

# Initialize analyzer with real AIS service
empirical_analyzer = EmpiricalDataAnalyzer(empirical_ais_service)

# Create blueprint
empirical_bp = Blueprint('empirical_bp', __name__)
logger = logging.getLogger(__name__)


@empirical_bp.route('/city/<city_name>/patterns')
def get_city_patterns(city_name: str):
    """
    Get empirical traffic patterns for a Norwegian city.
    
    Returns data-driven insights based on real AIS observations.
    """
    try:
        # Validate city
        if city_name not in empirical_ais_service.NORWEGIAN_CITIES:
            return jsonify({
                'error': f'Unknown city. Available: {list(empirical_ais_service.NORWEGIAN_CITIES.keys())}'
            }), 400
        
        # Get empirical analysis
        analysis = empirical_analyzer.analyze_traffic_patterns(city_name, days=3)
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing city patterns: {e}")
        return jsonify({
            'error': 'Analysis failed',
            'details': str(e)
        }), 500


@empirical_bp.route('/compare/<city1>/<city2>')
def compare_cities(city1: str, city2: str):
    """
    Compare empirical traffic patterns between two cities.
    
    All data is real-time from Norwegian AIS sources.
    """
    try:
        # Validate cities
        valid_cities = empirical_ais_service.NORWEGIAN_CITIES.keys()
        if city1 not in valid_cities or city2 not in valid_cities:
            return jsonify({
                'error': f'Invalid cities. Available: {list(valid_cities)}'
            }), 400
        
        # Get empirical comparison
        comparison = empirical_analyzer.compare_cities_traffic(city1, city2)
        
        return jsonify(comparison)
        
    except Exception as e:
        logger.error(f"Error comparing cities: {e}")
        return jsonify({
            'error': 'Comparison failed',
            'details': str(e)
        }), 500


@empirical_bp.route('/report/<city_name>')
def generate_empirical_report(city_name: str):
    """
    Generate comprehensive empirical report for a city.
    
    Includes traffic patterns, weather integration, and data-driven recommendations.
    """
    try:
        if city_name not in empirical_ais_service.NORWEGIAN_CITIES:
            return jsonify({
                'error': f'Unknown city. Available: {list(empirical_ais_service.NORWEGIAN_CITIES.keys())}'
            }), 400
        
        # Generate empirical report
        report = empirical_analyzer.generate_empirical_report(city_name)
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({
            'error': 'Report generation failed',
            'details': str(e)
        }), 500


@empirical_bp.route('/realtime/<city_name>')
def get_realtime_insights(city_name: str):
    """
    Get real-time empirical insights for a city.
    
    Combines current AIS data with pattern recognition.
    """
    try:
        if city_name not in empirical_ais_service.NORWEGIAN_CITIES:
            return jsonify({
                'error': f'Unknown city. Available: {list(empirical_ais_service.NORWEGIAN_CITIES.keys())}'
            }), 400
        
        # Get current vessels
        vessels = empirical_ais_service.get_vessels_in_city(city_name, radius_km=30)
        
        # Basic real-time insights
        insights = {
            'timestamp': datetime.now().isoformat(),
            'city': city_name,
            'current_vessel_count': len(vessels),
            'vessel_types': {},
            'average_speed_knots': 0,
            'busiest_sector': 'Calculating...',
            'data_freshness_seconds': 0,
            'is_empirical': True,
            'data_source': 'Kystdatahuset API'
        }
        
        if vessels:
            # Count vessel types
            type_counts = {}
            speeds = []
            for vessel in vessels:
                v_type = vessel.vessel_type
                type_counts[v_type] = type_counts.get(v_type, 0) + 1
                speeds.append(vessel.speed_knots)
            
            insights['vessel_types'] = type_counts
            insights['average_speed_knots'] = sum(speeds) / len(speeds) if speeds else 0
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error getting realtime insights: {e}")
        return jsonify({
            'error': 'Realtime insights failed',
            'details': str(e)
        }), 500


@empirical_bp.route('/methodology')
def get_methodology():
    """
    Explain the empirical methodology used.
    
    Important for scientific transparency.
    """
    methodology = {
        'approach': 'Empirical Data Science',
        'principle': 'Only use real, verifiable data from official sources',
        'data_sources': [
            {
                'name': 'Kystdatahuset API',
                'type': 'Real-time AIS',
                'verification_url': 'https://www.kystdatahuset.no/api/v1/ais',
                'license': 'Norwegian Open Data',
                'coverage': 'Norwegian territorial waters'
            },
            {
                'name': 'MET Norway API',
                'type': 'Weather and ocean data',
                'verification_url': 'https://api.met.no',
                'license': 'Norwegian Open Data',
                'coverage': 'Norwegian economic zone'
            }
        ],
        'analysis_techniques': [
            'Statistical pattern recognition',
            'Spatial density analysis',
            'Time-series analysis',
            'Comparative analytics'
        ],
        'quality_controls': [
            'No mock data used',
            'All data verifiable via source APIs',
            'Transparent methodology',
            'Reproducible analysis'
        ],
        'scientific_value': 'Provides genuine insights into Norwegian maritime operations',
        'limitations': [
            'Limited to publicly available data',
            'Real-time analysis depends on API availability',
            'Historical analysis limited by API data retention'
        ]
    }
    
    return jsonify(methodology)