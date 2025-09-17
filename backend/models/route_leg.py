from backend.extensions import db

class RouteLeg(db.Model):
    """
    A leg of a route, from waypoint A to waypoint B.
    """
    __tablename__ = "route_legs"

    id = db.Column(db.Integer, primary_key=True)
    leg_index = db.Column(db.Integer, nullable=False)
    geometry = db.Column(db.Geometry("LINESTRING", srid=4326))
    distance_nm = db.Column(db.Float)  # distance in nautical miles
    eta_minutes = db.Column(db.Float)  # estimated time

    # ForeignKey to base_routes
    base_route_id = db.Column(db.Integer, db.ForeignKey("base_routes.id"))
    base_route = db.relationship("BaseRoute", back_populates="legs")
