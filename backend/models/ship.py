from datetime import datetime, UTC
from backend.extensions import db

class Ship(db.Model):
    __tablename__ = 'ships'

    id = db.Column(db.Integer, primary_key=True)
    mmsi = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # tanker, container, passenger, cargo, bulk_carrier, roro
    length = db.Column(db.Float, nullable=True)  # meters
    draft = db.Column(db.Float, nullable=True)   # meters
    built_year = db.Column(db.Integer, nullable=True)
    
    # NEW FIELDS FROM SANDBOX LEARNING
    home_port = db.Column(db.String(50), nullable=True)
    fuel_efficiency_profile = db.Column(db.JSON, nullable=True)  # Store type-specific coefficients
    operational_constraints = db.Column(db.JSON, nullable=True)  # Speed limits, draft restrictions
    alternative_fuel_capability = db.Column(db.Boolean, default=False)  # Methanol support
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<Ship {self.name} ({self.type})>"

    # UPDATED: Method to get ship-specific coefficients WITH METHANOL DATA
    def get_efficiency_coefficients(self):
        """Return ship type specific coefficients for calculations including methanol"""
        coefficients = {
            'tanker': {
                'base': 0.0060, 'optimal': 11.0, 'fuel_cost': 800, 'maintenance_impact': 0.15,
                'methanol_consumption_ratio': 1.8, 'methanol_cost': 1200, 'validation': 'maersk_validated'
            },
            'container': {
                'base': 0.0040, 'optimal': 14.0, 'fuel_cost': 750, 'maintenance_impact': 0.08,
                'methanol_consumption_ratio': 1.8, 'methanol_cost': 1150, 'validation': 'maersk_validated'
            },
            'bulk_carrier': {
                'base': 0.0055, 'optimal': 13.0, 'fuel_cost': 740, 'maintenance_impact': 0.11,
                'methanol_consumption_ratio': 1.8, 'methanol_cost': 1100, 'validation': 'sandbox_validated'
            },
            'roro': {
                'base': 0.0042, 'optimal': 15.0, 'fuel_cost': 770, 'maintenance_impact': 0.09,
                'methanol_consumption_ratio': 1.8, 'methanol_cost': 1180, 'validation': 'sandbox_validated'
            },
            'passenger': {
                'base': 0.0045, 'optimal': 16.0, 'fuel_cost': 780, 'maintenance_impact': 0.12,
                'methanol_consumption_ratio': 1.8, 'methanol_cost': 1250, 'validation': 'theoretical'
            },
            'cargo': {
                'base': 0.0050, 'optimal': 12.0, 'fuel_cost': 760, 'maintenance_impact': 0.10,
                'methanol_consumption_ratio': 1.8, 'methanol_cost': 1120, 'validation': 'theoretical'
            }
        }
        return coefficients.get(self.type, coefficients['cargo'])