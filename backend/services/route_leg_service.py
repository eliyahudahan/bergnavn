from datetime import datetime, timedelta
from backend.services.port_service import add_or_update_port
from backend.utils.distance_utils import haversine_distance
from backend.extensions import db
from backend.models.voyage_leg import VoyageLeg
from backend.models.route import Route

def create_route_leg(route_id, departure_name, arrival_name, leg_order, cruise_id=None, country_from=None, country_to=None,
    cruise_departure_time=None):
    """
    יוצר מקטע הפלגה (voyage leg) בין שני נמלים.
    """
    departure_port = add_or_update_port(departure_name, country_from)
    arrival_port = add_or_update_port(arrival_name, country_to)

    if not departure_port.latitude or not arrival_port.latitude:
        raise Exception("Missing coordinates for ports")

    distance = haversine_distance(
        departure_port.latitude,
        departure_port.longitude,
        arrival_port.latitude,
        arrival_port.longitude
    )

    travel_speed_kmph = 37
    travel_time_hours = distance / travel_speed_kmph
    travel_time = timedelta(hours=travel_time_hours)
    
    departure_time = cruise_departure_time or datetime.now()
    arrival_time = departure_time + travel_time

    leg = VoyageLeg(
        cruise_id=cruise_id,
        route_id=route_id,
        departure_port_id=departure_port.id,
        arrival_port_id=arrival_port.id,
        departure_lat=departure_port.latitude,
        departure_lon=departure_port.longitude,
        arrival_lat=arrival_port.latitude,
        arrival_lon=arrival_port.longitude,
        departure_time=departure_time,
        arrival_time=arrival_time,
        leg_order=leg_order
    )

    
    leg.distance_nm = distance  # <-- מחוץ לקריאה לאובייקט

    db.session.add(leg)
    db.session.commit()
    return leg


def create_route(cruise_id, legs_list, cruise_departure_time=None):
    """
    יוצר מסלול שלם של מקטעים לפי רשימה מסודרת.
    """
    # יצירת Route חדש לפני כל מקטעים
    route = Route(
        cruise_id=cruise_id,
        name="Generated Route",  # אפשר לעדכן לפי צורך
        description="Generated based on legs",
        total_distance_nm=0
    )
    db.session.add(route)
    db.session.commit()  # חובה כדי שיהיה route.id

    current_departure_time = cruise_departure_time or datetime.now()
    created_legs = []

    for i, leg in enumerate(legs_list, start=1):
        created_leg = create_route_leg(
            route_id=route.id,
            cruise_id=cruise_id,
            departure_name=leg["from"],
            arrival_name=leg["to"],
            leg_order=i,
            country_from=leg.get("country_from"),
            country_to=leg.get("country_to"),
            cruise_departure_time=current_departure_time
        )
        current_departure_time = created_leg.arrival_time
        created_legs.append(created_leg)

    # חישוב מרחק כולל
    route.total_distance_nm = sum([
        haversine_distance(
            leg.departure_lat, leg.departure_lon,
            leg.arrival_lat, leg.arrival_lon
        ) for leg in created_legs
    ])
    db.session.commit()

    return created_legs




