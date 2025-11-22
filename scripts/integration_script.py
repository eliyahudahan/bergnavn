#!/usr/bin/env python3
"""
RTZ to Database Integration Script
Parses all RTZ files and saves them to the database using proper Route → VoyageLeg structure
FIXED: Added Flask application context for database verification
"""

import os
import sys
from pathlib import Path
import logging
from typing import Dict, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_all_rtz_files() -> Dict[str, int]:
    """
    Parse all RTZ files and save to database using Route → VoyageLeg structure
    
    Returns:
        Dict with integration statistics
    """
    base_path = "backend/assets/routeinfo_routes"
    
    if not os.path.exists(base_path):
        logger.error(f"Base path not found: {base_path}")
        return {'error': 'Base path not found'}
    
    # Find all RTZ files
    rtz_files = list(Path(base_path).rglob("*.rtz"))
    logger.info(f"Found {len(rtz_files)} RTZ files")
    
    if not rtz_files:
        logger.warning("No RTZ files found")
        return {'total_files': 0, 'routes_parsed': 0, 'routes_saved': 0}
    
    total_routes_parsed = 0
    total_routes_saved = 0
    
    for rtz_file in rtz_files:
        try:
            logger.info(f"Processing: {rtz_file}")
            
            # Parse RTZ file
            from backend.services.rtz_parser import parse_rtz
            routes = parse_rtz(str(rtz_file))
            
            if not routes:
                logger.warning(f"  No routes parsed from {rtz_file.name}")
                continue
            
            total_routes_parsed += len(routes)
            logger.info(f"  Parsed {len(routes)} routes with {sum(len(r['waypoints']) for r in routes)} total waypoints")
            
            # Save to database using proper Route → VoyageLeg structure
            from backend.services.rtz_parser import save_rtz_routes_to_db
            saved_count = save_rtz_routes_to_db(routes)
            total_routes_saved += saved_count
            
            if saved_count > 0:
                logger.info(f"  ✅ Saved {saved_count} routes to database")
            else:
                logger.warning(f"  ⚠️  No routes saved from {rtz_file.name} (possibly already exist)")
            
        except Exception as e:
            logger.error(f"  ❌ Error processing {rtz_file}: {e}")
            continue
    
    # Summary
    logger.info("=" * 50)
    logger.info("INTEGRATION SUMMARY:")
    logger.info(f"  Total RTZ files: {len(rtz_files)}")
    logger.info(f"  Total routes parsed: {total_routes_parsed}")
    logger.info(f"  Total routes saved to DB: {total_routes_saved}")
    if total_routes_parsed > 0:
        success_rate = round(total_routes_saved / total_routes_parsed * 100, 1)
        logger.info(f"  Success rate: {success_rate}%")
    logger.info("=" * 50)
    
    return {
        'total_files': len(rtz_files),
        'routes_parsed': total_routes_parsed,
        'routes_saved': total_routes_saved,
        'success_rate': round(total_routes_saved / max(total_routes_parsed, 1) * 100, 1)
    }

def verify_database_integration() -> Dict[str, int]:
    """
    Verify that routes are properly integrated in database
    FIXED: Added Flask application context to resolve 'Working outside of application context' error
    """
    try:
        # ✅ FIX: Import Flask app and create application context
        from app import create_app
        from backend.models import Route, VoyageLeg
        from backend.extensions import db
        
        # Create Flask app and application context for database operations
        app = create_app()
        
        with app.app_context():
            # Count routes and voyage legs
            total_routes = db.session.query(Route).count()
            total_voyage_legs = db.session.query(VoyageLeg).count()
            
            # Count routes with voyage legs
            routes_with_legs = db.session.query(Route).join(VoyageLeg).distinct().count()
            
            # Calculate average legs per route
            avg_legs_per_route = total_voyage_legs / max(total_routes, 1)
            
            # Get some route examples
            sample_routes = db.session.query(Route.name, Route.total_distance_nm).limit(5).all()
            
            logger.info("DATABASE VERIFICATION:")
            logger.info(f"  Total routes in DB: {total_routes}")
            logger.info(f"  Total voyage legs in DB: {total_voyage_legs}")
            logger.info(f"  Routes with voyage legs: {routes_with_legs}")
            logger.info(f"  Average legs per route: {avg_legs_per_route:.1f}")
            
            if sample_routes:
                logger.info("  Sample routes:")
                for name, distance in sample_routes:
                    logger.info(f"    - {name}: {distance} nm")
            
            return {
                'total_routes': total_routes,
                'total_voyage_legs': total_voyage_legs,
                'routes_with_legs': routes_with_legs,
                'avg_legs_per_route': round(avg_legs_per_route, 1),
                'sample_routes_count': len(sample_routes)
            }
            
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return {'error': str(e)}

