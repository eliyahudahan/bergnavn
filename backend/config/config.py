import os
from dotenv import load_dotenv

# טען מחדש את קובץ ה־.env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# בדוק האם הערך תקין
print(f"🔍 Loaded DATABASE_URL: {repr(DATABASE_URL)}")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL לא נטען כראוי! בדוק את קובץ .env")

# הדפסת DATABASE_URL לאימות
print("Loaded DATABASE_URL:", os.getenv("DATABASE_URL"))

class Config:
    # מפתח סוד
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')

    # טוען את כתובת ה-URL של בסיס הנתונים
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # מגדיר את URL של SQLAlchemy
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    # מונע עדכון לא נחוץ של מודל ה-SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # מצב דיבוג
    DEBUG = os.getenv('DEBUG', 'False') == 'True'  # ברירת מחדל היא False אם לא הוגדר

    # הגדרות דוא"ל
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')  # ברירת מחדל היא Gmail
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))  # פורט ברירת מחדל הוא 587 (TLS)
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')





