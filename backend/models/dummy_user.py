from backend import db
from datetime import datetime
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import JSON
import os

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

    # Use JSON + MutableList for testing and SQLite compatibility
    if os.environ.get('TESTING') == '1':
        preferred_sailing_areas = db.Column(MutableList.as_mutable(JSON), default=[])
    else:
        from sqlalchemy.dialects.postgresql import ARRAY
        preferred_sailing_areas = db.Column(ARRAY(db.String), default=[])

    def __repr__(self):
        return f'<DummyUser {self.username}>'

    # helper method to safely set preferred sailing areas
    def set_preferred_sailing_areas(self, areas):
        self.preferred_sailing_areas = areas or []
