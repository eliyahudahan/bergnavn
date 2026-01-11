# save as check_dashboard.py
import os
import re

def check_dashboard_html():
    html_path = "backend/templates/maritime_split/dashboard_base.html"
    
    with open(html_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("local-time element", r'id=["\']local-time["\']'),
        ("updateTime function", r'function updateTime\(\)'),
        ("setInterval for clock", r'setInterval.*updateTime.*1000\)'),
        ("DOMContentLoaded init", r'DOMContentLoaded.*updateTime'),
        ("routeData variable", r'window\.routeData'),
        ("mapReady event", r'mapReady.*addRoutesToMap'),
    ]
    
    print("🔍 Checking dashboard HTML:")
    for name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print(f"   ✅ {name}")
        else:
            print(f"   ❌ {name} - Missing!")

if __name__ == "__main__":
    check_dashboard_html()