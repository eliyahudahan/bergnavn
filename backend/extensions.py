"""
backend/extensions.py
Central place for initializing Flask extensions.
All extensions are imported here and initialized in app.py
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from geoalchemy2 import Geometry  # ✅ ADDED: For PostGIS support

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# Mail service
mail = Mail()