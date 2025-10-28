from backend.extensions import db
from datetime import datetime, UTC  # ✅ FIXED: Added UTC

class RouteFile(db.Model):
    """
    Stores uploaded RTZ route files metadata.
    """
    __tablename__ = "route_files"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))  # ✅ FIXED: UTC
    file_content = db.Column(db.LargeBinary, nullable=False)

    # FIXED: String-based relationship (no import needed)
    base_routes = db.relationship("BaseRoute", back_populates="route_file")

    def __repr__(self):
        return f"<RouteFile {self.filename}>"