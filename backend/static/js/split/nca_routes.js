// ============================================================================
// NORWEGIAN COASTAL ADMINISTRATION (NCA) REAL ROUTES
// ============================================================================

/**
 * Load REAL NCA routes with actual GPS coordinates
 */
async function loadRealNCARoutes() {
    console.log('🇳🇴 Loading REAL Norwegian Coastal Administration routes...');
    
    try {
        // Fetch route metadata
        const response = await fetch('/nca/api/nca/routes');
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
        activeRoutes = window.ncaRoutes;
        
        // Load waypoints for first few routes immediately
        await loadWaypointsForDisplay();
        
        // Display on map
        displayNcaRoutesOnMap();
        
        // Update dashboard with NCA info
        updateNcaDashboardInfo(data);
        
        return window.ncaRoutes;
        
    } catch (error) {
        console.error('❌ Failed to load NCA routes:', error);
        
        // Fallback to existing API
        console.log('🔄 Falling back to standard routes...');
        return await loadRTZRoutes();
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
    
    // Load waypoints for first 10 routes (or all if less)
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
        const response = await fetch(`/nca/api/nca/route/${encodeURIComponent(routeName)}/waypoints`);
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
    
    // Clear existing layers
    clearRouteLayers();
    
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
            
            // Check if we have real waypoints
            if (route.waypoints && route.waypoints.length > 1) {
                // We have REAL coordinates! 🎉
                const latLngs = route.waypoints.map(wp => [wp.lat, wp.lon]);
                
                const polyline = L.polyline(latLngs, {
                    color: color,
                    weight: 4,
                    opacity: 0.8,
                    dashArray: null,
                    className: 'nca-route-line'
                }).addTo(maritimeMap);
                
                // Add start marker
                L.marker(latLngs[0], {
                    icon: L.divIcon({
                        className: 'nca-start-marker',
                        html: `<div style="background: ${color}; color: white; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">S</div>`,
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    })
                }).addTo(maritimeMap).bindPopup(`<strong>Start:</strong> ${route.origin}`);
                
                // Add end marker
                L.marker(latLngs[latLngs.length - 1], {
                    icon: L.divIcon({
                        className: 'nca-end-marker',
                        html: `<div style="background: ${color}; color: white; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">E</div>`,
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    })
                }).addTo(maritimeMap).bindPopup(`<strong>End:</strong> ${route.destination}`);
                
                // Enhanced popup
                const popupContent = createNcaRoutePopup(route);
                polyline.bindPopup(popupContent);
                
                const routeId = `nca_route_${index}`;
                routeLayers[routeId] = polyline;
                
                displayedCount++;
                console.log(`   ✅ ${route.route_name}: ${route.waypoints.length} real waypoints`);
                
            } else {
                // No real waypoints yet, create approximate line
                console.log(`   ⏳ ${route.route_name}: Waiting for waypoints`);
            }
            
        } catch (error) {
            console.error(`Error displaying NCA route ${index}:`, error);
        }
    });
    
    console.log(`✅ Displayed ${displayedCount} NCA routes with REAL coordinates`);
    
    // Update counters
    updateRouteCounters();
    
    // If we have real routes, update UI
    if (displayedCount > 0) {
        document.getElementById('route-count').textContent = displayedCount;
        document.getElementById('route-display-count').textContent = displayedCount;
        document.getElementById('actual-routes-badge').textContent = displayedCount;
        
        // Show NCA badge
        const ncaBadge = document.createElement('span');
        ncaBadge.className = 'badge bg-success ms-2';
        ncaBadge.innerHTML = '<i class="fas fa-map-marked-alt"></i> NCA Real Data';
        document.querySelector('.dashboard-header h1').appendChild(ncaBadge);
    }
}

/**
 * Create enhanced popup for NCA routes
 */
