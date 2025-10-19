from datetime import datetime, UTC
from backend.extensions import db
from backend.models.port import Port
from backend.models.cruise import Cruise

class VoyageLeg(db.Model):
    __tablename__ = 'voyage_legs'

    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    cruise_id = db.Column(db.Integer, db.ForeignKey('cruises.id'), nullable=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=True)
    departure_port_id = db.Column(db.Integer, db.ForeignKey('ports.id', ondelete='SET NULL'), nullable=True)
    arrival_port_id = db.Column(db.Integer, db.ForeignKey('ports.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    departure_port = db.relationship("Port", foreign_keys=[departure_port_id])
    arrival_port = db.relationship("Port", foreign_keys=[arrival_port_id])
    cruise = db.relationship("Cruise", back_populates="legs")

    # Coordinates
    departure_lat = db.Column(db.Float, nullable=True)
    departure_lon = db.Column(db.Float, nullable=True)
    arrival_lat = db.Column(db.Float, nullable=True)
    arrival_lon = db.Column(db.Float, nullable=True)

    # Timing
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)

    # Sequence and status
    leg_order = db.Column(db.Integer, nullable=False, default=1)
    distance_nm = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                           onupdate=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        dep_name = self.departure_port.name if self.departure_port else "Unknown"
        arr_name = self.arrival_port.name if self.arrival_port else "Unknown"
        return f"<VoyageLeg {dep_name} → {arr_name} (Leg {self.leg_order})>"
