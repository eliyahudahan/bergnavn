import time
from app import app
from backend.extensions import db
from sqlalchemy import text

print("⚡ Performance Test")
print("=" * 50)

with app.app_context():
    tests = [
        ("Simple COUNT query", "SELECT COUNT(*) FROM routes"),
        ("Complex join check", """
            SELECT COUNT(*) 
            FROM routes r
            LEFT JOIN route_legs rl ON r.id = rl.route_id
            WHERE r.is_active = true
        """),
        ("Column metadata", """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'routes' 
            ORDER BY ordinal_position
        """),
        ("Sample data fetch", """
            SELECT id, name, origin, destination, source
            FROM routes
            WHERE is_active = true
            ORDER BY id
            LIMIT 10
        """)
    ]
    
    total_time = 0
    for test_name, query in tests:
        start_time = time.time()
        
        try:
            result = db.session.execute(text(query))
            
            # Fetch results (but don't print large results)
            if "metadata" in test_name or "Sample" in test_name:
                rows = result.fetchall()
                row_count = len(rows)
            else:
                row_count = result.scalar() or 0
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            status = "✅" if elapsed < 0.1 else "⚠️ "
            print(f"{status} {test_name}: {elapsed:.4f}s ({row_count} results)")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ {test_name}: {elapsed:.4f}s - Error: {str(e)[:50]}")

print(f"\n📊 Total test time: {total_time:.4f}s")
print(f"📊 Average per query: {total_time/len(tests):.4f}s")

if total_time < 0.5:
    print("\n🎉 Performance: ✅ EXCELLENT")
elif total_time < 1.0:
    print("\n🎉 Performance: ✅ GOOD")
elif total_time < 2.0:
    print("\n⚠️  Performance: ⚠️  ACCEPTABLE")
else:
    print("\n❌ Performance: ❌ NEEDS IMPROVEMENT")