function createNcaRoutePopup(route) {
    return `
        <div style="min-width: 250px;">
            <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <h6 style="margin: 0; color: #1a73e8;">
                    <i class="fas fa-ship"></i> ${route.clean_name}
                </h6>
            </div>
            
            <table class="table table-sm" style="font-size: 13px; margin-bottom: 10px;">
                <tr>
                    <td><strong><i class="fas fa-map-pin"></i> Origin:</strong></td>
                    <td>${route.origin}</td>
                </tr>
                <tr>
                    <td><strong><i class="fas fa-flag-checkered"></i> Destination:</strong></td>
                    <td>${route.destination}</td>
                </tr>
                <tr>
                    <td><strong><i class="fas fa-road"></i> Distance:</strong></td>
                    <td>${route.total_distance_nm || '?'} NM</td>
                </tr>
                <tr>
                    <td><strong><i class="fas fa-dot-circle"></i> Waypoints:</strong></td>
                    <td>${route.waypoint_count || '?'}</td>
                </tr>
                <tr>
                    <td><strong><i class="fas fa-city"></i> Port:</strong></td>
                    <td>${route.source_city}</td>
                </tr>
                <tr>
                    <td><strong><i class="fas fa-database"></i> Source:</strong></td>
                    <td>${route.data_source || 'NCA'}</td>
                </tr>
            </table>
            
            <div style="background: #e8f5e9; padding: 8px; border-radius: 4px; font-size: 12px;">
                <i class="fas fa-check-circle text-success"></i>
                <strong>Real GPS Coordinates</strong><br>
                <small>From Norwegian Coastal Administration</small>
            </div>
            
            ${route.has_loaded_waypoints ? 
                '<div class="text-success mt-2"><small><i class="fas fa-check"></i> Waypoints loaded</small></div>' : 
                '<div class="text-warning mt-2"><small><i class="fas fa-sync"></i> Loading waypoints...</small></div>'
            }
        </div>
    `;
}

/**
 * Update dashboard with NCA information
 */
function updateNcaDashboardInfo(data) {
    // Update route count badge
    const badge = document.getElementById('data-truth-badge');
    if (badge) {
        badge.innerHTML = `
            <i class="fas fa-database me-1"></i>
            <span id="route-count-badge">${data.total_routes}</span> NCA Real Routes
            <span class="badge bg-success ms-1">
                <i class="fas fa-check-circle"></i> Verified
            </span>
        `;
    }
    
    // Update data info alert
    const alert = document.getElementById('data-info-alert');
    if (alert) {
        alert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-map-marked-alt me-3"></i>
                <div>
                    <strong>Norwegian Coastal Administration Data</strong>
                    <p class="mb-0 small">
                        Showing <strong>${data.total_routes}</strong> real routes from 
                        <strong>${data.cities_covered}</strong> Norwegian ports.
                        <span class="text-success ms-2">
                            <i class="fas fa-check-circle"></i> Official NCA Data
                        </span>
                    </p>
                </div>
            </div>
        `;
    }
    
    // Update route table header
    const routeHeader = document.querySelector('.dashboard-card .card-header h5');
    if (routeHeader) {
        routeHeader.innerHTML = `
            <i class="fas fa-route me-2"></i>
            NCA Maritime Routes 
            <span class="badge bg-primary ms-2">${data.total_routes}</span>
            <span class="badge bg-success ms-1" title="Real NCA data">
                <i class="fas fa-map-marked-alt"></i> Official
            </span>
        `;
    }
}

/**
 * Initialize NCA routes when dashboard loads
 */
document.addEventListener('DOMContentLoaded', function() {
    // Replace the standard route loading with NCA loading
    if (typeof loadRTZRoutes === 'function') {
        // Store original function
        window.originalLoadRTZRoutes = loadRTZRoutes;
        
        // Replace with NCA loader
        window.loadRTZRoutes = loadRealNCARoutes;
        
        console.log('🔄 Replaced standard route loader with NCA loader');
    }
    
    // Also add NCA loading to map initialization
    setTimeout(() => {
        if (window.maritimeMap) {
            loadRealNCARoutes();
        }
    }, 3000);
});

// Export NCA functions
window.loadRealNCARoutes = loadRealNCARoutes;
window.displayNcaRoutesOnMap = displayNcaRoutesOnMap;
