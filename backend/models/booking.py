from backend.extensions import db
from datetime import datetime, UTC
from .user import User
from .cruise import Cruise

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cruise_id = db.Column(db.Integer, db.ForeignKey('cruises.id'), nullable=False)
    num_of_people = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    user = db.relationship('User', back_populates="bookings")
    cruise = db.relationship("Cruise", back_populates="bookings")

    def __repr__(self):
        return f'<Booking {self.id} by User {self.user_id} for Cruise {self.cruise_id}>'
