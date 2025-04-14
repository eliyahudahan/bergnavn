from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager

# Create global instances (not initialized yet)
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

