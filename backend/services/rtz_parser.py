def extract_origin_destination(route_name: str, waypoints: List[Dict]) -> Tuple[str, str]:
    """
    Extract origin and destination from route name or waypoints
    Handles NCA route naming convention: NCA_Origin_Destination_*
    """
    # Try to extract from route name first (NCA naming convention)
    if 'NCA_' in route_name:
        parts = route_name.split('_')
        if len(parts) >= 4:
            origin = parts[1].title()  # Capitalize first letter
            destination = parts[2].title()
            
            # Handle common abbreviations
            origin = _expand_abbreviation(origin)
            destination = _expand_abbreviation(destination)
            
            return origin, destination
    
    # Fallback: use first and last waypoint names
    if waypoints and len(waypoints) >= 2:
        origin = waypoints[0].get('name', 'Unknown')
        destination = waypoints[-1].get('name', 'Unknown')
        
        # Clean waypoint names
        origin = _clean_waypoint_name(origin)
        destination = _clean_waypoint_name(destination)
        
        return origin, destination
    
    return 'Unknown', 'Unknown'

def _expand_abbreviation(name: str) -> str:
    """Expand common Norwegian port abbreviations"""
    abbreviations = {
        'Bergen': 'Bergen',
        'Trondheim': 'Trondheim', 
        'Stavanger': 'Stavanger',
        'Oslo': 'Oslo',
        'Alesund': 'Ålesund',
        'Andalsnes': 'Åndalsnes',
        'Kristiansand': 'Kristiansand',
        'Drammen': 'Drammen',
        'Sandefj': 'Sandefjord',
        'Fedjeosen': 'Fedje',
        'Halten': 'Haltenbanken',
        'Stad': 'Stadthavet',
        'Breisundet': 'Breisundet',
        'Oksoy': 'Oksøy',
        'Sydostgr': 'Sydostgrunnen',
        'Bonden': 'Bonden',
        'Grip': 'Grip',
        'Grande': 'Rørvik',
        'Rorvik': 'Rørvik',
        'Steinsd': 'Steinsundet',
        'Krakhelle': 'Krakhellesundet',
        'Flavaer': 'Flævar',
        'Aramsd': 'Aramshavet'
    }
    return abbreviations.get(name, name)

def _clean_waypoint_name(name: str) -> str:
    """Clean waypoint names by removing technical details"""
    if not name:
        return 'Unknown'
    
    # Remove technical suffixes and VTS reports
    clean_name = name.split(' - report')[0].split(' lt')[0].split(' bn')[0]
    clean_name = clean_name.split(' buoy')[0].split(' 7.5 m')[0].split(' 9m')[0]
    clean_name = clean_name.split(' 13 m')[0].split(' pilot')[0]
    
    # Capitalize first letter
    return clean_name.strip().title()

def save_rtz_routes_to_db(routes_data: List[Dict]) -> int:
    """
    Save parsed RTZ routes to database using proper SQLAlchemy models
    ENHANCED: Now extracts and stores origin/destination information
    """
    try:
        # ✅ CORRECT IMPORT - app.py is in root directory
        from app import create_app
        from backend.models import Route, VoyageLeg
        from backend.extensions import db
        
        # Create Flask app and application context
        app = create_app()
        
        with app.app_context():
            saved_count = 0
            
            for route_info in routes_data:
                try:
                    # Check if route already exists
                    existing_route = Route.query.filter(
                        Route.name == route_info['route_name']
                    ).first()
                    
                    if existing_route:
                        logger.info(f"Route '{route_info['route_name']}' already exists, skipping")
                        continue
                    
                    # ✅ ENHANCED: Extract origin and destination
                    waypoints = route_info['waypoints']
                    origin, destination = extract_origin_destination(route_info['route_name'], waypoints)
                    
                    # ✅ ENHANCED: Calculate duration (assume 15 knots average speed)
                    total_distance = route_info['total_distance_nm']
                    duration_days = round(total_distance / (15 * 24), 2)  # 15 knots * 24 hours
                    
                    # Create main Route entry with enhanced data
                    new_route = Route(
                        name=route_info['route_name'],
                        total_distance_nm=total_distance,
                        origin=origin,
                        destination=destination,
                        duration_days=duration_days,
                        description=f"Official NCA route: {origin} → {destination} ({total_distance} nm)",
                        is_active=True
                    )
                    db.session.add(new_route)
                    db.session.flush()  # Get the route ID
                    
                    # Create VoyageLegs for each segment between waypoints
                    for i in range(len(waypoints) - 1):
                        start_wp = waypoints[i]
                        end_wp = waypoints[i + 1]
                        
                        # Find the corresponding leg distance
                        leg_distance = 0.0
                        if i < len(route_info['legs']):
                            leg_distance = route_info['legs'][i]['distance_nm']
                        else:
                            # Calculate if not available
                            leg_distance = haversine_nm(
                                start_wp['lat'], start_wp['lon'],
                                end_wp['lat'], end_wp['lon']
                            )
                        
                        # Create voyage leg
                        voyage_leg = VoyageLeg(
                            route_id=new_route.id,
                            leg_order=i + 1,
                            departure_lat=start_wp['lat'],
                            departure_lon=start_wp['lon'],
                            arrival_lat=end_wp['lat'],
                            arrival_lon=end_wp['lon'],
                            distance_nm=leg_distance,
                            departure_time=datetime.utcnow(),  # Placeholder
                            arrival_time=datetime.utcnow(),    # Placeholder
                            is_active=True
                        )
                        db.session.add(voyage_leg)
                    
                    saved_count += 1
                    logger.info(f"✅ Saved route '{route_info['route_name']}' ({origin} → {destination}) with {len(waypoints)} waypoints")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to save route '{route_info['route_name']}': {str(e)}")
                    continue
            
            # Commit all changes
            db.session.commit()
            logger.info(f"🎉 Successfully saved {saved_count} routes to database")
            return saved_count
        
    except ImportError as e:
        logger.warning(f"Database models not available: {e}")
        return 0
    except Exception as e:
        logger.error(f"Database save failed: {e}")
        return 0