# backend/services/route_evaluator.py
import logging
from backend.models.route import Route
from backend.models.voyage_leg import VoyageLeg
from backend.models.weather_status import WeatherStatus
from backend.models.port import Port

logger = logging.getLogger(__name__)


# ---------------------------------------
# Helper: Map route status → UI color
# ---------------------------------------
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


# ---------------------------------------
# Main Route Evaluation Logic
# ---------------------------------------
def evaluate_route(route_id):
    try:
        # Fetch route
        route = Route.query.get(route_id)
        if not route or not route.is_active:
            logger.warning(f"Route ID {route_id} not found or inactive.")
            return {
                "status": "NOT_FOUND",
                "color": get_status_color("NOT_FOUND")
            }

        # Active legs only
        legs = [leg for leg in route.legs if leg.is_active]

        if not legs:
            logger.info(f"Route ID {route_id} has no active legs.")
            return {
                "status": "NO_LEGS",
                "color": get_status_color("NO_LEGS")
            }

        issues = []
        cancelled_legs = 0

        # ---------------------------------------
        # Weather-based evaluation for each leg
        # ---------------------------------------
        for leg in legs:

            # A leg must have at least one port (arrival/departure)
            relevant_port_ids = [leg.departure_port_id, leg.arrival_port_id]

            for port_id in relevant_port_ids:
                if not port_id:
                    issues.append("Leg missing port reference")
                    continue

                status = WeatherStatus.query.filter_by(
                    port_id=port_id
                ).order_by(
                    WeatherStatus.datetime.desc()
                ).first()

                if not status:
                    issues.append(f"No weather data for port ID {port_id}")
                    continue

                if not status.is_active:
                    issues.append(f"Port {status.port.name} inactive")
                    continue

                # Actual alert logic
                if status.alert_level in ['red', 'black']:

                    if getattr(leg, "is_critical", False):
                        cancelled_legs += 1
                        issues.append(
                            f"Critical leg cancelled due to alert at "
                            f"{status.port.name}: {status.alert_level}"
                        )
                    else:
                        issues.append(
                            f"Non-critical leg affected due to alert at "
                            f"{status.port.name}: {status.alert_level}"
                        )

        # ---------------------------------------
        # Determine final route status
        # ---------------------------------------
        if cancelled_legs > 0:
            result = {
                "status": "CANCELLED",
                "issues": issues,
                "recommended_action": "Cancel"
            }
            result["color"] = get_status_color(result["status"])
            return result

        if issues:
            result = {
                "status": "REROUTE_NEEDED",
                "issues": issues,
                "recommended_action": "Reroute"
            }
            result["color"] = get_status_color(result["status"])
            return result

        # Default: everything clear
        result = {
            "status": "OK",
            "recommended_action": "Continue"
        }
        result["color"] = get_status_color(result["status"])
        return result

    except Exception as e:
        logger.error(
            f"Error evaluating route {route_id}: {str(e)}",
            exc_info=True
        )
        return {
            "status": "ERROR",
            "color": get_status_color("ERROR"),
            "error": str(e)
        }
