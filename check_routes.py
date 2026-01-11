#!/usr/bin/env python3
"""Check what's in the routes database - FIXED VERSION."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable scheduler initialization
os.environ['FLASK_SKIP_SCHEDULER'] = '1'

from app import create_app
from backend.models import Route

# Create app with minimal configuration
app = create_app()

with app.app_context():
    total = Route.query.count()
    print(f"📊 Total routes in database: {total}")
    
    if total > 0:
        print("\n📋 First 10 routes:")
        routes = Route.query.limit(10).all()
        
        for i, route in enumerate(routes, 1):
            print(f"\n{i}. ID: {route.id}")
            print(f"   Name: {route.name}")
            print(f"   Created: {route.created_at if hasattr(route, 'created_at') else 'N/A'}")
            
            # Try to get additional attributes
            if hasattr(route, 'origin') and route.origin:
                print(f"   From: {route.origin}")
            if hasattr(route, 'destination') and route.destination:
                print(f"   To: {route.destination}")
            if hasattr(route, 'total_distance_nm') and route.total_distance_nm:
                print(f"   Distance: {route.total_distance_nm} NM")
            if hasattr(route, 'source_city') and route.source_city:
                print(f"   City: {route.source_city}")
    
    # Check for duplicates
    print("\n🔍 Checking for duplicates...")
    from sqlalchemy import func
    from backend.extensions import db
    
    duplicates = (
        db.session.query(
            Route.name,
            func.count(Route.id).label('count')
        )
        .group_by(Route.name)
        .having(func.count(Route.id) > 1)
        .all()
    )
    
    if duplicates:
        print(f"⚠️ Found {len(duplicates)} routes with duplicates:")
        for name, count in duplicates:
            print(f"  • {name}: {count} copies")
            
            # Show details of duplicates
            dup_routes = Route.query.filter_by(name=name).all()
            for dup in dup_routes[:2]:  # Show first 2 duplicates
                print(f"    - ID {dup.id}: created {dup.created_at if hasattr(dup, 'created_at') else 'N/A'}")
    else:
        print("✅ No duplicates found!")
    
    # Summary
    print("\n📈 Summary:")
    print(f"Total routes: {total}")
    
    if total > 0:
        unique_names = db.session.query(func.count(Route.name.distinct())).scalar()
        print(f"Unique route names: {unique_names}")
        print(f"Duplicate entries: {total - unique_names}")
        
        # Show routes by source city
        print("\n🏙️ Routes by source city:")
        city_counts = {}
        for route in Route.query.all():
            city = getattr(route, 'source_city', 'Unknown')
            city_counts[city] = city_counts.get(city, 0) + 1
        
        for city, count in sorted(city_counts.items()):
            print(f"  • {city}: {count} routes")