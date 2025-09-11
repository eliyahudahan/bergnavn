from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# Mail service
mail = Mail()

# Login manager
login_manager = LoginManager()
