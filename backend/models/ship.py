from datetime import datetime, UTC
from backend.extensions import db

class Ship(db.Model):
    __tablename__ = 'ships'

    id = db.Column(db.Integer, primary_key=True)
    mmsi = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # tanker, container, passenger, cargo
    length = db.Column(db.Float, nullable=True)  # meters
    draft = db.Column(db.Float, nullable=True)   # meters
    built_year = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<Ship {self.name} ({self.type})>"