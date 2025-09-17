"""
Service layer for route management.
Handles RTZ file parsing, BaseRoute creation, RouteLegs, Waypoints, and HazardZones.
"""

from backend.models.route import BaseRoute, RouteFile, RouteLeg
from backend.models.voyage_leg import VoyageLeg
from backend.models.hazard_zones import HazardZone
from backend.extensions import db

class RouteService:
    def __init__(self):
        pass

    def process_rtz_file(self, file):
        """
        Parse the RTZ file, create RouteFile record, and populate BaseRoute + RouteLegs.
        """
        # TODO: implement RTZ parsing
        filename = file.filename

        # Save the uploaded file info
        route_file = RouteFile(filename=filename)
        db.session.add(route_file)
        db.session.commit()

        # TODO: create BaseRoutes and RouteLegs from parsed data
        # Example:
        # base_route = BaseRoute(route_file_id=route_file.id, name="Route A")
        # db.session.add(base_route)
        # db.session.commit()
        # self._create_legs(base_route, parsed_legs)

    def get_all_base_routes(self):
        """
        Retrieve all base routes.
        """
        routes = BaseRoute.query.all()
        return [self._serialize_base_route(r) for r in routes]

    def get_base_route_with_details(self, route_id):
        """
        Retrieve a single base route with legs and waypoints.
        """
        base_route = BaseRoute.query.get(route_id)
        if not base_route:
            return None

        data = self._serialize_base_route(base_route)
        # TODO: include legs and waypoints
        return data

    def _serialize_base_route(self, base_route):
        """
        Helper to serialize BaseRoute for JSON responses.
        """
        return {
            'id': base_route.id,
            'name': base_route.name,
            'description': base_route.description
        }

    # Optional: additional helper methods for creating legs, waypoints, hazard zones
