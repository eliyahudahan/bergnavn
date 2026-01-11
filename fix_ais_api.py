#!/usr/bin/env python3
"""
Fix Kystdatahuset API 406 error by updating User-Agent
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def update_ais_config():
    """Update AIS service configuration"""
    # Check .env file
    env_path = os.path.join(project_root, '.env')
    
    if not os.path.exists(env_path):
        print("❌ .env file not found")
        return
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    updated = False
    new_lines = []
    
    for line in lines:
        if 'KYSTDATAHUSET_USER_AGENT' in line:
            # Update to a more standard User-Agent
            new_line = 'KYSTDATAHUSET_USER_AGENT="Mozilla/5.0 (compatible; BergNavnMaritime/3.0; +mailto:framgangsrik747@gmail.com)"\n'
            new_lines.append(new_line)
            updated = True
            print(f"🔧 Updated: {line.strip()}")
            print(f"       To: {new_line.strip()}")
        else:
            new_lines.append(line)
    
    if updated:
        # Backup
        backup = env_path + '.backup'
        with open(backup, 'w') as f:
            f.writelines(lines)
        
        # Write updated
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        print(f"\n✅ Updated .env file")
        print(f"   Backup: {backup}")
        
        print("\n💡 Also check kystdatahuset_adapter.py for User-Agent header")
    else:
        print("✅ KYSTDATAHUSET_USER_AGENT already has proper format")

if __name__ == "__main__":
    print("🔧 Fixing AIS API 406 error...")
    update_ais_config()