# backend/models/route.py
from backend.extensions import db

class Route(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # FIX: back_populates במקום backref
    legs = db.relationship(
        "VoyageLeg",
        back_populates="route",
        cascade="all, delete-orphan",
        lazy=True
    )