def cleanup_existing_data() -> Dict[str, int]:
    """
    Optional: Clean up existing test data before new integration
    Use with caution - only for development!
    """
    try:
        from app import create_app  # ✅ FIX: Added Flask app import
        from backend.models import Route, VoyageLeg
        from backend.extensions import db
        
        # Create Flask app and application context
        app = create_app()
        
        with app.app_context():
            # Count before cleanup
            routes_before = db.session.query(Route).count()
            legs_before = db.session.query(VoyageLeg).count()
            
            # Delete voyage legs first (foreign key constraint)
            legs_deleted = db.session.query(VoyageLeg).delete()
            db.session.commit()
            
            # Then delete routes
            routes_deleted = db.session.query(Route).delete()
            db.session.commit()
            
            logger.info(f"🧹 Cleanup completed:")
            logger.info(f"  Deleted {routes_deleted} routes")
            logger.info(f"  Deleted {legs_deleted} voyage legs")
            
            return {
                'routes_deleted': routes_deleted,
                'legs_deleted': legs_deleted,
                'routes_before': routes_before,
                'legs_before': legs_before
            }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        db.session.rollback()
        return {'error': str(e)}

def main():
    """Main integration function"""
    print("🚀 Starting RTZ to Database Integration")
    print("Using Route → VoyageLeg structure (waypoints stored as leg coordinates)")
    print("=" * 50)
    
    try:
        # Optional: Clean up existing data (uncomment if needed)
        # print("🧹 Cleaning up existing data...")
        # cleanup_results = cleanup_existing_data()
        # if 'error' in cleanup_results:
        #     print(f"⚠️  Cleanup warning: {cleanup_results['error']}")
        # else:
        #     print(f"✅ Cleanup completed: {cleanup_results['routes_deleted']} routes, {cleanup_results['legs_deleted']} legs")
        # print()
        
        # Step 1: Integrate all RTZ files
        print("📁 Processing 80 RTZ files across all cities...")
        integration_results = integrate_all_rtz_files()
        
        if 'error' in integration_results:
            print(f"❌ Integration failed: {integration_results['error']}")
            return 1
        
        print(f"✅ Integration completed:")
        print(f"   Files processed: {integration_results['total_files']}")
        print(f"   Routes parsed: {integration_results['routes_parsed']}")
        print(f"   Routes saved: {integration_results['routes_saved']}")
        print(f"   Success rate: {integration_results['success_rate']}%")
        
        # Step 2: Verify database integration
        print("\n🔍 Verifying database integration...")
        verification_results = verify_database_integration()
        
        if 'error' in verification_results:
            print(f"❌ Verification failed: {verification_results['error']}")
            return 1
        
        print(f"✅ Database verification:")
        print(f"   Total routes: {verification_results['total_routes']}")
        print(f"   Total voyage legs: {verification_results['total_voyage_legs']}")
        print(f"   Routes with legs: {verification_results['routes_with_legs']}")
        print(f"   Avg legs per route: {verification_results['avg_legs_per_route']}")
        
        print("\n🎉 INTEGRATION COMPLETED SUCCESSFULLY!")
        print("💡 All RTZ routes are now available in the database for the recommendation engine!")
        return 0
        
    except Exception as e:
        print(f"❌ Integration failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())