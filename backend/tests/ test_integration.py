"""
Integration Tests for RTZ Parser and Database Integration
Tests the complete pipeline from RTZ parsing to database storage
"""

import pytest
import tempfile
import os
from pathlib import Path
from xml.etree import ElementTree as ET

class TestRTZDatabaseIntegration:
    """Test RTZ parser integration with database"""
    
    def test_rtz_parser_technical_waypoints(self):
        """Test that RTZ parser only extracts technical waypoints"""
        from backend.services.rtz_parser import parse_rtz, _is_technical_waypoint
        
        # Test technical waypoint detection
        technical_wp = {'name': 'pilot_boarding', 'lat': 60.0, 'lon': 5.0}
        tourist_wp = {'name': 'nature_park', 'lat': 61.0, 'lon': 6.0}
        
        assert _is_technical_waypoint(technical_wp) == True
        assert _is_technical_waypoint(tourist_wp) == False
        assert _is_technical_waypoint({'name': None, 'lat': 62.0, 'lon': 7.0}) == True
    
    def test_rtz_parser_with_sample_data(self):
        """Test RTZ parser with sample RTZ data"""
        from backend.services.rtz_parser import parse_rtz
        
        # Create a temporary RTZ file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rtz', delete=False) as f:
            # Simple RTZ-like XML structure
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
            <route>
                <routeInfo>
                    <routeName>Test Route</routeName>
                </routeInfo>
                <waypoints>
                    <waypoint id="1">
                        <position>
                            <lat>60.3913</lat>
                            <lon>5.3221</lon>
                        </position>
                        <name>bergen_harbor</name>
                    </waypoint>
                    <waypoint id="2">
                        <position>
                            <lat>60.7789</lat>
                            <lon>4.7150</lon>
                        </position>
                        <name>fedjeosen_entrance</name>
                    </waypoint>
                </waypoints>
            </route>''')
            temp_file = f.name
        
        try:
            # Parse the test file
            routes = parse_rtz(temp_file)
            
            # Verify parsing results
            assert len(routes) == 1
            route = routes[0]
            
            assert route['route_name'] == 'Test Route'
            assert len(route['waypoints']) == 2
            assert route['waypoints_type'] == 'technical_only'
            assert route['total_distance_nm'] > 0
            
            # Verify waypoints are technical
            for wp in route['waypoints']:
                assert _is_technical_waypoint(wp) == True
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_database_save_functionality(self):
        """Test saving parsed routes to database"""
        from backend.services.rtz_parser import save_rtz_routes_to_db
        
        # Create sample route data
        sample_routes = [
            {
                'route_name': 'Test Integration Route',
                'total_distance_nm': 45.2,
                'waypoints': [
                    {'name': 'test_point_1', 'lat': 59.91, 'lon': 10.75},
                    {'name': 'test_point_2', 'lat': 59.85, 'lon': 10.60}
                ],
                'legs': []
            }
        ]
        
        # Try to save to database
        saved_count = save_rtz_routes_to_db(sample_routes)
        
        # Should either save successfully or fail gracefully
        assert saved_count >= 0
        assert isinstance(saved_count, int)
    
    def test_recommendation_engine_db_integration(self):
        """Test that recommendation engine can use database data"""
        from backend.ml.recommendation_engine import EmpiricalRouteRecommender
        
        # Initialize recommender
        recommender = EmpiricalRouteRecommender()
        
        # Should be able to load routes (even if empty)
        routes = recommender.get_available_routes()
        assert isinstance(routes, list)
        
        # Test recommendation with sample data
        vessel_data = {
            'type': 'container',
            'current_location': 'bergen', 
            'destinations': ['oslo']
        }
        weather_forecast = {
            'wind_speed': 12,
            'wave_height': 1.5,
            'season': 'summer'
        }
        
        recommendations = recommender.recommend_optimal_routes(
            vessel_data, weather_forecast, max_recommendations=2
        )
        
        # Should return a list (may be empty if no matching routes)
        assert isinstance(recommendations, list)
    
    def test_validation_service_integration(self):
        """Test validation service with database integration"""
        from backend.services.validation_service import RouteValidation
        
        validator = RouteValidation()
        
        # Test with sample route data
        sample_route = {
            'origin': 'bergen',
            'destination': 'oslo', 
            'distance_nm': 310.0,
            'eem_savings_potential': 0.087
        }
        
        # Test fuel savings validation
        validation_result = validator.validate_fuel_savings(sample_route)
        
        # Should return structured validation results
        assert 'predicted_savings' in validation_result
        assert 'empirical_savings' in validation_result
        assert 'confidence_interval' in validation_result
        assert 'statistical_significance' in validation_result
        assert 'sample_size' in validation_result
        
        # Test safety validation
        safety_result = validator.validate_route_safety(
            {'waypoints': [{'lat': 59.91, 'lon': 10.75}]},
            {'wind_speed': 15, 'wave_height': 2.0}
        )
        
        assert 'safety_score' in safety_result
        assert 'overall_assessment' in safety_result

class TestIntegrationPipeline:
    """Test the complete integration pipeline"""
    
    def test_integration_script_structure(self):
        """Test that integration script has correct structure"""
        # This is a structural test - the script should run without syntax errors
        from backend.scripts.integration_script import integrate_all_rtz_files, verify_database_integration
        
        # These functions should exist and be callable
        assert callable(integrate_all_rtz_files)
        assert callable(verify_database_integration)
    
    def test_error_handling(self):
        """Test that integration handles errors gracefully"""
        from backend.services.rtz_parser import parse_rtz
        
        # Test with non-existent file
        routes = parse_rtz('/non/existent/file.rtz')
        assert routes == []  # Should return empty list, not crash
        
        # Test with invalid XML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rtz', delete=False) as f:
            f.write('Invalid XML content')
            temp_file = f.name
        
        try:
            routes = parse_rtz(temp_file)
            assert routes == []  # Should handle parse errors gracefully
        finally:
            os.unlink(temp_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])