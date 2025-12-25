from app import app
from backend.extensions import db
from sqlalchemy import text

with app.app_context():
    print("🧪 בדיקת API אחרי התיקון...")
    
    # 1. בדוק גרסת alembic
    result = db.session.execute(text("SELECT version_num FROM alembic_version"))
    print(f"✅ גרסת alembic: {result.scalar()}")
    
    # 2. בדוק עמודות
    result = db.session.execute(text("""
        SELECT COUNT(*) as column_count 
        FROM information_schema.columns 
        WHERE table_name = 'routes'
    """))
    print(f"✅ עמודות ב-routes: {result.scalar()}")
    
    # 3. בדוק נתונים
    result = db.session.execute(text("SELECT COUNT(*) FROM routes"))
    print(f"✅ שורות ב-routes: {result.scalar()}")
    
    # 4. בדוק דוגמה של נתונים
    result = db.session.execute(text("""
        SELECT name, origin, destination, source 
        FROM routes 
        LIMIT 3
    """))
    
    print("📋 דוגמת נתונים:")
    for name, origin, dest, source in result:
        print(f"  • {name}: {origin} → {dest} (מקור: {source})")
    
    print("\n🎉 הכל עובד!")
