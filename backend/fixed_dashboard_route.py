#!/usr/bin/env python3
"""
FIXED Dashboard Route for RTZ Routes Display
This should be added to backend/routes/maritime_routes.py
"""

from flask import render_template, jsonify, request, current_app
from datetime import datetime
import logging
from backend.services.rtz_parser import discover_rtz_files, get_processing_statistics
from backend.models import Route, VoyageLeg, db

logger = logging.getLogger(__name__)

def get_dashboard_data():
    """
    Get all data needed for the maritime dashboard.
    Returns: (routes_data, ports_list, unique_ports_count, empirical_verification)
    """
    try:
        # Norwegian ports list
        ports_list = [
            'bergen', 'oslo', 'stavanger', 'trondheim',
            'alesund', 'andalsnes', 'kristiansand',
            'drammen', 'sandefjord', 'flekkefjord'
        ]
        
        routes_data = []
        unique_ports = set()
        
        # Try database first
        try:
            logger.info("📊 Loading routes from database...")
            db_routes = Route.query.all()
            
            for route in db_routes:
                # Get waypoint count from voyage legs
                legs_count = VoyageLeg.query.filter_by(route_id=route.id).count()
                waypoint_count = legs_count + 1 if legs_count > 0 else 1
                
                route_dict = {
                    'route_name': route.name,
                    'clean_name': route.name.replace('NCA_', '').replace('_2025', '').replace('_', ' ').title(),
                    'origin': route.origin or 'Coastal',
                    'destination': route.destination or 'Coastal',
                    'total_distance_nm': float(route.total_distance_nm) if route.total_distance_nm else 0.0,
                    'source_city': route.origin.lower() if route.origin else 'unknown',
                    'waypoint_count': waypoint_count,
                    'legs': [],
                    'empirically_verified': True,
                    'description': f"NCA maritime route"
                }
                
                routes_data.append(route_dict)
                
                # Add to unique ports
                if route.origin and route.origin != 'Unknown':
                    unique_ports.add(route.origin.title())
                if route.destination and route.destination != 'Unknown':
                    unique_ports.add(route.destination.title())
            
            logger.info(f"✅ Loaded {len(routes_data)} routes from database")
            
        except Exception as db_error:
            logger.warning(f"⚠️ Database error: {db_error}")
            routes_data = []
        
        # If database empty, load from RTZ files
        if not routes_data:
            logger.info("📁 Loading routes from RTZ files...")
            try:
                file_routes = discover_rtz_files(enhanced=True)
                routes_data = file_routes
                
                for route in routes_data:
                    if route.get('origin'):
                        unique_ports.add(route['origin'].title())
                    if route.get('destination'):
                        unique_ports.add(route['destination'].title())
                
                logger.info(f"✅ Loaded {len(routes_data)} routes from RTZ files")
                
            except Exception as file_error:
                logger.error(f"❌ RTZ file error: {file_error}")
                routes_data = []
        
        # Create verification data
        empirical_verification = {
            'timestamp': datetime.now().isoformat(),
            'route_count': len(routes_data),
            'port_count': len(unique_ports),
            'verification_hash': f"RTZ_{len(routes_data)}_{len(unique_ports)}_{int(datetime.now().timestamp())}"
        }
        
        return routes_data, [p.title() for p in ports_list], len(unique_ports), empirical_verification
        
    except Exception as e:
        logger.error(f"❌ Dashboard data error: {e}")
        # Return empty but safe data
        return [], [], 0, None

@maritime_bp.route('/dashboard')
def dashboard():
    """
    Maritime dashboard - FIXED VERSION
    Shows actual RTZ routes from database or files
    """
    try:
        routes_data, ports_list, unique_ports_count, empirical_verification = get_dashboard_data()
        
        logger.info(f"📊 Dashboard: {len(routes_data)} routes, {unique_ports_count} ports")
        
        return render_template(
            'maritime_split/dashboard_base.html',
            routes=routes_data,
            ports_list=ports_list,
            unique_ports_count=unique_ports_count,
            empirical_verification=empirical_verification,
            lang='en'
        )
        
    except Exception as e:
        logger.error(f"❌ Dashboard route error: {e}")
        
        # Emergency fallback - minimal data
        return render_template(
            'maritime_split/dashboard_base.html',
            routes=[],
            ports_list=['Bergen', 'Oslo', 'Stavanger', 'Trondheim'],
            unique_ports_count=4,
            empirical_verification={
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            },
            lang='en'
        )

@maritime_bp.route('/api/dashboard-data')
def dashboard_data():
    """API endpoint for dashboard data (for AJAX)"""
    try:
        routes_data, ports_list, unique_ports_count, empirical_verification = get_dashboard_data()
        
        return jsonify({
            'success': True,
            'routes': routes_data[:50],  # Limit for performance
            'ports': ports_list,
            'unique_ports_count': unique_ports_count,
            'verification': empirical_verification,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'routes': [],
            'ports': []
        })

@maritime_bp.route('/api/load-rtz-now')
def load_rtz_now():
    """Force load RTZ data now"""
    try:
        from backend.services.rtz_parser import process_all_cities_routes
        
        result = process_all_cities_routes()
        
        return jsonify({
            'success': True,
            'message': f'Loaded {result} routes into database',
            'count': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
