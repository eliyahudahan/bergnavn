#!/usr/bin/env python3
"""
Discover the REAL route count from ALL available data sources.
Does NOT assume any number - discovers actual data.
"""

import os
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import glob

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class RealRouteDiscovery:
    """Discover real route counts from ALL sources"""
    
    def __init__(self):
        self.results = {
            'database': {},
            'json_files': {},
            'rtz_files': {},
            'dashboard_template': {},
            'summary': {}
        }
    
    def check_database(self):
        """Check ALL possible database sources"""
        print("\n" + "="*70)
        print("🔍 DATABASE SOURCES")
        print("="*70)
        
        # Get database URL
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not found in .env")
            return
        
        print(f"🔗 Database: {db_url}")
        
        try:
            engine = create_engine(db_url)
            
            # Get all tables
            with engine.connect() as conn:
                tables_result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                
                tables = [row[0] for row in tables_result]
                print(f"\n📋 Found {len(tables)} tables in database")
                
                # Check each table for route data
                for table in tables:
                    if 'route' in table.lower():
                        try:
                            # Count rows
                            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                            
                            # Get sample data
                            sample = conn.execute(text(f"SELECT * FROM {table} LIMIT 1")).fetchone()
                            columns = []
                            if sample:
                                columns = list(sample._fields)
                            
                            self.results['database'][table] = {
                                'row_count': count,
                                'columns': columns,
                                'sample_available': bool(sample)
                            }
                            
                            print(f"\n📊 Table: {table}")
                            print(f"   Rows: {count}")
                            
                            # If it has data, show more info
                            if count > 0 and table == 'routes':
                                routes = conn.execute(text("""
                                    SELECT name, origin, destination, total_distance_nm
                                    FROM routes
                                    WHERE is_active = true
                                    LIMIT 3
                                """)).fetchall()
                                
                                if routes:
                                    print("   Sample routes:")
                                    for route in routes:
                                        print(f"     • {route.name}: {route.origin} → {route.destination}")
                            
                        except Exception as e:
                            print(f"   ❌ Error reading {table}: {e}")
            
            engine.dispose()
            
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    def check_json_files(self):
        """Check JSON files in the assets directory"""
        print("\n" + "="*70)
        print("📁 JSON FILE SOURCES")
        print("="*70)
        
        # Look for JSON files
        json_pattern = os.path.join(project_root, "backend", "assets", "routeinfo_routes", "**", "*.json")
        json_files = glob.glob(json_pattern, recursive=True)
        
        print(f"\n🔍 Found {len(json_files)} JSON files")
        
        total_routes_in_json = 0
        
        for json_file in json_files[:5]:  # Check first 5 files
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    
                route_count = 0
                if isinstance(data, list):
                    route_count = len(data)
                elif isinstance(data, dict) and 'routes' in data:
                    route_count = len(data['routes'])
                
                self.results['json_files'][os.path.basename(json_file)] = {
                    'path': json_file,
                    'route_count': route_count
                }
                
                total_routes_in_json += route_count
                print(f"   • {os.path.basename(json_file):30} = {route_count:3} routes")
                
            except Exception as e:
                print(f"   • {os.path.basename(json_file):30} = ERROR: {e}")
        
        if len(json_files) > 5:
            print(f"   ... and {len(json_files) - 5} more files")
        
        self.results['summary']['json_routes'] = total_routes_in_json
    
    def check_rtz_files(self):
        """Check RTZ files directly"""
        print("\n" + "="*70)
        print("🗺️ RTZ FILE SOURCES")
        print("="*70)
        
        # Look for RTZ files
        rtz_pattern = os.path.join(project_root, "backend", "assets", "routeinfo_routes", "**", "*.rtz")
        rtz_files = glob.glob(rtz_pattern, recursive=True)
        
        # Look for ZIP files with RTZ
        zip_pattern = os.path.join(project_root, "backend", "assets", "routeinfo_routes", "**", "*.zip")
        zip_files = glob.glob(zip_pattern, recursive=True)
        
        print(f"\n📦 Found:")
        print(f"   • {len(rtz_files)} .rtz files")
        print(f"   • {len(zip_files)} .zip files (may contain multiple .rtz)")
        
        # Count by city
        city_counts = {}
        for file in rtz_files + zip_files:
            # Extract city from path
            parts = file.split(os.sep)
            for part in parts:
                if part in ['alesund', 'andalsnes', 'bergen', 'drammen', 'flekkefjord',
                           'kristiansand', 'oslo', 'sandefjord', 'stavanger', 'trondheim']:
                    city_counts[part] = city_counts.get(part, 0) + 1
                    break
        
        print(f"\n🌍 Files by city:")
        for city, count in sorted(city_counts.items()):
            print(f"   • {city.title():15} = {count:2} files")
        
        self.results['rtz_files'] = {
            'rtz_count': len(rtz_files),
            'zip_count': len(zip_files),
            'city_counts': city_counts
        }
    
    def analyze_dashboard_template(self):
        """Analyze what the dashboard template expects"""
        print("\n" + "="*70)
        print("📊 DASHBOARD TEMPLATE ANALYSIS")
        print("="*70)
        
        template_path = os.path.join(project_root, "backend", "templates", "maritime_split", "dashboard_base.html")
        
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
            
            # Find what variables the template uses
            variables = []
            if 'routes|length' in content:
                variables.append('routes (list)')
            if 'ports_list|length' in content:
                variables.append('ports_list (list)')
            if 'route_count' in content:
                variables.append('route_count (number)')
            
            print(f"\n📋 Template uses variables:")
            for var in variables:
                print(f"   • {var}")
            
            # Check what counts it shows
            if 'Actual RTZ Routes' in content:
                print("\n🎯 Template shows: 'Actual RTZ Routes' badge")
            
            self.results['dashboard_template'] = {
                'variables_needed': variables,
                'shows_actual_routes': 'Actual RTZ Routes' in content
            }
        else:
            print("❌ Dashboard template not found")
    
    def check_flask_routes_file(self):
        """Check what maritime_routes.py actually returns"""
        print("\n" + "="*70)
        print("🐍 FLASK ROUTES ANALYSIS")
        print("="*70)
        
        routes_file = os.path.join(project_root, "backend", "routes", "maritime_routes.py")
        
        if os.path.exists(routes_file):
            with open(routes_file, 'r') as f:
                content = f.read()
            
            print("\n🔍 Analyzing maritime_dashboard() function...")
            
            # Look for imports
            imports = []
            if 'from backend.services.route_service import route_service' in content:
                imports.append('route_service')
            if 'from backend.services.rtz_parser import discover_rtz_files' in content:
                imports.append('rtz_parser')
            if 'from backend.models.route import Route' in content:
                imports.append('Route model')
            
            print(f"   Imports found: {', '.join(imports) if imports else 'None'}")
            
            # Find what data source it uses
            data_sources = []
            if 'route_service.get_empirical_count()' in content:
                data_sources.append('RouteService (empirical)')
            if 'discover_rtz_files(' in content:
                data_sources.append('RTZ Parser (discover)')
            if 'Route.query.filter_by(' in content:
                data_sources.append('Database (Route model)')
            
            print(f"   Data sources used: {', '.join(data_sources) if data_sources else 'Unknown'}")
            
            self.results['flask_routes'] = {
                'imports': imports,
                'data_sources': data_sources
            }
        else:
            print("❌ maritime_routes.py not found")
    
    def discover_real_count(self):
        """Discover the REAL count by examining all sources"""
        print("\n" + "="*70)
        print("🎯 DISCOVERING REAL ROUTE COUNT")
        print("="*70)
        
        # 1. Check database
        self.check_database()
        
        # 2. Check JSON files
        self.check_json_files()
        
        # 3. Check RTZ files
        self.check_rtz_files()
        
        # 4. Analyze templates
        self.analyze_dashboard_template()
        
        # 5. Check Flask routes
        self.check_flask_routes_file()
        
        # 6. Calculate REAL counts
        self.calculate_real_counts()
        
        # 7. Show recommendations
        self.show_recommendations()
    
    def calculate_real_counts(self):
        """Calculate what the real counts should be"""
        print("\n" + "="*70)
        print("🧮 CALCULATING REAL COUNTS")
        print("="*70)
        
        # Get counts from all sources
        db_counts = {}
        for table, data in self.results['database'].items():
            db_counts[table] = data['row_count']
        
        json_count = self.results['summary'].get('json_routes', 0)
        
        print(f"\n📊 COUNTS FROM EACH SOURCE:")
        for table, count in db_counts.items():
            print(f"   • Database table '{table}': {count}")
        
        print(f"   • JSON files (estimated): {json_count}")
        
        # Determine which is the REAL source
        real_count = 0
        real_source = None
        
        # Prefer 'routes' table if it has data
        if 'routes' in db_counts and db_counts['routes'] > 0:
            real_count = db_counts['routes']
            real_source = "Database 'routes' table"
        
        # Otherwise use rtz_routes if available
        elif 'rtz_routes' in db_counts and db_counts['rtz_routes'] > 0:
            real_count = db_counts['rtz_routes']
            real_source = "Database 'rtz_routes' table (old)"
        
        # Otherwise use JSON files
        elif json_count > 0:
            real_count = json_count
            real_source = "JSON files in assets"
        
        # Save results
        self.results['summary']['real_count'] = real_count
        self.results['summary']['real_source'] = real_source
        
        print(f"\n🎯 REAL COUNT DISCOVERED:")
        print(f"   • Count: {real_count}")
        print(f"   • Source: {real_source}")
    
    def show_recommendations(self):
        """Show what to do next"""
        print("\n" + "="*70)
        print("🔧 RECOMMENDATIONS")
        print("="*70)
        
        real_count = self.results['summary'].get('real_count', 0)
        real_source = self.results['summary'].get('real_source', 'Unknown')
        
        print(f"\n✅ Your system has {real_count} REAL maritime routes")
        print(f"   Source: {real_source}")
        
        # Check what the dashboard is currently showing
        dashboard_source = self.results.get('flask_routes', {}).get('data_sources', [])
        
        print(f"\n🔍 Dashboard currently gets data from: {', '.join(dashboard_source) if dashboard_source else 'Unknown'}")
        
        if real_source.startswith("Database 'routes' table"):
            if "Database (Route model)" not in dashboard_source:
                print("\n⚠️  PROBLEM: Dashboard is NOT reading from the real database source!")
                print("💡 SOLUTION: Update maritime_routes.py to read from Route.query")
                
                print("\n💻 Add this to maritime_routes.py:")
                print("""
        # Get REAL data from database
        from backend.models.route import Route
        routes = Route.query.filter_by(is_active=True).all()
        total_routes = len(routes)
        """)
        
        elif real_source == "Database 'rtz_routes' table (old)":
            print("\n⚠️  WARNING: Using old 'rtz_routes' table")
            print("💡 SUGGESTION: Migrate data to 'routes' table")
        
        elif real_source == "JSON files in assets":
            print("\n⚠️  WARNING: Using JSON files instead of database")
            print("💡 SUGGESTION: Import JSON data to database")
        
        print(f"\n🎯 Your dashboard should show: {real_count} Actual Routes")
        print(f"   From source: {real_source}")
        
        # Save results to file
        results_file = os.path.join(project_root, "real_route_discovery.json")
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📁 Full analysis saved to: {results_file}")

def main():
    """Main function"""
    print("\n🚢 BergNavn REAL Route Discovery")
    print("="*70)
    print("Discovering ACTUAL route counts from ALL sources")
    print("="*70)
    
    try:
        # Create discoverer
        discoverer = RealRouteDiscovery()
        
        # Discover real counts
        discoverer.discover_real_count()
        
        print("\n" + "="*70)
        print("✅ DISCOVERY COMPLETE")
        print("="*70)
        
        real_count = discoverer.results['summary'].get('real_count', 0)
        
        print(f"\n🎯 THE TRUTH IS:")
        print(f"   Your system has {real_count} REAL maritime routes")
        
        print(f"\n🔧 To fix your dashboard:")
        print(f"   1. Update maritime_routes.py to read from correct source")
        print(f"   2. Restart the server: python app.py")
        print(f"   3. Visit: http://localhost:5000/maritime")
        print(f"   4. Dashboard should now show {real_count} Actual Routes")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)