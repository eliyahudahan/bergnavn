from datetime import datetime
from backend import db

class Cruise(db.Model):
    __tablename__ = 'cruises'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Attributes
    title = db.Column(db.String(150), nullable=False)  # Title of the cruise
    description = db.Column(db.Text, nullable=True)  # Description of the cruise (optional)
    departure_date = db.Column(db.DateTime, nullable=False)  # Departure date
    return_date = db.Column(db.DateTime, nullable=False)  # Return date
    price = db.Column(db.Float, nullable=False)  # Price of the cruise
    is_active = db.Column(db.Boolean, default=True)  # Flag to mark if the cruise is active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Creation timestamp
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Update timestamp

    # Optional: Relationships to other models (e.g. users, bookings, etc.)
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    # user = db.relationship('User', backref=db.backref('cruises', lazy=True))
    
    # Example method to format dates in a friendly way (optional)
    def __repr__(self):
        return f"<Cruise {self.title} ({self.departure_date} - {self.return_date})>"

