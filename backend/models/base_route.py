from backend.extensions import db
from geoalchemy2 import Geometry  # ✅ ADDED

class BaseRoute(db.Model):
    """
    Represents a parsed RTZ route (top-level).
    """
    __tablename__ = "base_routes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    geometry = db.Column(Geometry("LINESTRING", srid=4326))  # ✅ FIXED: Geometry not db.Geometry

    # ForeignKey to route_files
    route_file_id = db.Column(db.Integer, db.ForeignKey("route_files.id"))
    route_file = db.relationship("RouteFile", back_populates="base_routes")

    # Legs of this route
    legs = db.relationship("RouteLeg", back_populates="base_route")

    def __repr__(self):
        return f"<BaseRoute {self.name}>"