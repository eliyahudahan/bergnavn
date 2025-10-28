from backend.extensions import db
from datetime import datetime, UTC  # ✅ FIXED: Added import

class WeatherStatus(db.Model):
    __tablename__ = 'weather_statuses'

    id = db.Column(db.Integer, primary_key=True)
    port_id = db.Column(db.Integer, db.ForeignKey('ports.id'), nullable=False)
    datetime = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)  # ✅ FIXED: UTC default
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    wind_speed = db.Column(db.Float)
    weather_condition = db.Column(db.String(100))
    
    sunrise = db.Column(db.Time)
    sunset = db.Column(db.Time)
    
    alert_level = db.Column(db.String(10))

    # ✅ FIXED: String-based relationship
    port = db.relationship("Port", backref="weather_statuses")

    def __repr__(self):
        return f"<WeatherStatus port:{self.port_id} condition:{self.weather_condition}>"