#!/usr/bin/env python3
"""
Fix the health endpoint by adding the missing text() import
"""

import sys
import os

# מצא את קובץ system_routes.py
system_routes_file = "backend/routes/system_routes.py"

print(f"🔧 Fixing {system_routes_file}...")

# קרא את התוכן הנוכחי
with open(system_routes_file, 'r') as f:
    content = f.read()

print("📋 Current content:")
print("-" * 40)
print(content[:300] + "..." if len(content) > 300 else content)
print("-" * 40)

# בדוק אם יש כבר את ה-import
if "from sqlalchemy import text" in content:
    print("✅ text import already exists")
else:
    # הוסף את ה-import
    if "from backend import db" in content:
        # החלף את שורת ה-import
        new_content = content.replace(
            "from backend import db",
            "from backend import db\nfrom sqlalchemy import text"
        )
        
        with open(system_routes_file, 'w') as f:
            f.write(new_content)
        
        print("✅ Added 'from sqlalchemy import text' import")
    else:
        print("❌ Cannot find 'from backend import db' line")

# עכשיו תיקן את השורה עם ה-SQL
if "db.session.execute('SELECT 1')" in content:
    new_content = content.replace(
        "db.session.execute('SELECT 1')",
        "db.session.execute(text('SELECT 1'))"
    )
    
    with open(system_routes_file, 'w') as f:
        f.write(new_content)
    
    print("✅ Fixed SQL query to use text()")
else:
    print("⚠️  SQL query line not found or already fixed")

# בדוק את התיקון
print("\n📋 Updated content:")
with open(system_routes_file, 'r') as f:
    updated_content = f.read()
    
print("-" * 40)
print(updated_content[:400] + "..." if len(updated_content) > 400 else updated_content)
print("-" * 40)

print("\n✅ Health endpoint fixed!")
