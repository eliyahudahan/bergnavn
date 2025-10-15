from backend.extensions import db, migrate
from flask_mail import Mail

mail = Mail()

__all__ = ["db", "migrate", "mail"]


