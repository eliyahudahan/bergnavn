from backend.models.route import Route
from backend.models.voyage_leg import VoyageLeg
from backend.models.weather_status import WeatherStatus
from backend.models.port import Port


def evaluate_route(route_id):
    route = Route.query.get(route_id)
    if not route or not route.is_active:
        return {"status": "NOT_FOUND"}

    legs = [leg for leg in route.legs if leg.is_active]
    if not legs:
        return {"status": "NO_LEGS"}

    issues = []
    cancelled_legs = 0
    for leg in legs:
        for port_id in [leg.departure_port_id, leg.arrival_port_id]:
            status = WeatherStatus.query.filter_by(port_id=port_id).order_by(WeatherStatus.datetime.desc()).first()
            if status:
                if not status.is_active:
                    issues.append(f"Port {status.port.name} inactive")
                elif status.alert_level in ['red', 'black']:
                    # אם הרגל קריטי, ביטול, אחרת דילוג
                    if leg.is_critical:
                        cancelled_legs += 1
                        issues.append(f"Critical leg cancelled due to alert at {status.port.name}: {status.alert_level}")
                    else:
                        issues.append(f"Non-critical leg skipped due to alert at {status.port.name}: {status.alert_level}")

    if cancelled_legs > 0:
        return {
            "status": "CANCELLED",
            "issues": issues,
            "recommended_action": "Cancel"
        }
    elif issues:
        return {
            "status": "REROUTE_NEEDED",
            "issues": issues,
            "recommended_action": "Reroute"
        }

    return {"status": "OK", "recommended_action": "Continue"}


