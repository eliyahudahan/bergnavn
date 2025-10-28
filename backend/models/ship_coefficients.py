from datetime import datetime, UTC
from backend.extensions import db

class ShipTypeCoefficient(db.Model):
    __tablename__ = 'ship_type_coefficients'

    id = db.Column(db.Integer, primary_key=True)
    ship_type = db.Column(db.String(20), unique=True, nullable=False)
    
    # Core coefficients from sandbox validation
    base_consumption_coef = db.Column(db.Float, nullable=False)  # Consumption per meter-length
    optimal_speed_knots = db.Column(db.Float, nullable=False)    # Speed for max efficiency
    fuel_cost_usd_tonne = db.Column(db.Float, nullable=False)    # Type-specific fuel costs
    maintenance_impact = db.Column(db.Float, nullable=False)     # Maintenance on efficiency
    
    # NEW: Methanol support based on Maersk data
    methanol_consumption_ratio = db.Column(db.Float, default=1.8)  # Based on Maersk: 1.8x more consumption
    methanol_cost_usd_tonne = db.Column(db.Float, default=1200)    # Methanol price based on Maersk data
    
    # Validation metadata
    validation_status = db.Column(db.String(20), default='validated')  # validated, sandbox_validated, theoretical
    last_calibration_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<ShipTypeCoefficient {self.ship_type}>"


# UPDATED: Complete data population with methanol coefficients
def populate_ship_coefficients():
    """Populate with validated coefficients including methanol data from Maersk"""
    coefficients_data = [
        {
            'ship_type': 'tanker', 
            'base_consumption_coef': 0.0060, 
            'optimal_speed_knots': 11.0, 
            'fuel_cost_usd_tonne': 800, 
            'maintenance_impact': 0.15,
            'methanol_consumption_ratio': 1.8,
            'methanol_cost_usd_tonne': 1200,
            'validation_status': 'maersk_validated'
        },
        {
            'ship_type': 'container', 
            'base_consumption_coef': 0.0040, 
            'optimal_speed_knots': 14.0, 
            'fuel_cost_usd_tonne': 750, 
            'maintenance_impact': 0.08,
            'methanol_consumption_ratio': 1.8,
            'methanol_cost_usd_tonne': 1150,
            'validation_status': 'maersk_validated'
        },
        {
            'ship_type': 'bulk_carrier', 
            'base_consumption_coef': 0.0055, 
            'optimal_speed_knots': 13.0, 
            'fuel_cost_usd_tonne': 740, 
            'maintenance_impact': 0.11,
            'methanol_consumption_ratio': 1.8,
            'methanol_cost_usd_tonne': 1100,
            'validation_status': 'sandbox_validated'
        },
        {
            'ship_type': 'roro', 
            'base_consumption_coef': 0.0042, 
            'optimal_speed_knots': 15.0, 
            'fuel_cost_usd_tonne': 770, 
            'maintenance_impact': 0.09,
            'methanol_consumption_ratio': 1.8,
            'methanol_cost_usd_tonne': 1180,
            'validation_status': 'sandbox_validated'
        },
        {
            'ship_type': 'passenger', 
            'base_consumption_coef': 0.0045, 
            'optimal_speed_knots': 16.0, 
            'fuel_cost_usd_tonne': 780, 
            'maintenance_impact': 0.12,
            'methanol_consumption_ratio': 1.8,
            'methanol_cost_usd_tonne': 1250,
            'validation_status': 'theoretical'
        },
        {
            'ship_type': 'cargo', 
            'base_consumption_coef': 0.0050, 
            'optimal_speed_knots': 12.0, 
            'fuel_cost_usd_tonne': 760, 
            'maintenance_impact': 0.10,
            'methanol_consumption_ratio': 1.8,
            'methanol_cost_usd_tonne': 1120,
            'validation_status': 'theoretical'
        }
    ]
    
    for data in coefficients_data:
        if not ShipTypeCoefficient.query.filter_by(ship_type=data['ship_type']).first():
            coefficient = ShipTypeCoefficient(**data)
            db.session.add(coefficient)
            print(f"✅ Added coefficients for {data['ship_type']}")
        else:
            print(f"⚠️ Coefficients for {data['ship_type']} already exist")
    
    db.session.commit()
    print("🎉 Ship coefficients population completed!")