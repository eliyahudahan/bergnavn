from backend.extensions import db

class Port(db.Model):
    __tablename__ = 'ports'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    country = db.Column(db.String(100), nullable=False)  # ✅ הוספת שדה country

    def __repr__(self):
        return f'<Port {self.name} ({self.latitude}, {self.longitude})>'

