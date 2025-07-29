from backend import db
from datetime import datetime

class DummyUser(db.Model):
    __tablename__ = 'dummy_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    scenario = db.Column(db.String(120))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    flags = db.Column(db.JSON, default={})
    
    gender = db.Column(db.String(20))
    nationality = db.Column(db.String(50))
    language = db.Column(db.String(10))
    preferred_sailing_areas = db.Column(db.ARRAY(db.String))  # רשימת מחרוזות

    def __repr__(self):
        return f'<DummyUser {self.username}>'

