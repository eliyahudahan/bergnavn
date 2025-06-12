from backend.extensions import db  # זה החלק החסר שהיה גורם ל-NameError

class Route(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_days = db.Column(db.Float)
    total_distance_nm = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)

    legs = db.relationship("RouteLeg", backref="route", cascade="all, delete-orphan")


class RouteLeg(db.Model):
    __tablename__ = 'route_legs'

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    departure_city = db.Column(db.String(100), nullable=False)
    arrival_city = db.Column(db.String(100), nullable=False)
    distance_nm = db.Column(db.Float)
    estimated_time_days = db.Column(db.Float)
    leg_order = db.Column(db.Integer)
