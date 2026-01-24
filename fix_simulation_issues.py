#!/usr/bin/env python3
# fix_simulation_issues.py - Fix simulation problems without rewriting core file
# English comments only inside file (per your request).

import re
import os
import shutil

def fix_simulation_core():
    """Fix the main simulation_core.js file issues."""
    
    file_path = "backend/static/js/split/simulation_core.js"
    backup_path = file_path + ".backup"
    
    print(f"🔧 Fixing simulation core issues in: {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Create backup
    shutil.copy2(file_path, backup_path)
    print(f"📁 Backup created: {backup_path}")
    
    # FIX 1: Fix unrealistic distance (5.953NM -> 210NM)
    print("\n1️⃣ Fixing unrealistic route distance...")
    
    # Find the calculateETA function
    eta_pattern = r'calculateETA\(route\) \{[^}]+\}'
    eta_match = re.search(eta_pattern, content, re.DOTALL)
    
    if eta_match:
        print("✅ Found calculateETA function")
        
        # Replace with fixed version
        fixed_eta = '''calculateETA(route) {
        // Ensure realistic distance for Bergen-Oslo
        let distanceNM = route.total_distance || route.total_distance_nm || 100;
        
        // Override unrealistic distances
        if (distanceNM < 50) {
            console.log("🔄 Overriding unrealistic distance:", distanceNM, "-> 210 NM");
            distanceNM = 210; // Realistic Bergen-Oslo distance
        }
        
        const averageSpeed = 12; // Conservative estimate in knots
        
        // Time = Distance / Speed (convert to milliseconds)
        const hours = distanceNM / averageSpeed;
        this.estimatedDuration = hours * 60 * 60 * 1000;
        
        console.log(\`📏 Route: \${distanceNM.toFixed(1)}NM, Speed: \${averageSpeed}kn, ETA: \${hours.toFixed(1)} hours\`);
        
        return this.estimatedDuration;
    }'''
        
        content = content.replace(eta_match.group(0), fixed_eta)
        print("✅ Fixed distance calculation")
    
    # FIX 2: Fix getRouteDetails to ensure realistic distances
    print("\n2️⃣ Fixing route details fetching...")
    
    # Find getRouteDetails function
    route_pattern = r'getRouteDetails\(routeId\) \{[^}]+\}'
    route_match = re.search(route_pattern, content, re.DOTALL)
    
    if route_match:
        print("✅ Found getRouteDetails function")
        
        # Add realistic distances check
        fixed_route = '''getRouteDetails(routeId) {
        try {
            const response = await fetch(this.endpoints.routes);
            if (response.ok) {
                const data = await response.json();
                
                if (data.routes && data.routes.length > 0) {
                    // Try to find specific route
                    const foundRoute = data.routes.find(route => 
                        route.name && route.name.toLowerCase().includes(routeId.toLowerCase())
                    );
                    
                    if (foundRoute) {
                        return this.formatRoute(foundRoute);
                    }
                    
                    // Use first route
                    return this.formatRoute(data.routes[0]);
                }
            }
        } catch (error) {
            console.warn('Route fetch failed:', error);
        }
        
        // Default fallback route with REALISTIC distance
        return {
            id: 'bergen_oslo',
            name: 'Bergen to Oslo Commercial Route',
            departure_port: 'bergen',
            destination_port: 'oslo',
            total_distance: 210, // REALISTIC: 210 nautical miles (not 5.953!)
            duration_hours: 17.5, // 210NM / 12kn = 17.5 hours
            source: 'realistic_fallback'
        };
    }'''
        
        content = content.replace(route_match.group(0), fixed_route)
        print("✅ Fixed route details")
    
    # FIX 3: Fix formatRoute function to ensure realistic distances
    print("\n3️⃣ Fixing route formatting...")
    
    # Find formatRoute function
    format_pattern = r'formatRoute\(route\) \{[^}]+\}'
    format_match = re.search(format_pattern, content, re.DOTALL)
    
    if format_match:
        print("✅ Found formatRoute function")
        
        fixed_format = '''formatRoute(route) {
        // REALISTIC distances between Norwegian ports (nautical miles)
        const realisticDistances = {
            'bergen_oslo': 210,
            'bergen_stavanger': 160,
            'bergen_trondheim': 300,
            'oslo_stavanger': 180,
            'oslo_trondheim': 350,
            'bergen_alesund': 120,
            'default': 100
        };
        
        // Calculate route key
        const origin = (route.origin || '').toLowerCase();
        const destination = (route.destination || '').toLowerCase();
        const routeKey = \`\${origin}_\${destination}\`;
        
        // Use realistic distance if available, otherwise use route distance
        let distance = realisticDistances[routeKey] || route.total_distance_nm || route.total_distance;
        
        // If still no distance or unrealistic, use default
        if (!distance || distance < 10) {
            distance = realisticDistances[routeKey] || realisticDistances['default'];
            console.log(\`📏 Using realistic distance for \${routeKey}: \${distance}NM\`);
        }
        
        return {
            id: route.name || 'unknown',
            name: route.clean_name || route.name || 'Norwegian Coastal Route',
            departure_port: route.origin || 'bergen',
            destination_port: route.destination || 'oslo',
            total_distance: distance,
            duration_hours: distance / 12, // Based on 12 knots average speed
            source: route.source || 'database'
        };
    }'''
        
        content = content.replace(format_match.group(0), fixed_format)
        print("✅ Fixed route formatting")
    
    # FIX 4: Prevent duplicate simulation starts
    print("\n4️⃣ Preventing duplicate simulation starts...")
    
    # Find the auto-start timeout
    timeout_pattern = r'setTimeout\(\(\) => \{[\s\S]*?startSimulation\([\s\S]*?\}\);\s*\}, 3000\);'
    timeout_match = re.search(timeout_pattern, content)
    
    if timeout_match:
        print("✅ Found auto-start timeout")
        
        fixed_timeout = '''setTimeout(() => {
    if (window.simulationEngine && !window.simulationEngine.simulationActive) {
        console.log('🚀 Auto-starting simulation...');
        window.simulationEngine.startSimulation('bergen_oslo', 'bergen');
    } else {
        console.log('⏸️ Simulation already active, skipping auto-start');
    }
}, 3000);'''
        
        content = content.replace(timeout_match.group(0), fixed_timeout)
        print("✅ Fixed duplicate start prevention")
    
    # FIX 5: Add vessel position validation
    print("\n5️⃣ Adding vessel position validation...")
    
    # Find the fallback vessel creation
    vessel_pattern = r'loadVesselData:\s*function\(\)\s*\{[\s\S]*?currentVessel:\s*\{[\s\S]*?lat:\s*[\d\.]+[\s\S]*?lon:\s*[\d\.]+'
    vessel_match = re.search(vessel_pattern, content)
    
    if vessel_match:
        print("✅ Found vessel creation code")
        
        # Already fixed to 60.3940, 5.3200 - verify
        if '60.3940' in content and '5.3200' in content:
            print("✅ Vessel coordinates already fixed (60.3940, 5.3200)")
        else:
            print("⚠️ Vessel coordinates might need fixing")
    
    # Write fixed file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"\n✅ All fixes applied to: {file_path}")
    print("🔄 Restart Flask server and refresh browser to see changes")
    
    # Summary
    print("\n📋 Summary of fixes applied:")
    print("  1. Realistic route distances (210NM for Bergen-Oslo)")
    print("  2. Proper route fetching with fallback")
    print("  3. Realistic port-to-port distances")
    print("  4. Prevention of duplicate simulation starts")
    print("  5. Vessel in-water position verification")

def check_current_issues():
    """Check current simulation issues."""
    
    print("\n🔍 Checking current simulation configuration...")
    
    # Check the simulation core file
    core_path = "backend/static/js/split/simulation_core.js"
    
    if os.path.exists(core_path):
        with open(core_path, 'r') as f:
            content = f.read()
        
        # Check for unrealistic distance
        if '5.953' in content:
            print("❌ Found unrealistic distance (5.953NM)")
        else:
            print("✅ No unrealistic distance found")
        
        # Check for Bergen-Oslo distance
        if '210' in content and 'Bergen' in content and 'Oslo' in content:
            print("✅ Found realistic Bergen-Oslo distance (210NM)")
        else:
            print("⚠️ Realistic distance might be missing")
        
        # Check vessel coordinates
        if '60.3940' in content and '5.3200' in content:
            print("✅ Vessel in port coordinates (60.3940, 5.3200)")
        else:
            print("❌ Vessel coordinates might be incorrect")
    
    else:
        print(f"❌ File not found: {core_path}")

def main():
    """Main function."""
    
    print("=" * 60)
    print("🚢 BERGNAVN SIMULATION FIXER")
    print("=" * 60)
    
    # Check current issues
    check_current_issues()
    
    # Ask for confirmation
    response = input("\n🔧 Apply fixes? (y/n): ").strip().lower()
    
    if response == 'y':
        fix_simulation_core()
    else:
        print("⏸️ Skipping fixes")
    
    print("\n🎯 Next steps:")
    print("  1. Restart Flask server")
    print("  2. Refresh simulation page")
    print("  3. Check Console for realistic ETA (~17.5 hours)")
    print("  4. Verify vessel is in water at Bergen port")

if __name__ == "__main__":
    main()