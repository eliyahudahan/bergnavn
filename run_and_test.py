#!/usr/bin/env python3
"""
Run the app and test the health endpoint
"""
import time
import subprocess
import requests
import sys

print("🚀 Starting Flask server for testing...")
print("=" * 50)

# Start Flask in background
flask_process = subprocess.Popen(
    ['flask', 'run', '--host=0.0.0.0', '--port=5001'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

print(f"✅ Flask started with PID: {flask_process.pid}")
print("⏳ Waiting for server to start...")
time.sleep(3)  # Give server time to start

print("\n🧪 Testing endpoints...")

# Test endpoints
endpoints = [
    ("http://localhost:5001/health", "Health check"),
    ("http://localhost:5001/ping", "Ping"),
    ("http://localhost:5001/system/info", "System info"),
]

all_passed = True

for url, name in endpoints:
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"✅ {name}: HTTP 200")
            try:
                data = response.json()
                print(f"   Response: {data.get('status', 'unknown')}")
            except:
                print(f"   Response: {response.text[:50]}...")
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"❌ {name}: Failed - {str(e)[:50]}")
        all_passed = False

print("\n" + "=" * 50)

# Kill the Flask process
flask_process.terminate()
flask_process.wait()
print(f"✅ Flask server stopped")

if all_passed:
    print("\n🎉 ALL TESTS PASSED! Health endpoint is FIXED!")
else:
    print("\n⚠️  Some tests failed. Check the output above.")

print("=" * 50)
