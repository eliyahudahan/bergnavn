#!/usr/bin/env python3
"""
Migration Health Check Script
Runs before and after migrations to ensure consistency
"""

import sys
import os
from sqlalchemy import text

def check_migration_health():
    """
    Comprehensive migration health check
    Returns: (is_healthy: bool, message: str)
    """
    
    try:
        # Import within function to avoid circular imports
        from app import app
        from backend.extensions import db
        
        with app.app_context():
            health_checks = []
            
            # 1. Check alembic version table exists
            try:
                result = db.session.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version')"))
                alembic_table_exists = result.scalar()
                health_checks.append(('alembic_version table exists', alembic_table_exists))
            except:
                health_checks.append(('alembic_version table exists', False))
            
            if not alembic_table_exists:
                return False, "❌ alembic_version table not found"
            
            # 2. Get current alembic version
            try:
                result = db.session.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.scalar()
                health_checks.append(('alembic version readable', True))
            except Exception as e:
                return False, f"❌ Failed to read alembic version: {str(e)}"
            
            # 3. Verify critical tables exist
            critical_tables = ['routes', 'route_legs', 'waypoints']
            for table in critical_tables:
                try:
                    result = db.session.execute(text(f"""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table}'
                        )
                    """))
                    exists = result.scalar()
                    health_checks.append((f'table {table} exists', exists))
                    
                    if not exists:
                        return False, f"❌ Critical table '{table}' not found"
                    
                except Exception as e:
                    return False, f"❌ Failed to check table '{table}': {str(e)}"
            
            # 4. Verify current migration was properly applied
            migration_specific_checks = {
                'rtz_final_fix': [
                    ("routes", "source"),
                    ("routes", "rtz_filename"),
                    ("routes", "created_at"),
                    ("routes", "updated_at")
                ],
                '6ee84f482a42': [
                    ("routes", "origin"),
                    ("routes", "destination")
                ]
            }
            
            if current_version in migration_specific_checks:
                missing_columns = []
                for table, column in migration_specific_checks[current_version]:
                    try:
                        result = db.session.execute(text(f"""
                            SELECT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_schema = 'public' 
                                AND table_name = '{table}' 
                                AND column_name = '{column}'
                            )
                        """))
                        exists = result.scalar()
                        
                        if not exists:
                            missing_columns.append(f"{table}.{column}")
                            
                    except Exception as e:
                        return False, f"❌ Failed to check column {table}.{column}: {str(e)}"
                
                if missing_columns:
                    return False, f"❌ Migration {current_version} incomplete. Missing columns: {', '.join(missing_columns)}"
                
                health_checks.append((f'migration {current_version} complete', True))
            
            # 5. Check data consistency
            try:
                # Check routes table has data if expected
                result = db.session.execute(text("SELECT COUNT(*) FROM routes"))
                route_count = result.scalar()
                health_checks.append(('routes table has data', route_count > 0))
            except:
                health_checks.append(('routes table has data', False))
            
            # Prepare report
            passed = sum(1 for check, passed in health_checks if passed)
            total = len(health_checks)
            
            report = [
                "\n" + "="*60,
                "MIGRATION HEALTH CHECK REPORT",
                "="*60,
                f"Alembic version: {current_version}",
                f"Checks passed: {passed}/{total}",
                "-"*60
            ]
            
            for check_name, check_passed in health_checks:
                status = "✅ PASS" if check_passed else "❌ FAIL"
                report.append(f"{status}: {check_name}")
            
            report.append("="*60)
            
            if passed == total:
                report.append("✅ ALL CHECKS PASSED - System is healthy")
                return True, "\n".join(report)
            else:
                report.append("⚠️  SOME CHECKS FAILED - Review the issues above")
                return False, "\n".join(report)
                
    except Exception as e:
        return False, f"❌ CRITICAL ERROR: {str(e)}"

def main():
    """Main entry point"""
    print("🔍 Running Migration Health Check...")
    
    is_healthy, message = check_migration_health()
    
    print(message)
    
    # Return appropriate exit code
    sys.exit(0 if is_healthy else 1)

if __name__ == "__main__":
    main()
