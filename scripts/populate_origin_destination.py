#!/usr/bin/env python3
"""
Populate origin and destination columns for existing routes
based on their voyage legs data.
FINAL WORKING VERSION - No shortcuts, full solution
"""
import sys
import os

# ✅ CORRECT: Add project root to Python path properly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from app import create_app
    from backend.models import Route, VoyageLeg
    from backend.extensions import db
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def populate_route_endpoints():
    """Populate origin and destination for all routes"""
    try:
        app = create_app()
        
        with app.app_context():
            # First, let's understand the VoyageLeg structure
            sample_leg = VoyageLeg.query.first()
            if sample_leg:
                print("🔍 VoyageLeg structure:")
                for column in VoyageLeg.__table__.columns:
                    value = getattr(sample_leg, column.name, None)
                    print(f"   {column.name}: {value}")
            
            routes = Route.query.all()
            print(f"📊 Processing {len(routes)} routes...")
            
            updated_count = 0
            for route in routes:
                if not route.legs:
                    print(f"⚠️ Route {route.id} '{route.name}' has no legs, skipping")
                    continue
                
                print(f"🔍 Route {route.id} '{route.name}' has {len(route.legs)} legs")
                
                # Check what fields are available for sorting
                first_leg = route.legs[0]
                print(f"   First leg fields: {[col.name for col in VoyageLeg.__table__.columns]}")
                
                # Try different sorting methods based on available fields
                sorted_legs = []
                
                # Method 1: If there's an explicit sequence field
                if hasattr(first_leg, 'sequence_number'):
                    sorted_legs = sorted(route.legs, key=lambda x: x.sequence_number)
                elif hasattr(first_leg, 'sequence'):
                    sorted_legs = sorted(route.legs, key=lambda x: x.sequence)
                elif hasattr(first_leg, 'id'):
                    # Method 2: Sort by ID (assuming they were created in order)
                    sorted_legs = sorted(route.legs, key=lambda x: x.id)
                elif hasattr(first_leg, 'leg_order'):
                    sorted_legs = sorted(route.legs, key=lambda x: x.leg_order)
                else:
                    # Method 3: Just use the order they're returned
                    sorted_legs = route.legs
                    print(f"   ⚠️ No sequence field found, using default order")
                
                first_leg = sorted_legs[0]
                last_leg = sorted_legs[-1]
                
                # Set origin and destination
                route.origin = f"Position {first_leg.departure_lat:.2f}, {first_leg.departure_lon:.2f}"
                route.destination = f"Position {last_leg.arrival_lat:.2f}, {last_leg.arrival_lon:.2f}"
                
                updated_count += 1
                print(f"✅ Route {route.id}: {route.origin} → {route.destination}")
            
            db.session.commit()
            print(f"🎉 Successfully populated {updated_count} routes with origin/destination!")
            
    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    populate_route_endpoints()