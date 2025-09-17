from backend.extensions import db

class HazardZone(db.Model):
    """
    Hazardous area (turbines, tankers, currents).
    """
    __tablename__ = "hazard_zones"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    hazard_type = db.Column(db.String(100), nullable=False)  # e.g., turbine, tanker
    geometry = db.Column(db.Geometry("POLYGON", srid=4326))
    risk_score = db.Column(db.Float, default=0.0)
