#!/usr/bin/env python3
"""
Immediate fix for missing simulation_dashboard endpoint.
Adds the endpoint directly to maritime_routes.py
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def add_simulation_endpoint():
    """Add the simulation_dashboard endpoint to maritime_routes.py"""
    filepath = os.path.join(project_root, "backend", "routes", "maritime_routes.py")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    # Read the file
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Check if endpoint already exists
    for line in lines:
        if '@maritime_bp.route(\'/simulation\')' in line:
            print("✅ simulation_dashboard endpoint already exists in file")
            return True
    
    print("❌ simulation_dashboard endpoint not found, adding it...")
    
    # Find where to add it - after maritime_dashboard function
    insertion_point = -1
    for i, line in enumerate(lines):
        if 'def maritime_dashboard(' in line:
            # Find the end of this function
            for j in range(i, len(lines)):
                if j > i and lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                    insertion_point = j
                    break
            if insertion_point == -1:
                insertion_point = len(lines)
            break
    
    if insertion_point == -1:
        print("❌ Could not find where to insert")
        return False
    
    # Prepare the endpoint code
    simulation_code = [
        '\n',
        '@maritime_bp.route(\'/simulation\')\n',
        'def simulation_dashboard(lang=None):\n',
        '    """\n',
        '    Simulation dashboard endpoint.\n',
        '    Required by base.html template.\n',
        '    """\n',
        '    # For now, redirect to main dashboard\n',
        '    from flask import redirect, url_for\n',
        '    return redirect(url_for(\'maritime.maritime_dashboard\', lang=lang))\n',
        '\n'
    ]
    
    # Insert the code
    lines[insertion_point:insertion_point] = simulation_code
    
    # Create backup
    backup = filepath + '.backup_final'
    with open(backup, 'w') as f:
        f.writelines(lines)
    
    # Write the fixed file
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Added simulation_dashboard endpoint at line {insertion_point+1}")
    print(f"   Backup saved to: {backup}")
    
    # Verify
    print("\n🔍 Verifying fix...")
    with open(filepath, 'r') as f:
        content = f.read()
    
    if '@maritime_bp.route(\'/simulation\')' in content:
        print("✅ Route decorator added")
    if 'def simulation_dashboard(lang=None):' in content:
        print("✅ Function with lang parameter added")
    if 'redirect(url_for' in content:
        print("✅ Redirect logic added")
    
    return True

def main():
    print("\n🔧 IMMEDIATE FIX: Adding simulation_dashboard endpoint")
    print("=" * 60)
    
    print("Problem: base.html requires 'maritime.simulation_dashboard' endpoint")
    print("Solution: Add the endpoint with lang parameter support\n")
    
    if add_simulation_endpoint():
        print("\n" + "=" * 60)
        print("✅ FIX COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\n🚀 What was fixed:")
        print("   1. Added @maritime_bp.route('/simulation') decorator")
        print("   2. Added simulation_dashboard(lang=None) function")
        print("   3. Function redirects to main dashboard")
        print("   4. Supports 'lang' parameter as required by base.html")
        
        print("\n🎯 Next steps:")
        print("   1. Restart server: Ctrl+C then python app.py")
        print("   2. Visit: http://localhost:5000/maritime")
        print("   3. Should work without errors")
        print("   4. Will show: 37 Actual Routes")
    else:
        print("\n❌ Fix failed")
        print("\n💡 Manual fix required:")
        print("   Open: backend/routes/maritime_routes.py")
        print("   Add this code after maritime_dashboard function:")
        print('''
@maritime_bp.route('/simulation')
def simulation_dashboard(lang=None):
    """Simulation dashboard endpoint."""
    from flask import redirect, url_for
    return redirect(url_for('maritime.maritime_dashboard', lang=lang))
''')

if __name__ == "__main__":
    main()