#!/usr/bin/env python3
"""
Fix duplicate routes in BergNavn database - FIXED VERSION.
Run: python fix_duplicates.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable scheduler initialization
os.environ['FLASK_SKIP_SCHEDULER'] = '1'

from app import create_app
from backend.models import Route
from backend.extensions import db
from sqlalchemy import func, and_

def analyze_routes():
    """Analyze route data."""
    app = create_app()
    
    with app.app_context():
        print("🔍 Analyzing route database...")
        
        total = Route.query.count()
        print(f"📊 Total routes in database: {total}")
        
        if total == 0:
            print("❌ Database is empty!")
            return {'total': 0, 'unique': 0, 'duplicates': 0}
        
        # Get unique count
        unique_count = db.session.query(func.count(Route.name.distinct())).scalar()
        duplicates = total - unique_count
        
        print(f"🎯 Unique route names: {unique_count}")
        print(f"⚠️  Duplicate entries: {duplicates}")
        
        # Find actual duplicates
        duplicate_query = (
            db.session.query(
                Route.name,
                func.count(Route.id).label('count')
            )
            .group_by(Route.name)
            .having(func.count(Route.id) > 1)
            .all()
        )
        
        if duplicate_query:
            print(f"\n📋 Routes with duplicates ({len(duplicate_query)}):")
            for name, count in duplicate_query:
                print(f"  • {name}: {count} copies")
        
        return {
            'total': total,
            'unique': unique_count,
            'duplicates': duplicates,
            'duplicate_list': duplicate_query
        }

def fix_duplicates():
    """Remove duplicate routes."""
    app = create_app()
    
    with app.app_context():
        print("🧹 Removing duplicate routes...")
        
        # Find duplicates to remove
        duplicates = (
            db.session.query(
                Route.name,
                func.min(Route.id).label('keep_id'),  # Keep the oldest (smallest ID)
                func.count(Route.id).label('total_count')
            )
            .group_by(Route.name)
            .having(func.count(Route.id) > 1)
            .subquery()
        )
        
        # Find IDs to delete (all except the one to keep)
        routes_to_delete = (
            db.session.query(Route.id)
            .join(duplicates, Route.name == duplicates.c.name)
            .filter(Route.id != duplicates.c.keep_id)
            .all()
        )
        
        delete_ids = [r[0] for r in routes_to_delete]
        
        if not delete_ids:
            print("✅ No duplicates to remove!")
            return 0
        
        print(f"🗑️  Found {len(delete_ids)} duplicate routes to delete")
        
        # Show what we're deleting
        print("\n📋 Routes to delete:")
        for route_id in delete_ids[:10]:  # Show first 10
            route = Route.query.get(route_id)
            if route:
                print(f"  • ID {route_id}: {route.name}")
        
        if len(delete_ids) > 10:
            print(f"  ... and {len(delete_ids) - 10} more")
        
        # Ask for confirmation
        response = input(f"\n❓ Delete {len(delete_ids)} duplicate routes? (y/n): ")
        if response.lower() != 'y':
            print("⚠️  Cancelled!")
            return 0
        
        # Delete duplicates
        deleted_count = Route.query.filter(Route.id.in_(delete_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        print(f"✅ Deleted {deleted_count} duplicate routes!")
        
        # Show new stats
        new_total = Route.query.count()
        new_unique = db.session.query(func.count(Route.name.distinct())).scalar()
        
        print(f"\n📊 New statistics:")
        print(f"  Total routes: {new_total} ({new_total - deleted_count} removed)")
        print(f"  Unique routes: {new_unique}")
        
        return deleted_count

def show_route_details():
    """Show detailed route information."""
    app = create_app()
    
    with app.app_context():
        routes = Route.query.order_by(Route.name).all()
        
        print("\n📄 Detailed Route Information:")
        print("=" * 60)
        
        current_name = None
        for route in routes:
            if route.name != current_name:
                current_name = route.name
                print(f"\n🔹 {current_name}:")
            
            info = f"  ID {route.id}: "
            if hasattr(route, 'origin') and route.origin:
                info += f"From {route.origin} "
            if hasattr(route, 'destination') and route.destination:
                info += f"→ {route.destination} "
            if hasattr(route, 'source_city') and route.source_city:
                info += f"[{route.source_city}]"
            if hasattr(route, 'created_at') and route.created_at:
                info += f" (created: {route.created_at})"
            
            print(info)

if __name__ == "__main__":
    print("🛠️  BergNavn Route Duplicate Manager")
    print("=" * 50)
    
    # Show current state
    stats = analyze_routes()
    
    if stats['total'] == 0:
        print("\n❌ No routes in database!")
        print("💡 You need to import RTZ files first.")
        print("   Run: python backend/services/rtz_parser.py")
        sys.exit(1)
    
    if stats['duplicates'] == 0:
        print("\n✅ Database is clean!")
        show_route_details()
    else:
        print(f"\n⚠️  Found {stats['duplicates']} duplicate entries!")
        
        # Show menu
        print("\nOptions:")
        print("  1. Show detailed route information")
        print("  2. Remove duplicates")
        print("  3. Exit")
        
        choice = input("\nSelect option (1-3): ")
        
        if choice == '1':
            show_route_details()
        elif choice == '2':
            fix_duplicates()
            # Show final details
            show_route_details()
        else:
            print("👋 Goodbye!")