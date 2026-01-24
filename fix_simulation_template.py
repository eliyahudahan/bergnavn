#!/usr/bin/env python3
# fix_simulation_template.py
# English comments only inside file (per your request).

import os
import re

def fix_simulation_template():
    """Fix the simulation template by removing extra endblock tag."""
    
    template_path = "backend/templates/maritime_split/realtime_simulation.html"
    
    print(f"🔧 Fixing template: {template_path}")
    
    # Read the file
    with open(template_path, 'r') as f:
        lines = f.readlines()
    
    # Find all endblock tags
    endblock_lines = []
    for i, line in enumerate(lines):
        if '{% endblock %}' in line:
            endblock_lines.append((i+1, line.strip()))  # +1 for 1-based line numbers
    
    print(f"📊 Found {len(endblock_lines)} endblock tags:")
    for line_num, content in endblock_lines:
        print(f"  Line {line_num}: {content}")
    
    # Expected structure:
    # 1. {% endblock %} for title block
    # 2. {% endblock %} for head block  
    # 3. {% endblock %} for content block
    # 4. {% endblock %} for scripts block
    # Total: 4 endblock tags
    
    if len(endblock_lines) > 4:
        print(f"\n⚠️ PROBLEM: Found {len(endblock_lines)} endblock tags, expected 4")
        print("Removing extra endblock tags...")
        
        # Keep only the first 4 endblock tags
        lines_to_keep = []
        endblock_count = 0
        
        for line in lines:
            if '{% endblock %}' in line:
                endblock_count += 1
                if endblock_count <= 4:
                    lines_to_keep.append(line)
                else:
                    print(f"  Removing extra endblock at line ~{len(lines_to_keep)+1}")
            else:
                lines_to_keep.append(line)
        
        # Create backup
        backup_path = template_path + ".backup"
        import shutil
        shutil.copy2(template_path, backup_path)
        print(f"📁 Backup created: {backup_path}")
        
        # Write fixed file
        with open(template_path, 'w') as f:
            f.writelines(lines_to_keep)
        
        print("✅ Fixed! Removed extra endblock tags")
        
    elif len(endblock_lines) < 4:
        print(f"\n⚠️ PROBLEM: Found only {len(endblock_lines)} endblock tags, expected 4")
        print("Template might be missing required endblock tags")
        
    else:
        print("\n✅ CORRECT: Found exactly 4 endblock tags as expected")
        
        # Check if they're in the right places
        print("\n📋 Block structure:")
        print("1. title block - should have {% endblock %}")
        print("2. head block - should have {% endblock %}") 
        print("3. content block - should have {% endblock %}")
        print("4. scripts block - should have {% endblock %}")
    
    # Verify the fix
    print("\n🔍 Verifying template structure...")
    
    # Check for common issues
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Count blocks
    block_count = content.count('{% block ')
    endblock_count = content.count('{% endblock %}')
    
    print(f"Blocks: {block_count}, Endblocks: {endblock_count}")
    
    if block_count == endblock_count:
        print("✅ Block/endblock count matches!")
    else:
        print(f"❌ MISMATCH: Blocks ({block_count}) != Endblocks ({endblock_count})")
    
    # Show last 10 lines to verify
    print("\n📄 Last 10 lines of fixed template:")
    last_lines = lines[-10:] if 'lines' in locals() else []
    for i, line in enumerate(last_lines, max(1, len(lines)-9)):
        print(f"{i:3}: {line.rstrip()}")
    
    print("\n🎯 To apply fix: Restart Flask server")

if __name__ == "__main__":
    fix_simulation_template()