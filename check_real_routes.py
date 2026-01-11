#!/usr/bin/env python3
"""
Check REAL route counts from the actual database tables
This bypasses all services and shows what's REALLY in the database
"""

import os
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
from sqlalchemy import create_engine, text, inspect, MetaData
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection using actual DATABASE_URL from .env"""
    # Get the actual DATABASE_URL from .env
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        # Try alternative names
        db_url = os.getenv('DATABASE_URI') or os.getenv('SQLALCHEMY_DATABASE_URI')
    
    if not db_url:
        print("❌ No DATABASE_URL found in .env file!")
        print("   Please check your .env file has DATABASE_URL=...")
        sys.exit(1)
    
    print(f"🔗 Connecting to: {db_url}")
    engine = create_engine(db_url)
    return engine

def check_all_tables(engine):
    """Check all tables and their content"""
    print("\n" + "="*70)
    print("📊 DATABASE TABLE ANALYSIS")
    print("="*70)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📋 Found {len(tables)} tables:")
    for table in sorted(tables):
        try:
            with engine.connect() as conn:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"   • {table:25} = {count:4} rows")
        except:
            print(f"   • {table:25} = ERROR reading")
    
    return tables

def analyze_routes_table(engine):
    """Analyze the 'routes' table specifically"""
    print("\n" + "="*70)
    print("🎯 DETAILED ANALYSIS OF 'routes' TABLE")
    print("="*70)
    
    with engine.connect() as conn:
        # 1. Basic count
        total = conn.execute(text("SELECT COUNT(*) FROM routes")).scalar()
        print(f"\n📈 Total routes in 'routes' table: {total}")
        
        if total == 0:
            print("❌ 'routes' table is EMPTY!")
            return None
        
        # 2. Get unique ports
        origins = conn.execute(text("""
            SELECT COUNT(DISTINCT origin) as count,
                   STRING_AGG(DISTINCT origin, ', ') as list
            FROM routes
            WHERE origin IS NOT NULL AND origin != 'Unknown'
        """)).fetchone()
        
        destinations = conn.execute(text("""
            SELECT COUNT(DISTINCT destination) as count,
                   STRING_AGG(DISTINCT destination, ', ') as list
            FROM routes
            WHERE destination IS NOT NULL AND destination != 'Unknown'
        """)).fetchone()
        
        print(f"\n🌍 Port Analysis:")
        print(f"   Unique origins: {origins.count}")
        print(f"   Unique destinations: {destinations.count}")
        
        # 3. Show some routes
        sample_routes = conn.execute(text("""
            SELECT name, origin, destination, total_distance_nm, created_at
            FROM routes
            WHERE is_active = true
            ORDER BY created_at DESC
            LIMIT 10
        """)).fetchall()
        
        print(f"\n🚢 Sample routes (latest 10):")
        for i, route in enumerate(sample_routes, 1):
            print(f"   {i:2}. {route.name:40} {route.origin:15} → {route.destination:15} {route.total_distance_nm:6.1f} nm")
        
        # 4. Statistics
        stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                AVG(total_distance_nm) as avg_distance,
                MIN(total_distance_nm) as min_distance,
                MAX(total_distance_nm) as max_distance,
                SUM(total_distance_nm) as total_distance_sum
            FROM routes
            WHERE is_active = true
        """)).fetchone()
        
        print(f"\n📊 Route Statistics:")
        print(f"   Average distance: {stats.avg_distance:.1f} nm")
        print(f"   Min distance: {stats.min_distance:.1f} nm")
        print(f"   Max distance: {stats.max_distance:.1f} nm")
        print(f"   Total distance (sum): {stats.total_distance_sum:.0f} nm")
        
        # 5. Check for rtz_routes (old table)
        inspector = inspect(engine)
        if 'rtz_routes' in inspector.get_table_names():
            rtz_count = conn.execute(text("SELECT COUNT(*) FROM rtz_routes")).scalar()
            print(f"\n⚠️  Found 'rtz_routes' table (old) with {rtz_count} rows")
            print(f"   Your dashboard might be reading from WRONG table!")
        
        return {
            'total_routes': total,
            'unique_origins': origins.count,
            'unique_destinations': destinations.count,
            'origins_list': origins.list.split(', ') if origins.list else [],
            'destinations_list': destinations.list.split(', ') if destinations.list else [],
            'sample_routes': sample_routes
        }

