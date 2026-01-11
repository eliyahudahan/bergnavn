#!/usr/bin/env python3
"""
Fix port names in the database from coordinates to actual city names
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def fix_port_names():
    """Convert coordinate-based port names to actual city names"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found")
        return
    
    engine = create_engine(db_url)
    
    # Map coordinates to city names
    coord_to_city = {
        # Trondheim area
        'Position 63.45, 10.36': 'Trondheim',
        'Position 64.26, 9.75': 'Halten',
        'Position 64.86, 11.26': 'Rørvik',
        'Position 63.25, 7.60': 'Grip',
        
        # Bergen area
        'Position 60.40, 5.28': 'Bergen',
        'Position 60.75, 4.65': 'Fedjeosen',
        'Position 60.13, 4.94': 'Marstein',
        
        # Stavanger area
        'Position 58.98, 5.73': 'Stavanger',
        'Position 59.07, 5.35': 'Skudefjorden',
        'Position 58.80, 5.40': 'Feistein',
        
        # Oslo area
        'Position 59.90, 10.70': 'Oslo',
        'Position 59.88, 10.73': 'Oslo',
        'Position 59.73, 10.27': 'Drammen',
        'Position 59.16, 10.66': 'Larvik/Sandefjord',
        
        # And more...
    }
    
    with engine.connect() as conn:
        updated = 0
        
        for coord, city in coord_to_city.items():
            # Update origin
            result = conn.execute(text("""
                UPDATE routes 
                SET origin = :city 
                WHERE origin = :coord
            """), {'city': city, 'coord': coord})
            
            updated += result.rowcount
            
            # Update destination
            result = conn.execute(text("""
                UPDATE routes 
                SET destination = :city 
                WHERE destination = :coord
            """), {'city': city, 'coord': coord})
            
            updated += result.rowcount
        
        conn.commit()
        print(f"✅ Updated {updated} port names")
        
        # Show results
        routes = conn.execute(text("""
            SELECT name, origin, destination 
            FROM routes 
            LIMIT 10
        """)).fetchall()
        
        print("\n📋 Sample routes after fix:")
        for route in routes:
            print(f"   {route.name}: {route.origin} → {route.destination}")

if __name__ == "__main__":
    print("🔧 Fixing port names in database...")
    fix_port_names()