#!/usr/bin/env python3
"""
Test script to verify dashboard fixes work
"""

import os
import sys
sys.path.append('backend')

from flask import Flask, render_template

# Create test Flask app
app = Flask(__name__)

@app.route('/test-dashboard')
def test_dashboard():
    """Test route that simulates the dashboard data"""
    
    # Sample route data
    test_routes = [
        {
            "route_name": "NCA_Bergen_Oslo_2025",
            "clean_name": "Bergen to Oslo",
            "origin": "Bergen",
            "destination": "Oslo",
            "total_distance_nm": 185.5,
            "waypoint_count": 12,
            "source_city": "Bergen",
            "status": "active",
            "empirically_verified": True
        },
        {
            "route_name": "NCA_Stavanger_Haugesund_2025",
            "clean_name": "Stavanger to Haugesund",
            "origin": "Stavanger",
            "destination": "Haugesund",
            "total_distance_nm": 42.3,
            "waypoint_count": 8,
            "source_city": "Stavanger",
            "status": "active",
            "empirically_verified": True
        },
        {
            "route_name": "NCA_Trondheim_Bodo_2025",
            "clean_name": "Trondheim to Bodø",
            "origin": "Trondheim",
            "destination": "Bodø",
            "total_distance_nm": 312.7,
            "waypoint_count": 18,
            "source_city": "Trondheim",
            "status": "active",
            "empirically_verified": False
        }
    ]
    
    # Simulate dashboard template data
    template_data = {
        "routes": test_routes,
        "ports_list": ["Bergen", "Oslo", "Stavanger", "Haugesund", "Trondheim", "Bodø"],
        "actual_route_count": len(test_routes),
        "unique_ports_count": 6,
        "lang": "en"
    }
    
    return render_template('maritime_split/dashboard_base.html', **template_data)

if __name__ == '__main__':
    print("🚀 Starting test dashboard server...")
    print("🌐 Open: http://localhost:5001/test-dashboard")
    app.run(debug=True, port=5001)
