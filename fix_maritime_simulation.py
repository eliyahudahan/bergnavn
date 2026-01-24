#!/usr/bin/env python3
"""
FIX: Maritime Dashboard Simulation Endpoint
Empirical Fix for BuildError: maritime.simulation_dashboard endpoint missing

This fix adds the missing endpoint WITHOUT rebuilding or removing anything.
Fix only what's broken - keep everything else intact.

Problem: In base.html line 54, there's a link to 'maritime.simulation_dashboard'
but no such endpoint exists in maritime_routes.py

Solution: Add the minimal endpoint to fix the link.
"""

import os
import re
from pathlib import Path
import sys

def backup_file(filepath):
    """Create backup of existing file"""
    backup_path = filepath + '.backup'
    try:
        import shutil
        shutil.copy2(filepath, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def add_simulation_endpoint():
    """
    Add simulation_dashboard endpoint to maritime_routes.py
    This is the EMPIRICAL fix - adding only what's missing
    """
    maritime_routes_path = "backend/routes/maritime_routes.py"
    
    if not os.path.exists(maritime_routes_path):
        print(f"❌ File not found: {maritime_routes_path}")
        return False
    
    # First, backup the original file
    if not backup_file(maritime_routes_path):
        return False
    
    # Read the current file
    with open(maritime_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find where to add the new endpoint (after maritime_dashboard function)
    maritime_dashboard_end = content.find('def maritime_dashboard():')
    if maritime_dashboard_end == -1:
        print("❌ Could not find maritime_dashboard function")
        return False
    
    # Find the end of the maritime_dashboard function
    # Look for the next function definition or a blank line after the function
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def maritime_dashboard():' in line:
            # Find where this function ends
            indent_level = len(line) - len(line.lstrip())
            for j in range(i + 1, len(lines)):
                # Check if this line starts a new function (same indent level)
                if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) == indent_level:
                    if lines[j].lstrip().startswith('def '):
                        # Found the next function
                        insert_line = j
                        break
            else:
                # If no next function found, insert at end of file
                insert_line = len(lines)
            
            # Create the new endpoint code
            simulation_endpoint = '''
@maritime_bp.route('/simulation-dashboard/<lang>')
def simulation_dashboard(lang):
    """
    Simulation Dashboard - shows maritime simulations and scenarios.
    This endpoint was added to fix the broken link in base.html.
    For now, it redirects to the main dashboard.
    """
    # Ensure valid language
    if lang not in ['en', 'no']:
        lang = 'en'
    
    # TEMPORARY: Redirect to main dashboard
    # In the future, this can be a dedicated simulation dashboard
    from flask import redirect, url_for
    return redirect(url_for('maritime.maritime_dashboard', lang=lang))
'''
            
            # Insert the new endpoint
            lines.insert(insert_line, simulation_endpoint)
            new_content = '\n'.join(lines)
            
            # Write the fixed file
            with open(maritime_routes_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Added simulation_dashboard endpoint to maritime_routes.py")
            print("   - Path: /maritime/simulation-dashboard/<lang>")
            print("   - Temporary redirect to main dashboard")
            return True
    
    return False

def verify_simulation_endpoint():
    """Verify the simulation endpoint was added correctly"""
    maritime_routes_path = "backend/routes/maritime_routes.py"
    
    with open(maritime_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if endpoint exists
    if 'def simulation_dashboard(' in content:
        print("✅ Verification: simulation_dashboard endpoint exists")
        
        # Check route decorator
        if "@maritime_bp.route('/simulation-dashboard/<lang>')" in content:
            print("✅ Verification: Route decorator is correct")
            return True
        else:
            print("⚠️  Warning: Route decorator might be incorrect")
            return False
    else:
        print("❌ Verification failed: Endpoint not found")
        return False

def check_broken_link():
    """Check base.html for the broken link"""
    base_html_path = "backend/templates/base.html"
    
    if not os.path.exists(base_html_path):
        print(f"❌ File not found: {base_html_path}")
        return
    
    with open(base_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "maritime.simulation_dashboard" in line:
            print(f"📍 Found broken link at line {i+1}:")
            print(f"   {line.strip()}")
            return True
    
    print("ℹ️  No broken link found in base.html (maybe already fixed?)")
    return False

def main():
    """Main fix function"""
    print("=" * 60)
    print("FIX: Maritime Dashboard Simulation Endpoint")
    print("=" * 60)
    print()
    print("Problem: BuildError for 'maritime.simulation_dashboard'")
    print("Solution: Add missing endpoint with minimal changes")
    print()
    
    # Check current state
    print("🔍 Checking current state...")
    check_broken_link()
    
    # Apply the fix
    print()
    print("🛠️  Applying fix...")
    if add_simulation_endpoint():
        print()
        print("✅ Fix applied successfully!")
    else:
        print("❌ Fix failed")
        return 1
    
    # Verify the fix
    print()
    print("🔍 Verifying fix...")
    if verify_simulation_endpoint():
        print()
        print("🎉 Fix verification successful!")
        print()
        print("Next steps:")
        print("1. Restart your Flask application")
        print("2. Navigate to: /maritime/simulation-dashboard/en")
        print("3. The link in the navbar should now work")
    else:
        print("⚠️  Fix verification failed - manual check required")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Fix interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)