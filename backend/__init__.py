from backend.extensions import db, migrate
from flask_mail import Mail
from flask_login import LoginManager

mail = Mail()
login_manager = LoginManager()

__all__ = ["db", "migrate", "mail", "login_manager"]


