from flask import Flask
from backend.routes.user_routes import user_blueprint  # ➜ Import Blueprints for user and cruise routes
from backend.routes.cruise_routes import cruise_blueprint
from flask_migrate import Migrate  # Import Migrate globally
from backend import db, mail, login_manager  # ➜ Use the global instances
from backend.models.user import User
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Migrate globally
migrate = Migrate()

def create_app():
    # Import configuration class
    from backend.config.config import Config
    
    # Create the Flask app instance
    app = Flask(__name__)

    # Load configuration from the Config class    
    app.config.from_object(Config)

    # Initialize the services (database and mail)
    db.init_app(app)
    mail.init_app(app)  # Initialize mail extension here

    # Initialize login manager
    login_manager.init_app(app)  # Use the global login_manager

    # Initialize Migrate with the app and db
    migrate.init_app(app, db)  # Now Migrate is initialized globally

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # ➜ Disable SQLAlchemy modification tracking for better performance

    # ➜ Create all tables in the database (if they don't already exist)
    try:
        with app.app_context():
            db.create_all()  # Create all tables in the database
            logging.info("Database connected and tables created.")
        
    except Exception as e:
        logging.error(f"Could not connect to database: {e}")

    # Register the routes
    app.register_blueprint(user_blueprint)  # Register user blueprint
    app.register_blueprint(cruise_blueprint)  # Register cruise blueprint

    # Define how to load a user from the database
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

# Run the app with debugging enabled (only in development)
if __name__ == "__main__":
    app = create_app()  # Create the app instance
    app.run(debug=True)

















