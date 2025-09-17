from backend.extensions import db
from datetime import datetime

class RouteFile(db.Model):
    """
    Stores uploaded RTZ route files metadata.
    """
    __tablename__ = "route_files"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_content = db.Column(db.LargeBinary, nullable=False)

    # Relationship to base routes
    base_routes = db.relationship("BaseRoute", back_populates="route_file")
