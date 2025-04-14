from flask import Flask
from backend.routes.user_routes import user_blueprint  # ייבוא ה-blueprint
from backend.routes.cruise_routes import cruise_blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import os
from dotenv import load_dotenv
from backend.models.user import User
from flask_login import LoginManager
from backend import db

# Load environment variables from .env file
load_dotenv()

def create_app():
    # Create the Flask app
    from backend.config.config import Config
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking for better performance

    # Set up email configuration
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = True  # Set to True or False depending on your email provider
    app.config['MAIL_PORT'] = 587  # Adjust the port if necessary (587 is for TLS)
    
    # Set debugging mode based on .env configuration
    app.config['DEBUG'] = os.getenv('DEBUG') == 'True'

    # Initialize the services (database and mail)
    db.init_app(app)
    mail = Mail(app)

    # Attempt to create all tables (if not already created)
    try:
        with app.app_context():
            db.create_all()  # Create all tables in the database
        print("Database connection successful")
    except Exception as e:
        print("Error connecting to database:", e)

    # Register the routes
    from backend.routes.user_routes import user_blueprint
    from backend.routes.cruise_routes import cruise_blueprint
    app.register_blueprint(user_blueprint)
    app.register_blueprint(cruise_blueprint)

    # Initialize login manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'user.login'  # Set the login route for unauthenticated users

    # Define how to load a user from the database
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

# Run the app with debugging enabled (only in development)
if __name__ == "__main__":
    app = create_app()  # Create the app instance
    app.run(debug=True)











