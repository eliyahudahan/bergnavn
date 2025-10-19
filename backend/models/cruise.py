from datetime import datetime, UTC
from backend.extensions import db

class Cruise(db.Model):
    __tablename__ = 'cruises'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    departure_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=False)
    origin = db.Column(db.String(100), nullable=True)    # City or location name
    destination = db.Column(db.String(100), nullable=False)
    origin_lat = db.Column(db.Float, nullable=True)  # Optional: for weather API (latitude)
    origin_lon = db.Column(db.Float, nullable=True)  # Optional: for weather API (longitude)
    destination_lat = db.Column(db.Float, nullable=True)
    destination_lon = db.Column(db.Float, nullable=True)
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationship with clock (one-to-one)
    clock = db.relationship(
        "backend.models.clock.Clock",
        uselist=False,
        back_populates="cruise"
    )

    # (Temporarily disabled — Booking model currently removed)
    # bookings = db.relationship("Booking", back_populates="cruise")

    # Relationship with voyage legs
    legs = db.relationship(
        "backend.models.voyage_leg.VoyageLeg",
        back_populates="cruise",
        cascade="all, delete-orphan",
        order_by="VoyageLeg.leg_order"
    )

    @property
    def duration_days(self):
        if self.departure_date and self.return_date:
            return (self.return_date - self.departure_date).days
        return None

    def __repr__(self):
        return f"<Cruise {self.title} ({self.origin} → {self.destination})>"
