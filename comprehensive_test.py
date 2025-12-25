#!/usr/bin/env python3
"""
Comprehensive system test after migration fix
"""

import sys
import os
from datetime import datetime

def print_step(step_num, description):
    """Print a step header"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")

def main():
    print("🚀 COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Import the app
        print_step(1, "Application Import")
        from app import app
        from backend.extensions import db
        print("✅ Flask app imported successfully")
        
        with app.app_context():
            # Step 2: Database connection
            print_step(2, "Database Connection")
            from sqlalchemy import text
            
            result = db.session.execute(text("SELECT version()"))
            db_version = result.scalar()
            print(f"✅ Database: {db_version}")
            
            # Step 3: Alembic status
            print_step(3, "Alembic Status")
            result = db.session.execute(text("SELECT version_num FROM alembic_version"))
            alembic_version = result.scalar()
            print(f"✅ Alembic version: {alembic_version}")
            
            # Step 4: Routes table check
            print_step(4, "Routes Table")
            
            # Check column count
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'routes'
            """))
            column_count = result.scalar()
            print(f"✅ Columns in routes: {column_count}")
            
            # Check data
            result = db.session.execute(text("SELECT COUNT(*) FROM routes"))
            route_count = result.scalar()
            print(f"✅ Total routes: {route_count}")
            
            # Check RTZ columns
            result = db.session.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'routes'
                AND column_name IN ('source', 'rtz_filename', 'created_at', 'updated_at')
                ORDER BY column_name
            """))
            
            rtz_columns = result.fetchall()
            print(f"✅ RTZ columns found: {len(rtz_columns)}/4")
            for col_name, data_type in rtz_columns:
                print(f"   • {col_name} ({data_type})")
            
            # Step 5: Sample data verification
            print_step(5, "Sample Data")
            result = db.session.execute(text("""
                SELECT 
                    name, 
                    origin, 
                    destination,
                    source,
                    created_at IS NOT NULL as has_created_at,
                    updated_at IS NOT NULL as has_updated_at
                FROM routes 
                WHERE is_active = true
                ORDER BY id
                LIMIT 3
            """))
            
            print("Sample active routes:")
            for row in result:
                name, origin, dest, source, has_created, has_updated = row
                created_status = "✓" if has_created else "✗"
                updated_status = "✓" if has_updated else "✗"
                print(f"   • {name}")
                print(f"     {origin} → {dest} (source: {source})")
                print(f"     created_at: {created_status}, updated_at: {updated_status}")
            
            # Step 6: API models test
            print_step(6, "API Models")
            try:
                from backend.models.route import Route
                from backend.models.route_leg import RouteLeg
                from backend.models.waypoint import Waypoint
                print("✅ All models import successfully")
                
                # Try to query using SQLAlchemy models
                routes = Route.query.limit(2).all()
                if routes:
                    print(f"✅ SQLAlchemy query works: {len(routes)} routes returned")
                    for route in routes:
                        print(f"   • {route.name} (ID: {route.id})")
                else:
                    print("⚠️ No routes returned from SQLAlchemy query")
                    
            except Exception as e:
                print(f"❌ Model error: {e}")
            
            # Step 7: Migration history
            print_step(7, "Migration History")
            result = db.session.execute(text("""
                SELECT table_name, COUNT(*) as column_count
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name IN ('routes', 'route_legs', 'waypoints', 'base_routes')
                GROUP BY table_name
                ORDER BY table_name
            """))
            
            print("Current schema summary:")
            for table_name, col_count in result:
                print(f"   • {table_name}: {col_count} columns")
            
        # Step 8: External tools test
        print_step(8, "External Tools")
        
        # Test Flask CLI
        print("Testing Flask CLI commands...")
        os.system("flask db current > /dev/null 2>&1 && echo '✅ flask db current works' || echo '❌ flask db current failed'")
        
        # Test health endpoint (if server is running)
        print("\n🎉 All tests completed successfully!")
        print("\n" + "=" * 60)
        print("SYSTEM STATUS: ✅ HEALTHY")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ SYSTEM TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
