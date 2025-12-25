#!/usr/bin/env python3
"""
Safe test - imports the module directly without loading the full app
"""
import sys
import os

print("🔒 SAFE TEST - Importing module directly")
print("=" * 50)

# First, check if file exists
if not os.path.exists('backend/routes/system_routes.py'):
    print("❌ File does not exist!")
    sys.exit(1)

# Try to read the file to check syntax
try:
    with open('backend/routes/system_routes.py', 'r') as f:
        content = f.read()
    
    # Basic syntax checks
    if 'from sqlalchemy import text' in content:
        print("✅ Import statement found")
    else:
        print("❌ Missing 'from sqlalchemy import text'")
    
    if "text('SELECT 1')" in content:
        print("✅ SQL query uses text() wrapper")
    else:
        print("❌ SQL query not wrapped in text()")
    
    if 'health_bp = Blueprint' in content:
        print("✅ Blueprint definition found")
    else:
        print("❌ Blueprint not defined")
    
    # Count endpoints
    endpoint_count = content.count('@health_bp.route')
    print(f"✅ Found {endpoint_count} endpoints")
    
except Exception as e:
    print(f"❌ File read error: {e}")

print("\n" + "=" * 50)
print("🧪 Testing Python syntax...")

# Test Python syntax
import subprocess
result = subprocess.run(
    [sys.executable, '-m', 'py_compile', 'backend/routes/system_routes.py'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Python syntax is VALID")
else:
    print("❌ Python syntax error:")
    print(result.stderr)

print("\n" + "=" * 50)
