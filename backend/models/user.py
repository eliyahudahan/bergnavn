from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from backend.extensions import db  # Assuming SQLAlchemy is already configured

# Model to store user information
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    is_verified = db.Column(db.Boolean, default=False)  # Email verification flag
    is_admin = db.Column(db.Boolean, default=False)  # For distinguishing admins from regular users
    
    bookings = db.relationship("Booking", back_populates="user")
    ##payments = db.relationship("Payment", back_populates="user")



    # Relationship to bookings (if applicable)
    # bookings = db.relationship('Booking', backref='user', lazy=True)

    # Method to set the password (encrypt it before saving)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check the password (to verify user login)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Method to verify email (can be used after registration to confirm email)
    def verify_email(self):
        self.is_verified = True

    # Method to toggle admin status (for privileged users like operators)
    def set_admin(self, status: bool):
        self.is_admin = status

    # Additional helper methods can be added as needed for the app

# Helper function to create a user
def create_user(username, email, password):
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return new_user
