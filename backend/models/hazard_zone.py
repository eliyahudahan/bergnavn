from backend.extensions import db
from geoalchemy2 import Geometry  # ✅ ADDED

class HazardZone(db.Model):
    """
    Hazardous area (turbines, tankers, currents).
    """
    __tablename__ = "hazard_zones"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    hazard_type = db.Column(db.String(100), nullable=False)
    geometry = db.Column(Geometry("POLYGON", srid=4326))  # ✅ FIXED: Geometry not db.Geometry
    risk_score = db.Column(db.Float, default=0.0)

    # No relationships - this is fine

    def __repr__(self):
        return f"<HazardZone {self.name} ({self.hazard_type})>"