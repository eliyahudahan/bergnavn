# backend/models/weather_status.py

from backend.extensions import db

class WeatherStatus(db.Model):
    __tablename__ = 'weather_statuses'

    id = db.Column(db.Integer, primary_key=True)
    port_id = db.Column(db.Integer, db.ForeignKey('ports.id'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    wind_speed = db.Column(db.Float)
    weather_condition = db.Column(db.String(100))  # לדוגמה: 'Storm', 'Cloudy'
    
    sunrise = db.Column(db.Time)
    sunset = db.Column(db.Time)
    
    alert_level = db.Column(db.String(10))  # לדוגמה: 'green', 'red', 'black'

    port = db.relationship("Port", backref="weather_statuses")
