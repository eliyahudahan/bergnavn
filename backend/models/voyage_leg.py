from datetime import datetime, UTC
from backend.extensions import db

class VoyageLeg(db.Model):
    __tablename__ = 'voyage_legs'

    id = db.Column(db.Integer, primary_key=True)
    cruise_id = db.Column(db.Integer, db.ForeignKey('cruises.id'), nullable=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=True)
    departure_port_id = db.Column(db.Integer, db.ForeignKey('ports.id'), nullable=True)
    arrival_port_id   = db.Column(db.Integer, db.ForeignKey('ports.id'), nullable=True)
    departure_port = db.relationship("Port", foreign_keys=[departure_port_id])
    arrival_port   = db.relationship("Port", foreign_keys=[arrival_port_id])
    departure_lat = db.Column(db.Float, nullable=True)
    departure_lon = db.Column(db.Float, nullable=True)
    arrival_lat = db.Column(db.Float, nullable=True)
    arrival_lon = db.Column(db.Float, nullable=True)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    leg_order = db.Column(db.Integer, nullable=False)
    distance_nm = db.Column(db.Float, nullable=True)


    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    cruise = db.relationship("Cruise", back_populates="legs")

    def __repr__(self):
        return f"<VoyageLeg {self.departure_port.name} → {self.arrival_port.name} (Leg {self.leg_order})>"


