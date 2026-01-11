#!/usr/bin/env python3
"""
Complete fix for AIS Adapter - add all missing methods
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def fix_ais_adapter():
    """Add missing methods to KystdatahusetAdapter"""
    filepath = os.path.join(project_root, "backend", "services", "kystdatahuset_adapter.py")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Methods that maritime_routes.py expects
    required_methods = [
        ('get_latest_positions', 'get_vessels_in_bergen_region'),
        ('get_real_time_vessels', 'get_vessels_in_bergen_region')
    ]
    
    added = []
    
    for required_method, fallback_method in required_methods:
        if f'def {required_method}(' not in content:
            print(f"🔧 Adding {required_method}()...")
            
            # Find a good place to add (before get_service_status)
            if 'def get_service_status(self' in content:
                pos = content.find('def get_service_status(self')
                
                # Add the method
                new_method = f'''
    def {required_method}(self, force_refresh: bool = False):
        """
        Get latest vessel positions.
        Alias for {fallback_method}() for compatibility.
        
        Args:
            force_refresh: Ignored, kept for API compatibility
            
        Returns:
            List of vessel dictionaries
        """
        return self.{fallback_method}()
'''
                
                content = content[:pos] + new_method + content[pos:]
                added.append(required_method)
    
    if added:
        # Backup
        backup = filepath + '.complete_backup'
        with open(backup, 'w') as f:
            f.write(content)
        
        # Write fixed
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"✅ Added methods: {', '.join(added)}")
        print(f"   Backup: {backup}")
    else:
        print("✅ All required methods already exist")

def fix_maritime_routes_ais_calls():
    """Fix AIS calls in maritime_routes.py to match actual methods"""
    filepath = os.path.join(project_root, "backend", "routes", "maritime_routes.py")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace get_latest_positions with get_vessels_in_bergen_region
    if 'get_latest_positions()' in content:
        print("🔧 Fixing AIS calls in maritime_routes.py...")
        
        # Replace all occurrences
        content = content.replace(
            'get_latest_positions()',
            'get_vessels_in_bergen_region()'
        )
        
        content = content.replace(
            'get_latest_positions',
            'get_vessels_in_bergen_region'
        )
        
        # Also fix get_real_time_vessels
        content = content.replace(
            'get_real_time_vessels()',
            'get_vessels_in_bergen_region()'
        )
        
        content = content.replace(
            'get_real_time_vessels(force_refresh=True)',
            'get_vessels_in_bergen_region()'
        )
        
        # Backup and write
        backup = filepath + '.ais_fix_backup'
        with open(backup, 'w') as f:
            f.write(content)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed AIS method calls")
        print(f"   Backup: {backup}")

if __name__ == "__main__":
    print("🔧 Complete AIS fix...")
    print("=" * 60)
    
    fix_ais_adapter()
    print()
    fix_maritime_routes_ais_calls()
    
    print("\n✅ AIS fix complete!")
    print("\n🚀 Now restart: python app.py")