from backend.extensions import db

class Waypoint(db.Model):
    """
    A waypoint belonging to a route leg.
    """
    __tablename__ = "waypoints"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    position = db.Column(db.Geometry("POINT", srid=4326))
    order_index = db.Column(db.Integer, nullable=False)

    # ForeignKey to route_leg
    route_leg_id = db.Column(db.Integer, db.ForeignKey("route_legs.id"))
