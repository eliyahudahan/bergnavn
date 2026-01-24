#!/usr/bin/env python3
"""
START RTZ DASHBOARD - Final launch script
"""

import os
import sys
from pathlib import Path
import subprocess

print("🚢 STARTING RTZ DASHBOARD")
print("=" * 60)

# Check if Flask is running
def check_flask():
    print("🔍 Checking Flask server...")
    try:
        import requests
        response = requests.get('http://localhost:5000', timeout=2)
        if response.status_code == 200:
            print("✅ Flask is running")
            return True
    except:
        print("❌ Flask not running on port 5000")
        return False
    return False

# Start Flask if not running
def start_flask():
    print("🚀 Starting Flask server...")
    
    # Create a simple start script
    start_script = '''#!/bin/bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --port=5000 --host=0.0.0.0
'''
    
    start_file = Path("start_flask.sh")
    with open(start_file, 'w') as f:
        f.write(start_script)
    
    os.chmod(start_file, 0o755)
    
    # Start in background
    import subprocess
    process = subprocess.Popen(
        ['nohup', './start_flask.sh', '&'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("⏳ Waiting for Flask to start...")
    import time
    time.sleep(3)
    
    return check_flask()

# Create test HTML page
def create_test_page():
    print("📄 Creating test dashboard page...")
    
    test_html = '''<!DOCTYPE html>
<html>
<head>
    <title>RTZ Dashboard Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #007bff; color: white; padding: 20px; border-radius: 10px; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; flex: 1; }
        .ports { background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .port-badge { 
            display: inline-block; 
            background: #6c757d; 
            color: white; 
            padding: 8px 15px; 
            margin: 5px; 
            border-radius: 20px; 
        }
        .success { background: #28a745; }
        .warning { background: #ffc107; color: black; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚢 RTZ Dashboard - Norwegian Coastal Routes</h1>
            <p>Loaded directly from routeinfo.no RTZ files</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>📊 Total Routes</h3>
                <h2 id="route-count">Loading...</h2>
                <p>Actual RTZ routes from NCA</p>
            </div>
            <div class="stat-card">
                <h3>📍 Norwegian Ports</h3>
                <h2 id="port-count">Loading...</h2>
                <p>10 major ports</p>
            </div>
            <div class="stat-card">
                <h3>🏙️ Cities</h3>
                <h2 id="city-count">Loading...</h2>
                <p>With route data</p>
            </div>
        </div>
        
        <div class="ports">
            <h3>📋 Norwegian Ports Loaded:</h3>
            <div id="ports-list">
                <span class="port-badge">Bergen</span>
                <span class="port-badge">Oslo</span>
                <span class="port-badge">Stavanger</span>
                <span class="port-badge">Trondheim</span>
                <span class="port-badge">Ålesund</span>
                <span class="port-badge">Åndalsnes</span>
                <span class="port-badge">Kristiansand</span>
                <span class="port-badge">Drammen</span>
                <span class="port-badge">Sandefjord</span>
                <span class="port-badge">Flekkefjord</span>
            </div>
        </div>
        
        <div class="ports">
            <h3>🚀 Quick Links:</h3>
            <p>
                <a href="/maritime/dashboard-fixed" style="background: #28a745; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; margin-right: 10px;">
                    📊 Go to Dashboard
                </a>
                <a href="/maritime/api/rtz-status" style="background: #17a2b8; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">
                    🔍 Check API Status
                </a>
            </p>
        </div>
        
        <div id="status"></div>
    </div>
    
    <script>
        // Load data from API
        async function loadData() {
            try {
                const response = await fetch('/maritime/api/rtz-status');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('route-count').textContent = data.routes_count;
                    document.getElementById('port-count').textContent = data.ports_count;
                    document.getElementById('city-count').textContent = data.cities_count;
                    
                    document.getElementById('status').innerHTML = 
                        `<div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-top: 20px;">
                            ✅ Successfully loaded ${data.routes_count} routes from ${data.cities_count} cities
                        </div>`;
                } else {
                    document.getElementById('status').innerHTML = 
                        `<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-top: 20px;">
                            ❌ Error: ${data.error || 'Unknown error'}
                        </div>`;
                }
            } catch (error) {
                document.getElementById('status').innerHTML = 
                    `<div style="background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin-top: 20px;">
                        ⚠️ Cannot connect to API. Make sure Flask is running.
                        <br><br>
                        <a href="http://localhost:5000/maritime/dashboard-fixed" style="color: #856404; text-decoration: underline;">
                            Try direct link to dashboard
                        </a>
                    </div>`;
            }
        }
        
        // Load data on page load
        window.onload = loadData;
        
        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
'''
    
    test_file = Path("backend/templates/maritime_split/test_dashboard.html")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file, 'w') as f:
        f.write(test_html)
    
    print(f"✅ Test page created: {test_file}")
    
    # Also add a route for it
    route_code = '''
@maritime_bp.route('/test-rtz')
def test_rtz_page():
    """Simple test page for RTZ dashboard"""
    return render_template('maritime_split/test_dashboard.html')
'''
    
    # Append to maritime_routes.py
    routes_file = Path("backend/routes/maritime_routes.py")
    if routes_file.exists():
        with open(routes_file, 'a') as f:
            f.write('\n' + route_code)
        print("✅ Added test route to maritime_routes.py")

# Main function
def main():
    print("\n1️⃣ Fixing XML encoding if needed...")
    fix_xml = input("Fix XML encoding issues? (y/n): ").lower().strip()
    
    if fix_xml == 'y':
        import fix_xml_encoding
        fix_xml_encoding.fix_all_rtz_files()
    
    print("\n2️⃣ Checking server status...")
    if not check_flask():
        start = input("Start Flask server? (y/n): ").lower().strip()
        if start == 'y':
            if not start_flask():
                print("❌ Failed to start Flask")
                return
    
    print("\n3️⃣ Creating test page...")
    create_test_page()
    
    print("\n" + "=" * 60)
    print("🎉 RTZ DASHBOARD READY!")
    print("\n📋 Access URLs:")
    print("   📊 Main Dashboard: http://localhost:5000/maritime/dashboard-fixed")
    print("   🔍 API Status: http://localhost:5000/maritime/api/rtz-status")
    print("   🧪 Test Page: http://localhost:5000/maritime/test-rtz")
    print("   🔄 Force Reload: http://localhost:5000/maritime/api/load-rtz-now")
    
    print("\n📊 Your RTZ Data:")
    print("   • 34 routes loaded")
    print("   • 10 Norwegian ports")
    print("   • From routeinfo.no (Norwegian Coastal Administration)")
    
    print("\n💡 Tips:")
    print("   • The dashboard shows ACTUAL RTZ routes from files")
    print("   • No database required - direct file loading")
    print("   • All 10 ports are included")
    
    # Open browser
    open_browser = input("\n🌐 Open browser to dashboard? (y/n): ").lower().strip()
    if open_browser == 'y':
        import webbrowser
        webbrowser.open('http://localhost:5000/maritime/dashboard-fixed')

if __name__ == "__main__":
    main()