#!/bin/bash
# Installation script for RTZ Dashboard Fix

echo "🚢 Installing RTZ Dashboard Fix"
echo "================================"

# Step 1: Copy the fixed loader
echo -e "\n1️⃣ Copying fixed RTZ loader..."
cp backend/rtz_loader_fixed.py backend/services/rtz_loader_fixed.py 2>/dev/null || true
echo "✅ RTZ loader copied"

# Step 2: Check maritime_routes.py
echo -e "\n2️⃣ Checking maritime_routes.py..."
if [ -f "backend/routes/maritime_routes.py" ]; then
    echo "✅ maritime_routes.py exists"
    
    # Check if the route already exists
    if grep -q "dashboard-fixed" backend/routes/maritime_routes.py; then
        echo "⚠️  Route already exists, skipping..."
    else
        echo "📝 Adding route to maritime_routes.py..."
        echo "" >> backend/routes/maritime_routes.py
        cat backend/dashboard_route_final.py >> backend/routes/maritime_routes.py
        echo "✅ Route added"
    fi
else
    echo "❌ maritime_routes.py not found!"
    echo "💡 Create it first or add the route manually"
fi

# Step 3: Test the loader
echo -e "\n3️⃣ Testing RTZ loader..."
python3 -c "
import sys
sys.path.append('backend')
try:
    from rtz_loader_fixed import rtz_loader
    print('✅ RTZ loader imported successfully')
    data = rtz_loader.get_dashboard_data()
    print(f'📊 Found {data["total_routes"]} routes')
    print(f'📍 Ports: {len(data["ports_list"])}')
    for port in data['ports_list']:
        print(f'  • {port}')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo -e "\n🎉 Installation complete!"
echo -e "\n🚀 To use:"
echo "1. Restart Flask server"
echo "2. Visit: http://localhost:5000/maritime/dashboard-fixed"
echo "3. Check status: http://localhost:5000/maritime/api/rtz-status"
echo -e "\n📁 Files created:"
echo "• backend/rtz_loader_fixed.py - Fixed RTZ loader"
echo "• backend/dashboard_route_final.py - Dashboard route code"
echo -e "\n💡 If dashboard doesn't work, check Flask logs for errors"
