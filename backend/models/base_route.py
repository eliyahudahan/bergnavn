from backend.extensions import db

class BaseRoute(db.Model):
    """
    Represents a parsed RTZ route (top-level).
    """
    __tablename__ = "base_routes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    geometry = db.Column(db.Geometry("LINESTRING", srid=4326))

    # ForeignKey to route_files
    route_file_id = db.Column(db.Integer, db.ForeignKey("route_files.id"))
    route_file = db.relationship("RouteFile", back_populates="base_routes")

    # Legs of this route
    legs = db.relationship("RouteLeg", back_populates="base_route")
