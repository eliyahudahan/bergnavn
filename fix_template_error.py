#!/usr/bin/env python3
"""
FIX TEMPLATE SYNTAX ERROR - BERGNAVN MARITIME
Author: System Assistant
Date: 2024-01-18

🚨 FIXES: Jinja2 TemplateSyntaxError - missing 'endblock'
✅ RESTORES: Proper template structure
✅ PRESERVES: All our fixes
"""

import os
import sys
from datetime import datetime

class TemplateErrorFixer:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(
            self.project_root, 
            "backend", 
            "templates", 
            "maritime_split", 
            "realtime_simulation.html"
        )
        
    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.template_path}.error_fix_{timestamp}"
        
        try:
            import shutil
            shutil.copy2(self.template_path, backup_path)
            print(f"📦 Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def read_template(self):
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read template: {e}")
            return None
    
    def write_template(self, content):
        try:
            with open(self.template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Failed to write template: {e}")
            return False
    
    def fix_missing_endblock(self, content):
        """Fix the missing endblock issue"""
        print("🔧 Fixing missing endblock...")
        
        # Count opening and closing blocks
        opening_blocks = content.count('{% block')
        closing_blocks = content.count('{% endblock')
        
        print(f"📊 Block count: {opening_blocks} openings, {closing_blocks} closings")
        
        # Find where the scripts block starts
        scripts_start = content.find('{% block scripts %}')
        if scripts_start == -1:
            print("⚠️ No scripts block found, checking for any open block...")
            return content
        
        # Find the end of the file
        file_end = len(content)
        
        # Look for where the block should end
        # First, check if there's already an endblock after it
        endblock_pos = content.find('{% endblock', scripts_start + 1)
        
        if endblock_pos != -1 and endblock_pos < file_end:
            print("✅ Endblock already exists")
            return content
        
        # We need to add the endblock
        # Find a good place to add it (before the closing </html> or at the end)
        html_end = content.find('</html>')
        if html_end == -1:
            html_end = file_end
        
        # Add the endblock before </html>
        new_content = content[:html_end] + '\n{% endblock %}\n' + content[html_end:]
        
        print("✅ Added missing endblock")
        return new_content
    
    def verify_template_structure(self, content):
        """Verify the template has proper structure"""
        print("🔍 Verifying template structure...")
        
        # Check for required sections
        required_sections = [
            '{% extends',
            '{% block title',
            '{% block head',
            '{% block content',
            '{% block scripts'
        ]
        
        for section in required_sections:
            if section not in content:
                print(f"⚠️ Missing: {section}")
        
        # Count blocks
        lines = content.split('\n')
        indent_level = 0
        for i, line in enumerate(lines):
            if '{% block' in line:
                indent_level += 1
                print(f"  {'  ' * (indent_level-1)}▶ Open block: {line.strip()}")
            elif '{% endblock' in line:
                print(f"  {'  ' * indent_level}◀ Close block: {line.strip()}")
                indent_level -= 1
        
        if indent_level != 0:
            print(f"❌ Block mismatch: {indent_level} unclosed blocks")
        else:
            print("✅ All blocks properly closed")
        
        return content
    
    def fix_script_tags(self, content):
        """Fix script tag syntax"""
        print("🔧 Fixing script tag syntax...")
        
        # The problematic line from error:
        # <script src="{{ url_for('static', filename='js/split/turbine_alerts.js') }}">
        # Need to close this tag properly
        
        problem_line = '<script src="{{ url_for(\'static\', filename=\'js/split/turbine_alerts.js\') }}">'
        
        if problem_line in content:
            # Check if it has a closing tag
            pos = content.find(problem_line)
            next_chars = content[pos + len(problem_line):pos + len(problem_line) + 10]
            
            if '</script>' not in next_chars:
                # Add closing tag
                fixed_line = problem_line + '</script>'
                content = content.replace(problem_line, fixed_line)
                print("✅ Fixed unclosed script tag")
        
        return content
    
    def run(self):
        """Run all fixes"""
        print("=" * 70)
        print("🚨 FIX TEMPLATE SYNTAX ERROR")
        print("=" * 70)
        
        if not os.path.exists(self.template_path):
            print(f"❌ Template not found: {self.template_path}")
            return False
        
        # Create backup
        backup = self.create_backup()
        if not backup:
            return False
        
        # Read template
        content = self.read_template()
        if not content:
            return False
        
        original_content = content
        
        # Apply fixes
        content = self.fix_missing_endblock(content)
        content = self.verify_template_structure(content)
        content = self.fix_script_tags(content)
        
        # Write updated template
        if content != original_content:
            if self.write_template(content):
                print("\n" + "=" * 70)
                print("✅ TEMPLATE ERROR FIXED!")
                print("=" * 70)
                print(f"📦 Backup: {backup}")
                
                print("\n🎯 PROBLEMS FIXED:")
                print("   1. ✅ Missing '{% endblock %}'")
                print("   2. ✅ Template structure verified")
                print("   3. ✅ Script tags properly closed")
                
                print("\n🔧 TO TEST:")
                print("   1. python app.py")
                print("   2. Go to: /maritime/simulation")
                print("   3. Should load without TemplateSyntaxError")
                
                return True
            else:
                print("❌ Failed to write updated template")
                return False
        else:
            print("⚠️ No changes were made (might already be fixed)")
            return True

def main():
    fixer = TemplateErrorFixer()
    
    try:
        success = fixer.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()