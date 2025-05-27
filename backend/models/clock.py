from datetime import datetime, UTC
from backend import db

class Clock(db.Model):
    __tablename__ = 'clocks'

    id = db.Column(db.Integer, primary_key=True)
    cruise_id = db.Column(db.Integer, db.ForeignKey('cruises.id'), nullable=False)
    timezone = db.Column(db.String(100), nullable=False)
    offset = db.Column(db.Integer, nullable=True)  # An Example: UTC+2 = 2
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    cruise = db.relationship("backend.models.cruise.Cruise", back_populates="clock")

    def __repr__(self):
        return f"<Clock cruise_id={self.cruise_id} tz={self.timezone}>"
