from backend.extensions import db
from geoalchemy2 import Geometry  # ✅ ADDED

class Waypoint(db.Model):
    """
    A waypoint belonging to a route leg.
    """
    __tablename__ = "waypoints"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    position = db.Column(Geometry("POINT", srid=4326))  # ✅ FIXED: Geometry not db.Geometry
    order_index = db.Column(db.Integer, nullable=False)

    # ForeignKey to route_leg
    route_leg_id = db.Column(db.Integer, db.ForeignKey("route_legs.id"))

    def __repr__(self):
        return f"<Waypoint {self.name} (order: {self.order_index})>"