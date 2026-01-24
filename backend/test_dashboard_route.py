
@maritime_bp.route('/test-dashboard')
def test_dashboard():
    """Simple test dashboard with sample data"""
    test_routes = [
        {
            'route_name': 'NCA_Bergen_Oslo_2025',
            'clean_name': 'Bergen to Oslo',
            'origin': 'Bergen',
            'destination': 'Oslo',
            'total_distance_nm': 320.5,
            'source_city': 'bergen',
            'waypoint_count': 12,
            'empirically_verified': True,
            'description': 'Coastal route with 12 waypoints'
        },
        {
            'route_name': 'NCA_Stavanger_Trondheim_2025',
            'clean_name': 'Stavanger to Trondheim',
            'origin': 'Stavanger',
            'destination': 'Trondheim',
            'total_distance_nm': 450.2,
            'source_city': 'stavanger',
            'waypoint_count': 18,
            'empirically_verified': True,
            'description': 'Long coastal voyage'
        },
        {
            'route_name': 'NCA_Alesund_Kristiansand_2025',
            'clean_name': 'Ålesund to Kristiansand',
            'origin': 'Ålesund',
            'destination': 'Kristiansand',
            'total_distance_nm': 280.7,
            'source_city': 'alesund',
            'waypoint_count': 15,
            'empirically_verified': True,
            'description': 'Southern coastal route'
        }
    ]
    
    return render_template(
        'maritime_split/dashboard_base.html',
        routes=test_routes,
        ports_list=['Bergen', 'Oslo', 'Stavanger', 'Trondheim', 'Ålesund', 'Kristiansand'],
        unique_ports_count=6,
        empirical_verification={
            'timestamp': datetime.now().isoformat(),
            'route_count': 3,
            'port_count': 6,
            'verification_hash': 'TEST_3_6_123456'
        },
        lang='en'
    )
