#!/usr/bin/env python3
"""
Jinja2/HTML Syntax Error Detector for Flask Templates
Run from root directory: python3 check_template_errors.py
Output: template_errors_report.txt
"""

import re
import sys
from pathlib import Path
from datetime import datetime

def check_jinja2_template(filepath):
    """Check Jinja2 template for common syntax errors"""
    errors = []
    warnings = []
    
    try:
        content = Path(filepath).read_text(encoding='utf-8')
        lines = content.split('\n')
    except Exception as e:
        return [f"❌ Cannot read file: {e}"], []

    # 1. Check for default() with numeric values (should be strings)
    default_num_pattern = r'\|default\((\d+)\)'
    for i, line in enumerate(lines, 1):
        matches = re.finditer(default_num_pattern, line)
        for match in matches:
            errors.append({
                'line': i,
                'type': 'DEFAULT_NUMERIC',
                'msg': f"Use default('{match.group(1)}') instead of default({match.group(1)})",
                'context': line.strip()
            })

    # 2. Check for missing |int before comparisons
    int_compare_pattern = r'(\w+)\|default\([^)]+\)\s*(>=|<=|==|>|<)\s*\d+'
    for i, line in enumerate(lines, 1):
        matches = re.finditer(int_compare_pattern, line)
        for match in matches:
            errors.append({
                'line': i,
                'type': 'MISSING_INT_FILTER',
                'msg': f"Add |int after default: {match.group(1)}|default('...')|int",
                'context': line.strip()
            })

    # 3. Check for duplicate attributes in same tag
    duplicate_attr_pattern = r'<[^>]+\s+(\w+)=[^>]*\s+\1=[^>]*>'
    for i, line in enumerate(lines, 1):
        matches = re.finditer(duplicate_attr_pattern, line, re.IGNORECASE)
        for match in matches:
            errors.append({
                'line': i,
                'type': 'DUPLICATE_ATTRIBUTE',
                'msg': f"Duplicate attribute: '{match.group(1)}'",
                'context': line.strip()
            })

    # 4. Check for unclosed HTML tags
    unclosed_tags = []
    tag_stack = []
    
    for i, line in enumerate(lines, 1):
        if 'id="system-time"' in line and '</span>' not in line:
            errors.append({
                'line': i,
                'type': 'UNCLOSED_SPAN',
                'msg': 'Missing </span> closing tag for system-time',
                'context': line.strip()
            })

    # 5. Check for route-id vs route-index
    for i, line in enumerate(lines, 1):
        if 'data-route-id=' in line and 'view-route-btn' in line:
            errors.append({
                'line': i,
                'type': 'ROUTE_ID_ISSUE',
                'msg': 'Use data-route-index instead of data-route-id',
                'context': line.strip()
            })

    return errors, warnings

def main():
    """Main function to run the checker and save report"""
    template_path = Path('backend/templates/maritime_split/dashboard_base.html')
    output_path = Path('template_errors_report.txt')
    
    print("🔍 Maritime Dashboard Template Error Detector")
    print("="*60)
    print(f"📁 Scanning: {template_path}")
    print(f"📂 Current directory: {Path.cwd()}")
    
    if not template_path.exists():
        print(f"❌ ERROR: File not found at {template_path}")
        print("\n📂 Searching for dashboard_base.html...")
        
        # Search for the file
        for p in Path('.').rglob('dashboard_base.html'):
            print(f"   ✅ Found: {p}")
        
        return
    
    errors, warnings = check_jinja2_template(template_path)
    
    # Generate report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("MARITIME DASHBOARD TEMPLATE - ERROR DETECTION REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"File: {template_path}\n")
        f.write("="*80 + "\n\n")
        
        # CRITICAL ERRORS
        f.write("🔴 CRITICAL ERRORS (MUST FIX)\n")
        f.write("-"*80 + "\n")
        if errors:
            for error in sorted(errors, key=lambda x: x['line']):
                f.write(f"\nLine {error['line']}: {error['type']}\n")
                f.write(f"  ➤ {error['msg']}\n")
                f.write(f"  📝 Context: {error['context']}\n")
        else:
            f.write("\n✅ No critical errors found!\n")
        
        # WARNINGS
        f.write("\n\n🟡 WARNINGS (Recommended fixes)\n")
        f.write("-"*80 + "\n")
        if warnings:
            for warning in sorted(warnings, key=lambda x: x['line']):
                f.write(f"\nLine {warning['line']}: {warning['type']}\n")
                f.write(f"  ➤ {warning['msg']}\n")
                f.write(f"  📝 Context: {warning['context']}\n")
        else:
            f.write("\n✅ No warnings found!\n")
        
        # SUMMARY
        f.write("\n\n📊 SUMMARY\n")
        f.write("-"*80 + "\n")
        f.write(f"Critical errors: {len(errors)}\n")
        f.write(f"Warnings: {len(warnings)}\n")
    
    # Print summary to console
    print("\n" + "="*60)
    print(f"✅ Report saved to: {output_path}")
    print(f"📊 Found {len(errors)} critical errors, {len(warnings)} warnings")
    
    if errors:
        print("\n🔴 CRITICAL ERRORS:")
        for error in errors[:5]:
            print(f"   Line {error['line']}: {error['msg']}")
        if len(errors) > 5:
            print(f"   ... and {len(errors)-5} more errors")
    
    print("\n📄 Full report: cat template_errors_report.txt")
    print("="*60)

if __name__ == "__main__":
    main()
