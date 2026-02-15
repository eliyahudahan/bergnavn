// ============================================================================
// NORWEGIAN COASTAL ADMINISTRATION (NCA) REAL ROUTES
// ============================================================================

/**
 * Load REAL NCA routes with actual GPS coordinates
 */
async function loadRealNCARoutes() {
    console.log('🇳🇴 Loading REAL Norwegian Coastal Administration routes...');
    
    try {
        // Fetch route metadata - FIXED PATH
        const response = await fetch('/maritime/api/nca/routes');  // ✅ תוקן!
        if (!response.ok) {
            throw new Error(`NCA API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('NCA API returned failure');
        }
        
        console.log(`📊 NCA Database: ${data.total_routes} routes, ${data.cities_covered} cities, ${data.total_waypoints} waypoints`);
        console.log(`📁 Source: ${data.data_source}`);
        
        // Store globally
        window.ncaRoutes = data.routes || [];
        
        // Load waypoints for first few routes immediately
        await loadWaypointsForDisplay();
        
        // Display on map
        displayNcaRoutesOnMap();
        
        // Update dashboard with NCA info
        updateNcaDashboardInfo(data);
        
        return window.ncaRoutes;
        
    } catch (error) {
        console.error('❌ Failed to load NCA routes:', error);
        
        // Fallback to rtz_waypoints
        console.log('🔄 Falling back to rtz_waypoints...');
        if (window.rtzWaypoints && window.dashboardData?.routes) {
            window.rtzWaypoints.drawMultipleRoutes(window.dashboardData.routes);
        }
    }
}

/**
 * Load waypoints for routes that will be displayed
 */
async function loadWaypointsForDisplay() {
    if (!window.ncaRoutes || window.ncaRoutes.length === 0) {
        return;
    }
    
    console.log('🔄 Loading waypoints for NCA routes...');
    
    // Load waypoints for first 10 routes
    const routesToLoad = window.ncaRoutes.slice(0, Math.min(10, window.ncaRoutes.length));
    
    for (const route of routesToLoad) {
        try {
            const waypoints = await fetchNcaWaypoints(route.route_name);
            if (waypoints && waypoints.length > 0) {
                route.waypoints = waypoints;
                route.has_loaded_waypoints = true;
                console.log(`   ✅ ${route.route_name}: ${waypoints.length} waypoints`);
            }
        } catch (error) {
            console.log(`   ⚠️ ${route.route_name}: No waypoints loaded`);
        }
    }
}

/**
 * Fetch waypoints for a specific NCA route
 */
async function fetchNcaWaypoints(routeName) {
    try {
        const response = await fetch(`/maritime/api/nca/route/${encodeURIComponent(routeName)}/waypoints`);  // ✅ תוקן!
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.waypoints) {
                return data.waypoints;
            }
        }
    } catch (error) {
        console.log(`Waypoint fetch error for ${routeName}:`, error.message);
    }
    
    return null;
}

/**
 * Display NCA routes on map with REAL coordinates
 */
function displayNcaRoutesOnMap() {
    if (!window.ncaRoutes || window.ncaRoutes.length === 0) {
        console.log('No NCA routes to display');
        return;
    }
    
    console.log(`🗺️ Displaying ${window.ncaRoutes.length} NCA routes with REAL coordinates`);
    
    // Color coding by city
    const cityColors = {
        'bergen': '#1e88e5',      // Blue - Bergen
        'oslo': '#43a047',        // Green - Oslo
        'stavanger': '#fb8c00',   // Orange - Stavanger
        'trondheim': '#e53935',   // Red - Trondheim
        'kristiansand': '#8e24aa',// Purple - Kristiansand
        'alesund': '#3949ab',     // Indigo - Ålesund
        'andalsnes': '#00897b',   // Teal - Åndalsnes
        'drammen': '#f4511e',     // Deep Orange - Drammen
        'flekkefjord': '#5e35b1', // Deep Purple - Flekkefjord
        'sandefjord': '#039be5'   // Light Blue - Sandefjord
    };
    
    let displayedCount = 0;
    
    window.ncaRoutes.forEach((route, index) => {
        try {
            const sourceCity = (route.source_city || '').toLowerCase();
            const color = cityColors[sourceCity] || '#607d8b';
            
            if (route.waypoints && route.waypoints.length > 1) {
                const latLngs = route.waypoints.map(wp => [wp.lat, wp.lon]);
                
                const polyline = L.polyline(latLngs, {
                    color: color,
                    weight: 4,
                    opacity: 0.8,
                    className: 'nca-route-line'
                }).addTo(window.map);
                
                // Add start marker
                L.marker(latLngs[0], {
                    icon: L.divIcon({
                        className: 'nca-start-marker',
                        html: `<div style="background: ${color}; color: white; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">S</div>`,
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    })
                }).addTo(window.map).bindPopup(`<strong>Start:</strong> ${route.origin}`);
                
                // Add end marker
                L.marker(latLngs[latLngs.length - 1], {
                    icon: L.divIcon({
                        className: 'nca-end-marker',
                        html: `<div style="background: ${color}; color: white; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">E</div>`,
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    })
                }).addTo(window.map).bindPopup(`<strong>End:</strong> ${route.destination}`);
                
                displayedCount++;
                console.log(`   ✅ ${route.route_name}: ${route.waypoints.length} real waypoints`);
            }
            
        } catch (error) {
            console.error(`Error displaying NCA route ${index}:`, error);
        }
    });
    
    console.log(`✅ Displayed ${displayedCount} NCA routes with REAL coordinates`);
}

/**
 * Update dashboard with NCA information
 */
function updateNcaDashboardInfo(data) {
    const routeCountElement = document.getElementById('route-count');
    if (routeCountElement) {
        routeCountElement.textContent = data.total_routes;
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        if (window.map) {
            loadRealNCARoutes();
        }
    }, 2000);
});

window.loadRealNCARoutes = loadRealNCARoutes;