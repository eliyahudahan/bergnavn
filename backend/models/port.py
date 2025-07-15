from backend.extensions import db  # <-- חשוב מאוד לייבא את db לפני השימוש בו

class Port(db.Model):
    __tablename__ = 'ports'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # אם החלטת להוסיף

    __table_args__ = (
        db.UniqueConstraint('name', 'country', name='uq_port_name_country'),
    )

    def __repr__(self):
        return f'<Port {self.name} ({self.latitude}, {self.longitude})>'




