from backend.extensions import db
from backend.models.voyage_leg import VoyageLeg

class Route(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_days = db.Column(db.Float)
    total_distance_nm = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)

    legs = db.relationship("VoyageLeg", backref="route", cascade="all, delete-orphan")

