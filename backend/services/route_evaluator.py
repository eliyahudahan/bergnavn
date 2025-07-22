import logging
from backend.models.route import Route
from backend.models.voyage_leg import VoyageLeg
from backend.models.weather_status import WeatherStatus
from backend.models.port import Port

logger = logging.getLogger(__name__)

def get_status_color(status):
    color_map = {
        "OK": "green",
        "REROUTE_NEEDED": "yellow",
        "CANCELLED": "red",
        "NOT_FOUND": "black",
        "NO_LEGS": "black",
        "ERROR": "grey"
    }
    return color_map.get(status, "grey")

def evaluate_route(route_id):
    try:
        route = Route.query.get(route_id)
        if not route or not route.is_active:
            logger.warning(f"Route ID {route_id} not found or inactive.")
            return {
                "status": "NOT_FOUND",
                "color": get_status_color("NOT_FOUND")
            }

        legs = [leg for leg in route.legs if leg.is_active]
        if not legs:
            logger.info(f"Route ID {route_id} has no active legs.")
            return {
                "status": "NO_LEGS",
                "color": get_status_color("NO_LEGS")
            }

        issues = []
        cancelled_legs = 0

        for leg in legs:
            for port_id in [leg.departure_port_id, leg.arrival_port_id]:
                status = WeatherStatus.query.filter_by(port_id=port_id).order_by(WeatherStatus.datetime.desc()).first()
                if status:
                    if not status.is_active:
                        issues.append(f"Port {status.port.name} inactive")
                    elif status.alert_level in ['red', 'black']:
                        if leg.is_critical:
                            cancelled_legs += 1
                            issues.append(f"Critical leg cancelled due to alert at {status.port.name}: {status.alert_level}")
                        else:
                            issues.append(f"Non-critical leg skipped due to alert at {status.port.name}: {status.alert_level}")

        if cancelled_legs > 0:
            result = {
                "status": "CANCELLED",
                "issues": issues,
                "recommended_action": "Cancel"
            }
            result["color"] = get_status_color(result["status"])
            return result

        elif issues:
            result = {
                "status": "REROUTE_NEEDED",
                "issues": issues,
                "recommended_action": "Reroute"
            }
            result["color"] = get_status_color(result["status"])
            return result

        result = {
            "status": "OK",
            "recommended_action": "Continue"
        }
        result["color"] = get_status_color(result["status"])
        return result

    except Exception as e:
        logger.error(f"Error evaluating route {route_id}: {str(e)}", exc_info=True)
        return {
            "status": "ERROR",
            "color": get_status_color("ERROR"),
            "error": str(e)
        }

