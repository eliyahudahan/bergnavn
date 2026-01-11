#!/usr/bin/env python3
"""
Fix KystdatahusetAdapter missing get_latest_positions method
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def fix_ais_adapter():
    """Add missing method to KystdatahusetAdapter"""
    filepath = os.path.join(project_root, "backend", "services", "kystdatahuset_adapter.py")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if method exists
    if 'def get_latest_positions(self' in content:
        print("✅ get_latest_positions already exists")
        return
    
    print("🔧 Adding get_latest_positions method...")
    
    # Find where to add the method (after get_real_time_vessels)
    if 'def get_real_time_vessels(self' in content:
        # Find the end of that method
        start = content.find('def get_real_time_vessels(self')
        end = content.find('\n\n', start)
        if end == -1:
            end = len(content)
        
        # Add the new method
        new_method = '''

    def get_latest_positions(self):
        """
        Get latest vessel positions.
        Alias for get_real_time_vessels for compatibility.
        """
        return self.get_real_time_vessels()
'''
        
        new_content = content[:end] + new_method + content[end:]
        
        # Backup and write
        backup = filepath + '.backup'
        with open(backup, 'w') as f:
            f.write(content)
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Added get_latest_positions method")
        print(f"   Backup: {backup}")
    else:
        print("❌ Could not find get_real_time_vessels method")

if __name__ == "__main__":
    print("🔧 Fixing AIS Adapter missing method...")
    fix_ais_adapter()