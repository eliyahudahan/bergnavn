from app import create_app
import psycopg2
import os

app = create_app()

print("🔍 Reality Check - What's REALLY in the database?")
print("=" * 50)

# Method 1: What Flask sees
with app.app_context():
    from backend.extensions import db
    print("1. Flask/Almebic Connection:")
    print(f"   URL: {db.engine.url}")
    
    try:
        result = db.session.execute("SELECT current_database(), current_schema()")
        db_name, schema = result.fetchone()
        print(f"   Database: {db_name}, Schema: {schema}")
        
        # Check routes table
        result = db.session.execute("""
            SELECT column_name, data_type, ordinal_position
            FROM information_schema.columns 
            WHERE table_schema = :schema AND table_name = 'routes'
            ORDER BY ordinal_position
        """, {'schema': schema})
        
        flask_columns = [(row[0], row[1]) for row in result]
        print(f"   Flask sees {len(flask_columns)} columns in routes")
        if flask_columns:
            print("   First few columns:", [c[0] for c in flask_columns[:10]])
    except Exception as e:
        print(f"   ❌ Flask error: {e}")

print()

# Method 2: Direct PostgreSQL connection
print("2. Direct PostgreSQL Connection (from .env):")
db_url = os.getenv('DATABASE_URL')
print(f"   DATABASE_URL: {db_url}")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Check current database
    cur.execute("SELECT current_database(), current_schema()")
    db_name, schema = cur.fetchone()
    print(f"   Database: {db_name}, Schema: {schema}")
    
    # Check routes table
    cur.execute("""
        SELECT column_name, data_type, ordinal_position
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = 'routes'
        ORDER BY ordinal_position
    """, (schema,))
    
    direct_columns = [(row[0], row[1]) for row in cur.fetchall()]
    print(f"   Direct connection sees {len(direct_columns)} columns in routes")
    for col, dtype in direct_columns:
        print(f"   - {col} ({dtype})")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"   ❌ Direct connection error: {e}")

print("=" * 50)
