from backend.extensions import db

class Route(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_days = db.Column(db.Float)
    total_distance_nm = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)

    # ✅ FIXED: String-based relationship - NO ABSOLUTE IMPORT!
    legs = db.relationship("VoyageLeg", backref="route", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Route {self.name}>"