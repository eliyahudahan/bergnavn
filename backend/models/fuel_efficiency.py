from datetime import datetime, UTC
from backend.extensions import db

class FuelEfficiencyCalculation(db.Model):
    __tablename__ = 'fuel_efficiency_calculations'

    id = db.Column(db.Integer, primary_key=True)
    ship_id = db.Column(db.Integer, db.ForeignKey('ships.id'), nullable=False)
    voyage_leg_id = db.Column(db.Integer, db.ForeignKey('voyage_legs.id'), nullable=True)
    
    # Input parameters
    current_speed = db.Column(db.Float, nullable=False)
    weather_wind_speed = db.Column(db.Float, nullable=True)
    weather_wind_direction = db.Column(db.Float, nullable=True)
    
    # Calculation results
    optimal_speed = db.Column(db.Float, nullable=False)
    fuel_saving_percent = db.Column(db.Float, nullable=False)
    estimated_savings_usd_hour = db.Column(db.Float, nullable=False)
    
    # Enhanced metrics from sandbox
    efficiency_class = db.Column(db.String(10), nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    algorithm_version = db.Column(db.String(20), default='v2.0_sandbox')
    
    # Alternative fuel calculations
    alternative_fuel_type = db.Column(db.String(20), nullable=True)
    alternative_fuel_savings = db.Column(db.Float, nullable=True)
    
    calculated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    
    # FIXED: String-based relationships
    ship = db.relationship("Ship", backref="fuel_calculations")
    voyage_leg = db.relationship("VoyageLeg", backref="fuel_calculations")

    def __repr__(self):
        return f"<FuelEfficiencyCalculation ship:{self.ship_id} saving:{self.fuel_saving_percent}%>"

    # REMOVED: calculate_optimal_speed should be in Ship class or service