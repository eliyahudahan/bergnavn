from datetime import datetime, UTC
from backend.extensions import db

class FuelEfficiencyCalculation(db.Model):
    __tablename__ = 'fuel_efficiency_calculations'

    id = db.Column(db.Integer, primary_key=True)
    ship_id = db.Column(db.Integer, db.ForeignKey('ships.id'), nullable=False)
    voyage_leg_id = db.Column(db.Integer, db.ForeignKey('voyage_legs.id'), nullable=True)
    
    # Calculation results
    fuel_saving_percent = db.Column(db.Float, nullable=False)
    estimated_savings_usd_hour = db.Column(db.Float, nullable=False)
    optimal_speed = db.Column(db.Float, nullable=False)
    current_speed = db.Column(db.Float, nullable=False)
    
    calculated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    
    # Relationships
    ship = db.relationship("Ship", backref="fuel_calculations")
    voyage_leg = db.relationship("VoyageLeg", backref="fuel_calculations")

    def __repr__(self):
        return f"<FuelEfficiencyCalculation ship:{self.ship_id} saving:{self.fuel_saving_percent}%>"