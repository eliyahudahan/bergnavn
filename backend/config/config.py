# backend/config/config.py - Configuration settings for BergNavn Maritime Application
import os
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL was not loaded properly! Check your .env file.")

Base = declarative_base()  # SQLAlchemy base model definition - FIXED deprecated import

class Config:
    """Main application configuration class with environment variables"""
    
    # Security settings for session management
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    
    # Database configuration for PostgreSQL connection
    DATABASE_URL = DATABASE_URL
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Debug and development settings
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    # Email configuration for SMTP server
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    # External API configurations for maritime data
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')  # From environment only
    MET_NORWAY_USER_AGENT = 'BergNavnMaritime/2.0 (framgangsrik747@gmail.com)'
    
    # Application performance and cache settings
    CACHE_TIMEOUT = 600  # 10 minutes in seconds
    WEATHER_UPDATE_INTERVAL = 300000  # 5 minutes in milliseconds
    AIS_SOCKET_TIMEOUT = 30  # Socket timeout for AIS data in seconds


class TestingConfig(Config):
    """Testing configuration with PostgreSQL test database"""
    TESTING = True
    DEBUG = False
    
    # Use PostgreSQL for tests - supports spatial functions
    SQLALCHEMY_DATABASE_URI = TEST_DATABASE_URL
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False  # Disable CSRF protection for tests
    DATABASE_URL = TEST_DATABASE_URL
    
    # Disable external services for tests
    DISABLE_AIS_SERVICE = True
    FLASK_SKIP_SCHEDULER = True