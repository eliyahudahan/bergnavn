#!/usr/bin/env python3
"""
Complete the port name fix - convert all coordinates to city names
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def complete_port_fix():
    """Fix all remaining coordinate-based port names"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found")
        return
    
    engine = create_engine(db_url)
    
    # More comprehensive coordinate mapping
    coord_to_city = {
        # Kristiansand area
        'Position 58.06, 8.10': 'Kristiansand',
        'Position 58.13, 7.99': 'Oksøy',
        'Position 58.15, 8.05': 'Oksøy East',
        
        # Flekkefjord
        'Position 58.15, 6.48': 'Flekkefjord West',
        'Position 58.29, 6.66': 'Flekkefjord East',
        
        # Ålesund area
        'Position 62.23, 5.17': 'Stad West',
        'Position 62.23, 5.18': 'Stad East',
        'Position 62.46, 6.34': 'Ålesund South',
        'Position 62.49, 6.39': 'Ålesund North',
        'Position 62.51, 5.68': 'Breisundet',
        'Position 62.56, 7.63': 'Åndalsnes',
        'Position 62.57, 7.68': 'Åndalsnes East',
        
        # Northern Norway
        'Position 68.21, 15.62': 'Lødingen',
        'Position 68.22, 15.61': 'Lødingen West',
        'Position 69.25, 19.36': 'Bergeneset',
        'Position 69.25, 19.37': 'Bergeneset East',
        
        # Misc
        'Position 58.97, 10.26': 'Sandefjord West',
        'Position 58.97, 10.31': 'Sandefjord East',
        'Position 59.11, 10.23': 'Sydostgrunnen',
        'Position 59.87, 6.37': 'Fjæra',
        
        # Clean up any "Position" strings
        'Position ': '',  # Remove "Position " prefix
    }
    
    with engine.connect() as conn:
        updated = 0
        
        # First pass: specific coordinates
        for coord, city in coord_to_city.items():
            if coord == 'Position ':
                continue
                
            # Update origin
            result = conn.execute(text("""
                UPDATE routes 
                SET origin = :city 
                WHERE origin LIKE :coord_pattern
            """), {'city': city, 'coord_pattern': f'{coord}%'})
            
            updated += result.rowcount
            
            # Update destination
            result = conn.execute(text("""
                UPDATE routes 
                SET destination = :city 
                WHERE destination LIKE :coord_pattern
            """), {'city': city, 'coord_pattern': f'{coord}%'})
            
            updated += result.rowcount
        
        # Second pass: remove "Position " prefix from any remaining
        result = conn.execute(text("""
            UPDATE routes 
            SET origin = REPLACE(origin, 'Position ', '')
            WHERE origin LIKE 'Position %'
        """))
        updated += result.rowcount
        
        result = conn.execute(text("""
            UPDATE routes 
            SET destination = REPLACE(destination, 'Position ', '')
            WHERE destination LIKE 'Position %'
        """))
        updated += result.rowcount
        
        conn.commit()
        print(f"✅ Updated {updated} port names")
        
        # Show results
        routes = conn.execute(text("""
            SELECT DISTINCT origin, COUNT(*) as count
            FROM routes 
            GROUP BY origin
            ORDER BY count DESC
            LIMIT 15
        """)).fetchall()
        
        print("\n📋 Top origins after fix:")
        for route in routes:
            print(f"   {route.origin}: {route.count} routes")

if __name__ == "__main__":
    print("🔧 Completing port name fix...")
    complete_port_fix()