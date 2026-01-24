// debug_simulation.js - Debug the simulation page loading
// English comments only inside file.

console.log("🔍 Starting simulation debug...");

// Test 1: Check if all required elements exist
const elements = [
    'data-source-alert',
    'data-source-text',
    'data-source-badge',
    'real-time-map',
    'vessel-info-container',
    'ports-scan-list'
];

elements.forEach(id => {
    const element = document.getElementById(id);
    console.log(`${element ? '✅' : '❌'} Element #${id}:`, element ? 'Found' : 'NOT FOUND');
});

// Test 2: Check API endpoints
const endpoints = [
    '/maritime/api/ais-data',
    '/maritime/api/health',
    '/maritime/api/rtz/routes/deduplicated'
];

async function testEndpoints() {
    for (const endpoint of endpoints) {
        try {
            const response = await fetch(endpoint);
            console.log(`${response.ok ? '✅' : '❌'} ${endpoint}: ${response.status} ${response.statusText}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log(`   Data:`, data);
            }
        } catch (error) {
            console.log(`❌ ${endpoint}: ${error.message}`);
        }
    }
}

// Test 3: Check if EmpiricalVesselTracker class exists
console.log("🔧 Checking JavaScript classes...");
console.log("EmpiricalVesselTracker:", typeof window.EmpiricalVesselTracker);
console.log("vesselTracker:", window.vesselTracker);
console.log("RealTimeSimulation:", typeof window.RealTimeSimulation);
console.log("simulationEngine:", window.simulationEngine);

// Test 4: Check console for errors
window.addEventListener('error', function(event) {
    console.error("🚨 Global error caught:", event.error);
});

// Run tests
setTimeout(() => {
    console.log("\n🚀 Running API tests...");
    testEndpoints();
}, 1000);

// Add a button to manually trigger vessel search
setTimeout(() => {
    const debugButton = document.createElement('button');
    debugButton.innerHTML = '🔧 Manual Debug';
    debugButton.style.position = 'fixed';
    debugButton.style.top = '10px';
    debugButton.style.right = '10px';
    debugButton.style.zIndex = '9999';
    debugButton.style.padding = '10px';
    debugButton.style.backgroundColor = '#ff6b6b';
    debugButton.style.color = 'white';
    debugButton.style.border = 'none';
    debugButton.style.borderRadius = '5px';
    debugButton.style.cursor = 'pointer';
    
    debugButton.onclick = async function() {
        console.log("🔄 Manual debug triggered...");
        
        // Try to load vessel data manually
        if (window.vesselTracker && typeof window.vesselTracker.loadVesselData === 'function') {
            console.log("Calling vesselTracker.loadVesselData()...");
            await window.vesselTracker.loadVesselData();
        }
        
        // Try to initialize map
        if (window.vesselTracker && typeof window.vesselTracker.initMap === 'function') {
            console.log("Calling vesselTracker.initMap()...");
            window.vesselTracker.initMap();
        }
    };
    
    document.body.appendChild(debugButton);
    console.log("✅ Debug button added to page");
}, 2000);

console.log("🔍 Debug script loaded. Check browser console (F12) for results.");