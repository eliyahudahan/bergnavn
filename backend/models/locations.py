from backend.extensions import db

class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Location {self.name}, {self.country}>"
