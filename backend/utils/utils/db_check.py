#!/usr/bin/env python3
"""
Check actual database counts and resolve discrepancies
"""

import sys
import os
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from sqlalchemy import create_engine, text, inspect, MetaData
from backend.config import ProductionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_actual_counts():
    """Get actual counts from ALL route-related tables"""
    config = ProductionConfig()
    db_uri = getattr(config, 'SQLALCHEMY_DATABASE_URI', 
                    "postgresql://bergnavn_user:securepass@localhost/bergnavn_db")
    
    engine = create_engine(db_uri)
    
    try:
        # Get metadata to see all tables
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        print("=" * 60)
        print("🔍 DATABASE ROUTE TABLES ANALYSIS")
        print("=" * 60)
        
        # First, list all tables
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        
        print(f"📋 Total tables in database: {len(all_tables)}")
        print("\n📊 Checking ALL route-related tables:")
        
        counts = {}
        total_routes_across_all_tables = 0
        
        for table_name in sorted(all_tables):
            if 'route' in table_name.lower():
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = result.scalar()
                        counts[table_name] = count
                        total_routes_across_all_tables += count
                        
                        # Also get sample data structure
                        sample_query = text(f"SELECT * FROM {table_name} LIMIT 1")
                        sample_result = conn.execute(sample_query)
                        columns = sample_result.keys() if sample_result else []
                        
                        print(f"\n📁 Table: {table_name}")
                        print(f"   Rows: {count}")
                        print(f"   Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                        
                        # If it's a routes table, show some data
                        if table_name == 'routes' and count > 0:
                            routes_query = text("""
                                SELECT id, name, origin, destination, total_distance_nm, created_at 
                                FROM routes 
                                LIMIT 5
                            """)
                            routes = conn.execute(routes_query).fetchall()
                            print(f"\n   Sample routes:")
                            for route in routes:
                                print(f"     • {route.name}: {route.origin} → {route.destination} ({route.total_distance_nm} nm)")
                            
                except Exception as e:
                    print(f"   ❌ Error reading {table_name}: {e}")
        
        # Check for rtz_routes table specifically
        print("\n" + "=" * 60)
        print("🎯 SPECIFIC TABLE CHECKS")
        print("=" * 60)
        
        # Check routes table structure
        print("\n📊 'routes' table detailed analysis:")
        try:
            with engine.connect() as conn:
                # Get column info
                routes_columns = inspector.get_columns('routes')
                print(f"   Columns in 'routes' table: {len(routes_columns)}")
                
                # Get statistics
                stats_query = text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(DISTINCT name) as unique_names,
                        COUNT(DISTINCT origin) as unique_origins,
                        COUNT(DISTINCT destination) as unique_destinations,
                        AVG(total_distance_nm) as avg_distance,
                        MIN(total_distance_nm) as min_distance,
                        MAX(total_distance_nm) as max_distance
                    FROM routes
                """)
                
                stats = conn.execute(stats_query).fetchone()
                print(f"\n   Statistics:")
                print(f"     • Total routes: {stats.total}")
                print(f"     • Unique route names: {stats.unique_names}")
                print(f"     • Unique origins: {stats.unique_origins}")
                print(f"     • Unique destinations: {stats.unique_destinations}")
                print(f"     • Average distance: {stats.avg_distance:.1f} nm")
                print(f"     • Min distance: {stats.min_distance:.1f} nm")
                print(f"     • Max distance: {stats.max_distance:.1f} nm")
                
                # List all origins and destinations
                origins_query = text("""
                    SELECT origin, COUNT(*) as count
                    FROM routes
                    WHERE origin IS NOT NULL
                    GROUP BY origin
                    ORDER BY count DESC
                """)
                
                origins = conn.execute(origins_query).fetchall()
                print(f"\n   Top origins:")
                for origin in origins[:5]:
                    print(f"     • {origin.origin}: {origin.count} routes")
                
        except Exception as e:
            print(f"   ❌ Error analyzing 'routes' table: {e}")
        
        # Check rtz_routes table if it exists
        print("\n📊 'rtz_routes' table check:")
        if 'rtz_routes' in all_tables:
            try:
                with engine.connect() as conn:
                    rtz_count = conn.execute(text("SELECT COUNT(*) FROM rtz_routes")).scalar()
                    print(f"   'rtz_routes' exists with {rtz_count} rows")
                    
                    # Compare with routes table
                    print(f"\n   📈 COMPARISON:")
                    print(f"     • 'routes' table: {counts.get('routes', 0)} rows")
                    print(f"     • 'rtz_routes' table: {rtz_count} rows")
                    
                    if rtz_count > 0 and 'routes' in counts:
                        print(f"     • Total unique routes across tables: {total_routes_across_all_tables}")
                        print(f"     • Duplicate management needed: {'YES' if total_routes_across_all_tables > max(counts.get('routes', 0), rtz_count) else 'NO'}")
                        
            except Exception as e:
                print(f"   ❌ Error checking 'rtz_routes': {e}")
        else:
            print("   'rtz_routes' table does not exist")
        
        # Check which tables the dashboard might be reading
        print("\n" + "=" * 60)
        print("🎛️  DASHBOARD DATA SOURCE ANALYSIS")
        print("=" * 60)
        
        # Check actual JSON file structure
        json_files_count = 0
        json_routes_count = 0
        
        # Look for JSON files in the routeinfo_routes directory
        import glob
        json_pattern = os.path.join(project_root, "backend", "assets", "routeinfo_routes", "**", "*.json")
        json_files = glob.glob(json_pattern, recursive=True)
        
        print(f"\n📁 JSON files found: {len(json_files)}")
        
        if json_files:
            # Count routes in first few JSON files
            import json
            for json_file in json_files[:3]:  # Check first 3
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            json_routes_count += len(data)
                        elif isinstance(data, dict) and 'routes' in data:
                            json_routes_count += len(data['routes'])
                except:
                    pass
            
            print(f"   Estimated routes in JSON files: {json_routes_count}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 FINAL RECOMMENDATIONS")
        print("=" * 60)
        
        recommendations = []
        
        if 'rtz_routes' in all_tables and 'routes' in counts:
            if counts['routes'] > 0 and counts.get('rtz_routes', 0) > 0:
                recommendations.append("⚠️  You have TWO route tables: 'routes' AND 'rtz_routes'")
                recommendations.append("   Need to migrate data or choose one source")
        
        if total_routes_across_all_tables > 0:
            recommendations.append(f"📊 Total route entries across all tables: {total_routes_across_all_tables}")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        
        print("\n💡 SOLUTIONS:")
        print("1. Run: python fix_dashboard_counts.py")
        print("2. Check which table your dashboard reads")
        print("3. Update dashboard to read from correct source")
        
        return {
            'all_tables': all_tables,
            'counts': counts,
            'total_routes': total_routes_across_all_tables,
            'json_files': len(json_files),
            'json_routes': json_routes_count
        }
        
    finally:
        engine.dispose()

def fix_dashboard_counts():
    """Fix the dashboard to show correct counts"""
    print("\n" + "=" * 60)
    print("🔧 FIXING DASHBOARD COUNTS")
    print("=" * 60)
    
    config = ProductionConfig()
    db_uri = getattr(config, 'SQLALCHEMY_DATABASE_URI', 
                    "postgresql://bergnavn_user:securepass@localhost/bergnavn_db")
    
    engine = create_engine(db_uri)
    
    try:
        with engine.connect() as conn:
            # 1. Check which table has the real data
            print("\n📋 Checking data sources...")
            
            # Count routes in each table
            tables_to_check = ['routes', 'rtz_routes']
            
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"   {table}: {count} rows")
                except:
                    print(f"   {table}: Does not exist or error")
            
            # 2. Get actual route count from 'routes' table
            print("\n📊 Getting actual route data from 'routes' table...")
            
            routes_query = text("""
                SELECT 
                    COUNT(*) as total_routes,
                    COUNT(DISTINCT origin) as unique_origins,
                    COUNT(DISTINCT destination) as unique_destinations,
                    STRING_AGG(DISTINCT origin, ', ') as origin_list
                FROM routes
            """)
            
            routes_stats = conn.execute(routes_query).fetchone()
            
            if routes_stats:
                print(f"   ✅ Actual routes in database: {routes_stats.total_routes}")
                print(f"   Unique origins: {routes_stats.unique_origins}")
                print(f"   Unique destinations: {routes_stats.unique_destinations}")
                print(f"   Origins: {routes_stats.origin_list}")
                
                # Get port list
                ports_query = text("""
                    SELECT DISTINCT origin as port
                    FROM routes 
                    WHERE origin IS NOT NULL AND origin != 'Unknown'
                    UNION
                    SELECT DISTINCT destination as port
                    FROM routes 
                    WHERE destination IS NOT NULL AND destination != 'Unknown'
                    ORDER BY port
                """)
                
                ports = conn.execute(ports_query).fetchall()
                port_list = [port.port for port in ports]
                
                print(f"\n🌍 Ports covered: {len(port_list)}")
                for port in port_list[:10]:  # Show first 10
                    print(f"   • {port}")
                
                if len(port_list) > 10:
                    print(f"   ... and {len(port_list) - 10} more")
                
                return {
                    'total_routes': routes_stats.total_routes,
                    'unique_origins': routes_stats.unique_origins,
                    'unique_destinations': routes_stats.unique_destinations,
                    'ports': port_list,
                    'port_count': len(port_list)
                }
            else:
                print("   ❌ No data in 'routes' table")
                return None
                
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("🚢 BergNavn Database Route Analyzer")
    print("=" * 50)
    
    # Step 1: Analyze database
    analysis = get_actual_counts()
    
    print("\n" + "=" * 60)
    print("🛠️  RUNNING FIXES")
    print("=" * 60)
    
    # Step 2: Fix counts
    fixed_data = fix_dashboard_counts()
    
    if fixed_data:
        print("\n✅ FIXED COUNTS:")
        print(f"   Total routes: {fixed_data['total_routes']}")
        print(f"   Ports: {fixed_data['port_count']}")
        print(f"   Dashboard should show: {fixed_data['total_routes']} Actual Routes")
        print(f"   Port coverage: {fixed_data['port_count']}/10 ports")
        
        print("\n💡 Update your dashboard template to use these numbers!")