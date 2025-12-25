import psycopg2

print("🔍 Checking database reality...")
print("=" * 50)

try:
    # Connect directly to PostgreSQL
    conn = psycopg2.connect(
        dbname="framg",
        user="framg",
        password="copenhagen2024",
        host="localhost",
        port="5432"
    )
    
    cursor = conn.cursor()
    
    # 1. Check ALL tables in the database
    cursor.execute("""
        SELECT schemaname, tablename, tableowner 
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    
    print("📊 All tables in 'public' schema:")
    for schema, table, owner in cursor.fetchall():
        print(f"  • {table} (owner: {owner})")
    
    print("\n" + "=" * 50)
    
    # 2. Check routes table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'routes'
        ORDER BY ordinal_position;
    """)
    
    print("📋 Structure of 'routes' table:")
    columns = cursor.fetchall()
    for col_name, dtype, nullable, default in columns:
        default_str = f" DEFAULT: {default}" if default else ""
        print(f"  • {col_name}: {dtype} (nullable: {nullable}){default_str}")
    
    print(f"\nTotal columns: {len(columns)}")
    
    # 3. Check for data in routes table
    cursor.execute("SELECT COUNT(*) FROM public.routes;")
    count = cursor.fetchone()[0]
    print(f"\n📈 Number of rows in routes table: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, name, is_active FROM public.routes LIMIT 5;")
        print("\nFirst 5 routes:")
        for route_id, name, active in cursor.fetchall():
            status = "✓ Active" if active else "✗ Inactive"
            print(f"  • {route_id}: '{name}' [{status}]")
    
    # 4. Check what the actual migration state is
    cursor.execute("""
        SELECT version_num FROM alembic_version LIMIT 1;
    """)
    alembic_version = cursor.fetchone()
    print(f"\n🔧 Alembic version: {alembic_version[0] if alembic_version else 'No version found'}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Database check completed successfully!")
    
except psycopg2.OperationalError as e:
    print(f"❌ Cannot connect to database: {e}")
    print("Please check if PostgreSQL is running and credentials are correct.")
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 50)
