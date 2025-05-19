from datetime import datetime
from backend import db

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
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Future relationship with bookings
    bookings = db.relationship("Booking", back_populates="cruise")
    

    def __repr__(self):
        return f"<Cruise {self.title} ({self.origin} → {self.destination})>"

