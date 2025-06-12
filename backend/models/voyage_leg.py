from datetime import datetime, UTC
from backend.extensions import db

class VoyageLeg(db.Model):
    __tablename__ = 'voyage_legs'

    id = db.Column(db.Integer, primary_key=True)
    cruise_id = db.Column(db.Integer, db.ForeignKey('cruises.id'), nullable=False)
    departure_port = db.Column(db.String(100), nullable=False)
    arrival_port = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    leg_order = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    cruise = db.relationship("Cruise", back_populates="legs")

    def __repr__(self):
        return f"<VoyageLeg {self.departure_port} → {self.arrival_port} (Leg {self.leg_order})>"

