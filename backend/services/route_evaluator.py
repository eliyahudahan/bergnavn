from backend.models.route import Route
from backend.models.voyage_leg import VoyageLeg
from backend.models.weather_status import WeatherStatus
from backend.models.port import Port


def evaluate_route(route_id):
    route = Route.query.get(route_id)
    if not route:
        return {"status": "NOT_FOUND"}

    legs = route.legs
    if not legs:
        return {"status": "NO_LEGS"}

    issues = []
    for leg in legs:
        for port_id in [leg.departure_port_id, leg.arrival_port_id]:
            status = WeatherStatus.query.filter_by(port_id=port_id).order_by(WeatherStatus.datetime.desc()).first()
            if status:
                if not status.is_active:
                    issues.append(f"Port {status.port.name} inactive")
                elif status.alert_level in ['red', 'black']:
                    issues.append(f"Alert at {status.port.name}: {status.alert_level}")

    # הדפסת מידע על המסלול והשלבים (מחוץ ללולאה)
    print(f"Route: {route.name}, Legs count: {len(legs)}")
    for leg in legs:
        print(f"Leg {leg.leg_order}: Ports {leg.departure_port_id}, {leg.arrival_port_id}")

    if issues:
        return {
            "status": "REROUTE_NEEDED",
            "issues": issues
        }

    return {"status": "OK"}

