from datetime import datetime, UTC
from backend.extensions import db

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # הקשר היחיד שנשאר
    booking = db.relationship("Booking", back_populates="payment", uselist=False)

    def __repr__(self):
        return f"<Payment {self.id} - Booking {self.booking_id} - Amount {self.amount}>"


