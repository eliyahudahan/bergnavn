from backend import db
from datetime import datetime
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import JSON

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

    # Always JSON – works both with SQLite and PostgreSQL
    preferred_sailing_areas = db.Column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list
    )

    def __repr__(self):
        return f'<DummyUser {self.username}>'

    # Helper method to safely set preferred sailing areas
    def set_preferred_sailing_areas(self, areas):
        self.preferred_sailing_areas = areas or []
