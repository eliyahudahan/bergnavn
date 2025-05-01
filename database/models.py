from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Cruise(db.Model):
    __tablename__ = 'cruises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='planned')
    description = db.Column(db.Text, nullable=True)
