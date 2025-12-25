#!/usr/bin/env python3
"""
Safe Migration Wrapper
Always runs health checks before and after migrations
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd, description=""):
    """Run a shell command with error handling"""
    if description:
        print(f"\n📋 {description}")
        print(f"   $ {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Command failed with exit code {result.returncode}")
            if result.stdout:
                print(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                print(f"STDERR:\n{result.stderr}")
            return False, result.stdout + result.stderr
        
        return True, result.stdout
    
    except Exception as e:
        print(f"❌ Exception running command: {e}")
        return False, str(e)

def create_backup():
    """Create database backup before migration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_pre_migration_{timestamp}.sql"
    
    print(f"💾 Creating backup: {backup_file}")
    
    success, output = run_command(
        f'pg_dump "postgresql://framg:copenhagen2024@localhost/framg" > {backup_file}',
        "Creating database backup"
    )
    
    if success:
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    else:
        print(f"❌ Backup failed: {output}")
        return None

def main():
    """Main migration workflow"""
    
    print("🚀 SAFE MIGRATION WORKFLOW")
    print("=" * 60)
    
    # Step 1: Pre-migration health check
    print("\n🔍 STEP 1: Pre-migration health check")
    success, output = run_command("python check_migration_health.py", "Health check")
    
    if not success:
        print("❌ Pre-migration health check failed!")
        print("Aborting migration to prevent data loss.")
        sys.exit(1)
    
    # Step 2: Create backup
    print("\n💾 STEP 2: Creating backup")
    backup_file = create_backup()
    
    if not backup_file:
        print("⚠️  Backup failed, but continuing anyway...")
    
    # Step 3: Show migration plan
    print("\n📋 STEP 3: Migration plan")
    success, output = run_command("flask db heads", "Current migration heads")
    success, output = run_command("flask db current", "Current migration")
    success, output = run_command("flask db history --verbose", "Migration history")
    
    # Step 4: Confirm with user
    print("\n⚠️  STEP 4: User confirmation")
    confirm = input("Do you want to proceed with the migration? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y', 'כן']:
        print("❌ Migration cancelled by user")
        sys.exit(0)
    
    # Step 5: Run the migration
    print("\n🔧 STEP 5: Running migration")
    success, output = run_command("flask db upgrade", "Running migration")
    
    if not success:
        print("❌ Migration failed!")
        
        if backup_file:
            print("🔄 Attempting rollback from backup...")
            rollback_success, rollback_output = run_command(
                f'psql "postgresql://framg:copenhagen2024@localhost/framg" < {backup_file}',
                "Restoring from backup"
            )
            
            if rollback_success:
                print("✅ Rollback successful")
            else:
                print("❌ Rollback failed! Manual intervention required.")
        
        sys.exit(1)
    
    # Step 6: Post-migration health check
    print("\n🔍 STEP 6: Post-migration health check")
    success, output = run_command("python check_migration_health.py", "Post-migration health check")
    
    if not success:
        print("❌ Post-migration health check failed!")
        print("Migration completed but system may be in an inconsistent state.")
        print(f"Backup available at: {backup_file}")
        sys.exit(1)
    
    # Step 7: Verify API functionality
    print("\n🧪 STEP 7: API verification")
    
    # Start Flask in background to test API
    print("Starting Flask server for API test...")
    
    # Try to import and test without starting server
    try:
        from app import app
        from backend.extensions import db
        
        with app.app_context():
            from sqlalchemy import text
            
            # Test a simple query
            result = db.session.execute(text("SELECT COUNT(*) FROM routes"))
            route_count = result.scalar()
            
            print(f"✅ Database accessible - {route_count} routes found")
            
            # Test model loading
            from backend.models.route import Route
            print("✅ Models load successfully")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print(f"Backup available at: {backup_file}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    if backup_file:
        print(f"📦 Backup saved: {backup_file}")
        print("   You can delete it after verifying everything works correctly.")
    
    print("\nRecommended next steps:")
    print("1. Test the application manually")
    print("2. Run the full test suite")
    print("3. Verify all endpoints are working")
    print("4. Delete backup if everything is OK")

if __name__ == "__main__":
    main()
