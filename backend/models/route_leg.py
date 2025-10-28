from backend.extensions import db
from geoalchemy2 import Geometry  # ✅ ADDED

class RouteLeg(db.Model):
    """
    A leg of a route, from waypoint A to waypoint B.
    """
    __tablename__ = "route_legs"

    id = db.Column(db.Integer, primary_key=True)
    leg_index = db.Column(db.Integer, nullable=False)
    geometry = db.Column(Geometry("LINESTRING", srid=4326))  # ✅ FIXED: Geometry not db.Geometry
    distance_nm = db.Column(db.Float)  # distance in nautical miles
    eta_minutes = db.Column(db.Float)  # estimated time

    # ForeignKey to base_routes
    base_route_id = db.Column(db.Integer, db.ForeignKey("base_routes.id"))
    
    # FIXED: String-based relationship
    base_route = db.relationship("BaseRoute", back_populates="legs")

    def __repr__(self):
        return f"<RouteLeg {self.leg_index} of route {self.base_route_id}>"