def check_what_dashboard_sees():
    """Check what the dashboard template is actually getting"""
    print("\n" + "="*70)
    print("👀 WHAT THE DASHBOARD ACTUALLY SEES")
    print("="*70)
    
    engine = get_database_connection()
    
    with engine.connect() as conn:
        # Check what maritime_routes.py is doing
        print("\n🔍 Checking 'routes' table data that dashboard should see:")
        
        # Count active routes
        active_routes = conn.execute(text("""
            SELECT COUNT(*) 
            FROM routes 
            WHERE is_active = true
        """)).scalar()
        
        print(f"   Active routes in 'routes' table: {active_routes}")
        
        # Get ports for dashboard
        ports_query = conn.execute(text("""
            SELECT DISTINCT origin as port
            FROM routes 
            WHERE origin IS NOT NULL AND origin != 'Unknown'
            UNION
            SELECT DISTINCT destination as port
            FROM routes 
            WHERE destination IS NOT NULL AND destination != 'Unknown'
            ORDER BY port
        """)).fetchall()
        
        ports = [p.port for p in ports_query]
        print(f"   Unique ports in database: {len(ports)}")
        print(f"   Ports: {', '.join(ports[:10])}{'...' if len(ports) > 10 else ''}")
        
    engine.dispose()
    
    return {
        'active_routes': active_routes,
        'ports': ports,
        'port_count': len(ports)
    }

def fix_dashboard_data_source():
    """Show how to fix dashboard to read from correct source"""
    print("\n" + "="*70)
    print("🔧 HOW TO FIX THE DASHBOARD")
    print("="*70)
    
    # Get real data
    engine = get_database_connection()
    dashboard_data = check_what_dashboard_sees()
    
    print(f"\n🎯 Dashboard SHOULD show:")
    print(f"   Actual Routes: {dashboard_data['active_routes']}")
    print(f"   Ports: {dashboard_data['port_count']}/10")
    
    print(f"\n💻 Update 'backend/routes/maritime_routes.py' to:")
    print("""
    @maritime_bp.route('/dashboard')
    def maritime_dashboard():
        # GET REAL DATA FROM DATABASE
        from backend.models.route import Route
        
        # Get active routes from 'routes' table
        routes = Route.query.filter_by(is_active=True).all()
        total_routes = len(routes)
        
        # Get unique ports
        origins = db.session.query(Route.origin).distinct().filter(
            Route.origin.isnot(None), 
            Route.origin != 'Unknown'
        ).all()
        destinations = db.session.query(Route.destination).distinct().filter(
            Route.destination.isnot(None), 
            Route.destination != 'Unknown'
        ).all()
        
        all_ports = set()
        for origin in origins:
            all_ports.add(origin[0])
        for destination in destinations:
            all_ports.add(destination[0])
        
        ports_list = sorted(list(all_ports))
        
        # Pass to template
        return render_template('maritime_split/dashboard_base.html',
                             routes=routes,
                             total_routes=total_routes,
                             ports_list=ports_list,
                             unique_ports_count=len(ports_list),
                             lang='en')
    """)
    
    engine.dispose()
    
    return dashboard_data

def main():
    """Main function"""
    print("\n🚢 BergNavn REAL Route Data Checker")
    print("="*70)
    print("This shows what's ACTUALLY in your database")
    print("="*70)
    
    try:
        # 1. Get database connection
        engine = get_database_connection()
        
        # 2. Check all tables
        tables = check_all_tables(engine)
        
        # 3. Analyze routes table
        routes_data = analyze_routes_table(engine)
        
        # 4. Check what dashboard sees
        dashboard_data = check_what_dashboard_sees()
        
        # 5. Show fix
        fix_dashboard_data_source()
        
        # Summary
        print("\n" + "="*70)
        print("✅ SUMMARY")
        print("="*70)
        
        if routes_data:
            print(f"\n📊 REAL DATA IN DATABASE:")
            print(f"   • 'routes' table has: {routes_data['total_routes']} routes")
            print(f"   • Unique origins: {routes_data['unique_origins']}")
            print(f"   • Unique destinations: {routes_data['unique_destinations']}")
        
        print(f"\n👁️  DASHBOARD CURRENTLY SEES:")
        print(f"   • Active routes: {dashboard_data['active_routes']}")
        print(f"   • Ports: {dashboard_data['port_count']}")
        
        print(f"\n🎯 YOUR DASHBOARD SHOULD SHOW:")
        print(f"   • Actual Routes: {dashboard_data['active_routes']}")
        print(f"   • Port Coverage: {dashboard_data['port_count']}/10 Norwegian cities")
        
        print("\n🔧 NEXT STEPS:")
        print("   1. Run: python app.py to start server")
        print("   2. Visit: http://localhost:5000/maritime")
        print("   3. Dashboard should now show REAL numbers")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n💡 TROUBLESHOOTING:")
        print("   • Check DATABASE_URL in .env file")
        print("   • Make sure PostgreSQL is running")
        print("   • Check database connection")
        return False
    
    finally:
        if 'engine' in locals():
            engine.dispose()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)