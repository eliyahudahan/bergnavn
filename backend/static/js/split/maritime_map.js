/**
 * Maritime Map Module for BergNavn Dashboard
 * Handles Leaflet map initialization, RTZ route display, and real-time vessel tracking
 * FIXED: Count routes per port correctly
 * FIXED: Zoom button works with correct route IDs
 */

// Global map variables
let maritimeMap = null;
let vesselMarkers = [];
let activeRoutes = [];
let routePolylines = []; // Store references to all route lines
let routeMarkers = [];   // Store references to all route markers

// Real-time vessel tracking variables
let realTimeVesselMarker = null;
let vesselUpdateInterval = null;
let vesselTrackingActive = false;

// Store route counts per port
let portRouteCounts = {};

// Make zoom functions available globally with better error handling
window.zoomToRoute = function(routeIdentifier) {
    console.log(`🎯 zoomToRoute called with:`, routeIdentifier);
    
    if (!maritimeMap) {
        console.error('❌ Map not initialized');
        showNotification('Map not ready', 'error');
        return false;
    }
    
    // Try to find the route
    let route = null;
    let routeIndex = -1;
    
    // Check if identifier is numeric index
    if (typeof routeIdentifier === 'number') {
        routeIndex = routeIdentifier;
        route = activeRoutes[routeIndex];
    } 
    // Check if identifier is string ID
    else if (typeof routeIdentifier === 'string') {
        // Try to find by route_id
        routeIndex = activeRoutes.findIndex(r => {
            // Try different ID formats
            if (r.route_id && r.route_id.toString() === routeIdentifier) return true;
            if (r.id && r.id.toString() === routeIdentifier) return true;
            if (r.routeId && r.routeId.toString() === routeIdentifier) return true;
            
            // Try to match by clean_name or route_name
            const routeName = r.clean_name || r.route_name || '';
            if (routeName.toLowerCase().includes(routeIdentifier.toLowerCase())) return true;
            
            return false;
        });
        
        if (routeIndex !== -1) {
            route = activeRoutes[routeIndex];
        } else {
            // Try to parse as index from route-XX format
            const match = routeIdentifier.match(/route[_-]?(\d+)/i);
            if (match) {
                routeIndex = parseInt(match[1]);
                if (routeIndex < activeRoutes.length) {
                    route = activeRoutes[routeIndex];
                }
            }
        }
    }
    
    if (!route) {
        console.error(`❌ Route not found: ${routeIdentifier}`);
        showNotification(`Could not find route: ${routeIdentifier}`, 'error');
        return false;
    }
    
    console.log(`🎯 Found route: ${route.clean_name || route.route_name} at index ${routeIndex}`);
    
    const waypoints = extractWaypointsFromRoute(route);
    
    if (waypoints.length < 2) {
        console.warn(`Cannot zoom: Route has insufficient waypoints (${waypoints.length})`);
        showNotification(`Cannot zoom: Route has no waypoints`, 'warning');
        return false;
    }
    
    // Create bounds from waypoints
    const bounds = L.latLngBounds(waypoints.map(wp => [wp.lat, wp.lon]));
    
    if (bounds.isValid()) {
        maritimeMap.fitBounds(bounds.pad(0.1));
        
        // Flash the route to highlight it
        highlightRoute(routeIndex);
        
        // Show notification with route name
        const routeName = route.clean_name || route.route_name || `Route ${routeIndex + 1}`;
        showNotification(`Zoomed to route: ${routeName}`, 'success');
        
        return true;
    } else {
        console.error('❌ Invalid bounds for route');
        showNotification('Invalid route bounds', 'error');
        return false;
    }
};

/**
 * Highlight a specific route by making it more visible
 */
window.highlightRoute = function(routeIndex) {
    if (!maritimeMap || !activeRoutes[routeIndex]) return;
    
    // Reset all routes to normal
    routePolylines.forEach(polyline => {
        polyline.setStyle({ weight: 4, opacity: 0.8 });
    });
    
    // Highlight the selected route
    const route = activeRoutes[routeIndex];
    if (route.mapPolyline) {
        route.mapPolyline.setStyle({ 
            weight: 8, 
            opacity: 1.0,
            color: '#ff5722' // Orange highlight color
        });
        
        // Bring to front
        route.mapPolyline.bringToFront();
        
        console.log(`🔦 Highlighted route ${routeIndex}: ${route.clean_name || route.route_name}`);
    }
};

// Main map initialization - MUST be called first
function initMaritimeMap() {
    console.log('🌊 Maritime Map: Initializing...');
    
    const mapElement = document.getElementById('maritime-map');
    if (!mapElement) {
        console.error('❌ Map container not found');
        return null;
    }
    
    if (!maritimeMap) {
        // Create map centered on Norway
        maritimeMap = L.map('maritime-map').setView([64.0, 10.0], 6);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(maritimeMap);
        
        // Add Norwegian waters layer
        L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
            attribution: '© OpenSeaMap',
            opacity: 0.4,
            maxZoom: 18,
        }).addTo(maritimeMap);
        
        console.log('✅ Maritime map created');
        
        // Make map available globally
        window.map = maritimeMap;
        console.log('✅ Map saved to window.map');
    }
    
    return maritimeMap;
}

/**
 * Load and display RTZ routes from API endpoint
 * Uses /maritime/api/rtz/complete which contains full route data with waypoints
 * 
 * UPDATED: Sends routesDataLoaded event for RTZ Waypoints module
 */
function loadAndDisplayRTZRoutes() {
    console.log('🗺️ RTZ Routes: Loading from API...');
    
    // Clear any existing routes first
    clearAllRouteLayers();
    
    // Try to load from API first (contains waypoints)
    fetch('/maritime/api/rtz/complete')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.routes && Array.isArray(data.routes) && data.routes.length > 0) {
                console.log(`✅ Loaded ${data.routes.length} routes from API`);
                activeRoutes = data.routes;
                
                // Count routes per port
                countRoutesByPort();
                
                // Update port counters in UI
                updatePortCounters();
                
                // Save to window for other scripts
                window.routesData = activeRoutes;
                window.allRoutesData = activeRoutes; // For RTZ Waypoints module
                
                // Display routes on map
                displayRoutesOnMap();
                
                // Update UI counters
                updateRouteCounters();
                
                // ========== Send event for RTZ Waypoints module ==========
                console.log('📤 Dispatching routesDataLoaded event for waypoints...');
                const event = new CustomEvent('routesDataLoaded', {
                    detail: {
                        routes: activeRoutes,
                        source: 'maritime_map.js',
                        timestamp: new Date().toISOString(),
                        totalRoutes: activeRoutes.length,
                        routesWithWaypoints: activeRoutes.filter(r => r.waypoints && r.waypoints.length > 0).length,
                        hasWaypointsData: true
                    }
                });
                document.dispatchEvent(event);
                console.log('✅ Event dispatched successfully');
                // ========== END ==========
                
                // Show success message
                showNotification(`Loaded ${activeRoutes.length} RTZ routes with waypoints`, 'success');
                
                // Start vessel tracking after routes are loaded
                setTimeout(() => {
                    startVesselTracking();
                }, 2000);
                
                return activeRoutes;
            } else {
                console.warn('⚠️ API returned no routes, trying template data');
                return loadRoutesFromTemplate();
            }
        })
        .catch(error => {
            console.error('❌ Error loading from API:', error);
            console.log('🔄 Falling back to template data');
            return loadRoutesFromTemplate();
        });
}

/**
 * Count routes by port for the port counters display
 */
function countRoutesByPort() {
    portRouteCounts = {};
    
    activeRoutes.forEach(route => {
        const port = (route.source_city || '').toLowerCase().replace('å', 'a').replace('Å', 'a');
        if (port) {
            if (!portRouteCounts[port]) {
                portRouteCounts[port] = 0;
            }
            portRouteCounts[port]++;
        }
    });
    
    console.log('📊 Route counts by port:', portRouteCounts);
}

/**
 * Update port counters in the UI
 */
function updatePortCounters() {
    // Map of port names to display names
    const portDisplayNames = {
        'bergen': 'Bergen',
        'oslo': 'Oslo',
        'stavanger': 'Stavanger',
        'trondheim': 'Trondheim',
        'alesund': 'Ålesund',
        'andalsnes': 'Åndalsnes',
        'kristiansand': 'Kristiansand',
        'drammen': 'Drammen',
        'sandefjord': 'Sandefjord',
        'flekkefjord': 'Flekkefjord'
    };
    
    // Update each port badge
    Object.keys(portDisplayNames).forEach(portKey => {
        const count = portRouteCounts[portKey] || 0;
        const displayName = portDisplayNames[portKey];
        
        // Find all city badges with this port
        const badges = document.querySelectorAll(`.city-badge[data-port="${portKey}"]`);
        badges.forEach(badge => {
            const countSpan = badge.querySelector('.port-count');
            if (countSpan) {
                countSpan.textContent = count;
            }
        });
        
        // Also update any badges with the display name
        const displayBadges = document.querySelectorAll('.city-badge');
        displayBadges.forEach(badge => {
            if (badge.textContent.includes(displayName)) {
                const countSpan = badge.querySelector('.port-count');
                if (countSpan) {
                    countSpan.textContent = count;
                }
            }
        });
    });
    
    console.log('✅ Updated port counters in UI');
}

/**
 * Fallback: Load routes from template data (doesn't have waypoints)
 */
function loadRoutesFromTemplate() {
    try {
        // Get routes from embedded JSON in HTML
        const routesDataElement = document.getElementById('routes-data');
        if (!routesDataElement || !routesDataElement.textContent) {
            console.error('❌ No routes data found in HTML');
            return [];
        }
        
        activeRoutes = JSON.parse(routesDataElement.textContent);
        console.log(`✅ Found ${activeRoutes.length} routes in HTML (no waypoints)`);
        
        // Count routes per port
        countRoutesByPort();
        
        // Update port counters
        updatePortCounters();
        
        // Save to window
        window.routesData = activeRoutes;
        window.allRoutesData = activeRoutes;
        
        // Update UI but can't display on map without waypoints
        updateRouteCounters();
        
        // Send event even for template data (waypoints module might handle it)
        if (activeRoutes.length > 0) {
            const event = new CustomEvent('routesDataLoaded', {
                detail: {
                    routes: activeRoutes,
                    source: 'template_data',
                    timestamp: new Date().toISOString(),
                    totalRoutes: activeRoutes.length,
                    routesWithWaypoints: 0,
                    hasWaypointsData: false
                }
            });
            document.dispatchEvent(event);
        }
        
        // Start vessel tracking anyway
        setTimeout(() => {
            startVesselTracking();
        }, 2000);
        
        // Show warning
        showNotification(`Loaded ${activeRoutes.length} routes (no waypoints in template data)`, 'warning');
        
        return activeRoutes;
        
    } catch (error) {
        console.error('❌ Error loading RTZ routes from template:', error);
        return [];
    }
}

/**
 * Display all routes on the map
 */
function displayRoutesOnMap() {
    if (!maritimeMap) {
        console.error('❌ Cannot display routes: No map available');
        return;
    }
    
    if (!activeRoutes.length) {
        console.warn('⚠️ No routes to display');
        return;
    }
    
    console.log(`🗺️ Displaying ${activeRoutes.length} routes on map...`);
    
    // Clear any existing routes
    clearAllRouteLayers();
    
    let displayedCount = 0;
    let skippedCount = 0;
    
    // Display each route
    activeRoutes.forEach((route, index) => {
        try {
            const success = displaySingleRoute(route, index);
            if (success) {
                displayedCount++;
            } else {
                skippedCount++;
            }
        } catch (error) {
            console.error(`❌ Error displaying route ${index}:`, error);
            skippedCount++;
        }
    });
    
    console.log(`✅ Successfully displayed ${displayedCount} routes, skipped ${skippedCount}`);
    
    // Fit map to show all routes
    if (displayedCount > 0) {
        fitMapToRoutes();
    }
    
    // Add legend (updated to include real-time vessel)
    addMapLegend();
}

/**
 * Display a single route on the map
 */
function displaySingleRoute(route, index) {
    if (!maritimeMap) return false;
    
    // Debug logging
    console.log(`📋 Processing route ${index}: ${route.clean_name || route.route_name || 'Unnamed route'}`);
    
    // Get route waypoints - MUST exist for display
    const waypoints = extractWaypointsFromRoute(route);
    
    if (waypoints.length < 2) {
        console.warn(`Route ${index} has insufficient waypoints: ${waypoints.length}`, {
            routeName: route.clean_name || route.route_name,
            hasWaypointsProperty: !!route.waypoints,
            waypointCountProperty: route.waypoint_count,
            extractedWaypoints: waypoints.length
        });
        return false;
    }
    
    console.log(`📍 Route ${index} has ${waypoints.length} waypoints`);
    
    // Choose color based on source city
    const colors = {
        'bergen': '#1e88e5',     // Blue
        'oslo': '#43a047',       // Green
        'stavanger': '#f39c12',  // Orange
        'trondheim': '#e74c3c',  // Red
        'alesund': '#9b59b6',    // Purple
        'andalsnes': '#3498db',  // Light Blue
        'kristiansand': '#2ecc71', // Emerald
        'drammen': '#e67e22',    // Carrot
        'sandefjord': '#16a085', // Teal
        'flekkefjord': '#8e44ad'  // Violet
    };
    
    const port = (route.source_city || '').toLowerCase();
    const color = colors[port] || '#1e88e5';
    
    console.log(`🎨 Route ${index} color: ${color} (port: ${port})`);
    
    // Create coordinates array for polyline
    const coordinates = waypoints.map(wp => [wp.lat, wp.lon]);
    
    // Draw the route line
    const polyline = L.polyline(coordinates, {
        color: color,
        weight: 4,
        opacity: 0.8,
        lineCap: 'round',
        lineJoin: 'round',
        className: 'rtz-route-line'
    }).addTo(maritimeMap);
    
    // Store reference for later manipulation
    routePolylines.push(polyline);
    
    // Add start marker (GREEN)
    const startMarker = L.circleMarker(coordinates[0], {
        color: '#28a745',
        fillColor: '#28a745',
        fillOpacity: 1.0,
        radius: 8,
        weight: 3,
        className: 'route-start-marker'
    }).addTo(maritimeMap);
    
    startMarker.bindTooltip(`<b>Start:</b> ${route.origin || 'Unknown'}`);
    
    // Add end marker (RED)
    const endMarker = L.circleMarker(coordinates[coordinates.length - 1], {
        color: '#dc3545',
        fillColor: '#dc3545',
        fillOpacity: 1.0,
        radius: 8,
        weight: 3,
        className: 'route-end-marker'
    }).addTo(maritimeMap);
    
    endMarker.bindTooltip(`<b>End:</b> ${route.destination || 'Unknown'}`);
    
    // Store marker references
    routeMarkers.push({ start: startMarker, end: endMarker, routeIndex: index });
    
    // Create popup content
    const popupContent = createRoutePopup(route, index, color);
    
    // Bind popups
    polyline.bindPopup(popupContent);
    startMarker.bindPopup(popupContent);
    endMarker.bindPopup(popupContent);
    
    // Add hover effects
    polyline.on('mouseover', function() {
        this.setStyle({ weight: 6, opacity: 1.0 });
        // Also highlight markers
        startMarker.setStyle({ radius: 10 });
        endMarker.setStyle({ radius: 10 });
    });
    
    polyline.on('mouseout', function() {
        this.setStyle({ weight: 4, opacity: 0.8 });
        // Reset markers
        startMarker.setStyle({ radius: 8 });
        endMarker.setStyle({ radius: 8 });
    });
    
    // Add click handler to zoom to route
    polyline.on('click', function() {
        zoomToRoute(index);
    });
    
    // Store route ID for later reference
    const routeId = route.route_id || `route_${index}`;
    route.routeElementId = routeId;
    route.mapPolyline = polyline; // Store reference on route object
    
    console.log(`✅ Added route ${index}: ${route.clean_name || route.route_name || 'Unnamed route'}`);
    
    return true;
}

/**
 * Extract waypoints from route data in various formats
 * Enhanced with better debugging
 */
function extractWaypointsFromRoute(route) {
    let waypoints = [];
    
    // DEBUG: Log what we're working with
    console.log(`🛠️ Extracting waypoints for: ${route.clean_name || route.route_name}`);
    console.log(`   Has 'waypoints' property: ${!!route.waypoints}`);
    console.log(`   Has 'geometry' property: ${!!route.geometry}`);
    console.log(`   Has 'path' property: ${!!route.path}`);
    
    // Format 1: Direct waypoints array (the main format from API)
    if (route.waypoints && Array.isArray(route.waypoints)) {
        console.log(`   Found ${route.waypoints.length} waypoints in route.waypoints`);
        
        waypoints = route.waypoints.map((wp, i) => {
            // Handle various waypoint formats
            if (wp && typeof wp === 'object') {
                return {
                    lat: wp.lat || wp[1],
                    lon: wp.lon || wp[0],
                    name: wp.name || `WP${i + 1}`
                };
            }
            // Handle array format [lon, lat]
            else if (Array.isArray(wp) && wp.length >= 2) {
                return {
                    lat: wp[1],
                    lon: wp[0],
                    name: `WP${i + 1}`
                };
            }
            // Invalid format
            return null;
        }).filter(wp => wp !== null); // Remove null entries
        
        console.log(`   Successfully parsed ${waypoints.length} waypoints`);
    }
    // Format 2: Geometry coordinates
    else if (route.geometry && route.geometry.coordinates) {
        console.log(`   Found geometry with ${route.geometry.coordinates.length} coordinates`);
        waypoints = route.geometry.coordinates.map((coord, i) => ({
            lat: coord[1],
            lon: coord[0],
            name: `WP${i + 1}`
        }));
    }
    // Format 3: Path array
    else if (route.path && Array.isArray(route.path)) {
        console.log(`   Found path with ${route.path.length} points`);
        waypoints = route.path.map((coord, i) => ({
            lat: coord[1] || coord.lat,
            lon: coord[0] || coord.lon,
            name: `WP${i + 1}`
        }));
    }
    else {
        console.warn(`   No waypoints found in any expected format`);
    }
    
    // Filter out invalid coordinates
    const validWaypoints = waypoints.filter(wp => {
        const isValid = wp && wp.lat && wp.lon && 
                       !isNaN(wp.lat) && !isNaN(wp.lon) &&
                       wp.lat >= 55 && wp.lat <= 72 &&   // Norwegian latitude range
                       wp.lon >= 0 && wp.lon <= 32;      // Norwegian longitude range
        
        if (!isValid && wp) {
            console.warn(`   Invalid waypoint filtered out: lat=${wp.lat}, lon=${wp.lon}`);
        }
        
        return isValid;
    });
    
    console.log(`   ${validWaypoints.length} valid waypoints after filtering`);
    
    return validWaypoints;
}

/**
 * Create HTML popup for a route
 */
function createRoutePopup(route, index, color) {
    const routeName = route.clean_name || 
                     (route.route_name ? 
                      route.route_name.replace('NCA_', '')
                                     .replace('_2025', '')
                                     .replace('_2024', '')
                                     .replace(/_/g, ' ') : 
                      `Route ${index + 1}`);
    
    const distance = route.total_distance_nm ? 
                    `${route.total_distance_nm.toFixed(1)} NM` : 
                    'Unknown';
    
    const waypointCount = route.waypoints ? route.waypoints.length : 
                         (route.waypoint_count || 'Unknown');
    
    return `
        <div style="min-width: 250px;">
            <div style="background: ${color}; color: white; padding: 10px; border-radius: 5px 5px 0 0;">
                <i class="fas fa-route"></i> ${routeName}
            </div>
            <div style="padding: 10px; background: white;">
                <table style="width: 100%; font-size: 12px;">
                    <tr>
                        <td><strong>Origin:</strong></td>
                        <td style="color: #28a745;">${route.origin || 'Unknown'}</td>
                    </tr>
                    <tr>
                        <td><strong>Destination:</strong></td>
                        <td style="color: #dc3545;">${route.destination || 'Unknown'}</td>
                    </tr>
                    <tr>
                        <td><strong>Distance:</strong></td>
                        <td>${distance}</td>
                    </tr>
                    <tr>
                        <td><strong>Waypoints:</strong></td>
                        <td>${waypointCount}</td>
                    </tr>
                    <tr>
                        <td><strong>Port:</strong></td>
                        <td>${route.source_city || 'Unknown'}</td>
                    </tr>
                </table>
                <div style="margin-top: 10px; display: flex; gap: 5px;">
                    <button onclick="zoomToRoute(${index})"
                            style="background: ${color}; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;">
                        <i class="fas fa-search-plus"></i> Zoom to Route
                    </button>
                    <button onclick="highlightRoute(${index})"
                            style="background: #ffc107; color: #212529; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;">
                        <i class="fas fa-highlighter"></i> Highlight
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Fit map to show all routes
 */
function fitMapToRoutes() {
    if (!maritimeMap || routePolylines.length === 0) return;
    
    // Get bounds from all polylines
    const bounds = L.latLngBounds();
    
    routePolylines.forEach(polyline => {
        if (polyline.getBounds) {
            bounds.extend(polyline.getBounds());
        }
    });
    
    if (bounds.isValid()) {
        maritimeMap.fitBounds(bounds.pad(0.1));
        console.log('🗺️ Map fitted to routes');
    }
}

/**
 * Add legend to map (updated for real-time vessel)
 */
function addMapLegend() {
    if (!maritimeMap) return;
    
    const legend = L.control({ position: 'bottomleft' });
    
    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'leaflet-control-legend');
        div.innerHTML = `
            <div class="legend-title">Maritime Map Legend</div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #28a745;"></div>
                <div class="legend-label"><i class="fas fa-play"></i> Route Start</div>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #dc3545;"></div>
                <div class="legend-label"><i class="fas fa-flag-checkered"></i> Route End</div>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="height: 4px; background-color: #1e88e5; margin-top: 8px;"></div>
                <div class="legend-label"><i class="fas fa-route"></i> RTZ Route</div>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #007bff;"></div>
                <div class="legend-label"><i class="fas fa-map-marker-alt"></i> Waypoint</div>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #28a745;"></div>
                <div class="legend-label"><i class="fas fa-ship"></i> Real-time Vessel (LIVE)</div>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ffc107;"></div>
                <div class="legend-label"><i class="fas fa-ship"></i> Empirical Vessel (SIM)</div>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #17a2b8;"></div>
                <div class="legend-label"><i class="fas fa-cloud-sun"></i> Weather Station</div>
            </div>
            <div style="font-size: 10px; color: #666; margin-top: 8px; border-top: 1px solid #ddd; padding-top: 4px;">
                <i class="fas fa-info-circle"></i> Real-time vessel updates every 30s
            </div>
        `;
        return div;
    };
    
    legend.addTo(maritimeMap);
}

/**
 * Clear all route layers from map
 */
function clearAllRouteLayers() {
    if (!maritimeMap) return;
    
    // Remove all polylines
    routePolylines.forEach(polyline => {
        maritimeMap.removeLayer(polyline);
    });
    routePolylines = [];
    
    // Remove all markers
    routeMarkers.forEach(markerGroup => {
        if (markerGroup.start) maritimeMap.removeLayer(markerGroup.start);
        if (markerGroup.end) maritimeMap.removeLayer(markerGroup.end);
    });
    routeMarkers = [];
    
    console.log('🗑️ Cleared all route layers from map');
}

/**
 * Update route counters in UI
 */
function updateRouteCounters() {
    // Update route count display
    const routeCountElement = document.getElementById('route-count');
    const routeCountBadge = document.getElementById('route-count-badge');
    const waypointCountElement = document.getElementById('waypoint-count');
    
    if (routeCountElement) {
        routeCountElement.textContent = activeRoutes.length;
    }
    
    if (routeCountBadge) {
        routeCountBadge.textContent = activeRoutes.length;
    }
    
    // Calculate total waypoints
    let totalWaypoints = 0;
    activeRoutes.forEach(route => {
        if (route.waypoints && Array.isArray(route.waypoints)) {
            totalWaypoints += route.waypoints.length;
        } else if (route.waypoint_count) {
            totalWaypoints += route.waypoint_count;
        }
    });
    
    if (waypointCountElement) {
        waypointCountElement.textContent = totalWaypoints;
    }
    
    console.log(`📊 Updated counters: ${activeRoutes.length} routes, ${totalWaypoints} waypoints`);
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const types = {
        'info': { class: 'alert-info', icon: 'ℹ️' },
        'success': { class: 'alert-success', icon: '✅' },
        'warning': { class: 'alert-warning', icon: '⚠️' },
        'error': { class: 'alert-danger', icon: '❌' }
    };
    
    const config = types[type] || types.info;
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert ${config.class} alert-dismissible fade show`;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        max-width: 300px;
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <strong>${config.icon} ${type.charAt(0).toUpperCase() + type.slice(1)}:</strong>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// ============================================
// REAL-TIME VESSEL TRACKING FUNCTIONS
// ============================================

/**
 * Fetch and display a real-time vessel
 */
function updateRealTimeVessel() {
    console.log('🚢 Fetching real-time vessel...');
    
    fetch('/maritime/api/vessels/real-time?city=bergen&radius_km=20')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`📡 Vessel data: ${data.status} from ${data.source}`);
            
            if (data.vessel) {
                displaySingleVesselOnMap(data.vessel, data.is_empirical);
                
                // Update UI counter
                updateVesselCounter(data.is_empirical ? 'real' : 'fallback');
                
                // Show notification for first successful load
                if (!window.vesselLoaded) {
                    const sourceText = data.is_empirical ? 
                        `Real-time from ${data.source}` : 
                        'Empirical fallback (API offline)';
                    showNotification(`Tracking vessel: ${data.vessel.name} (${sourceText})`, 'info');
                    window.vesselLoaded = true;
                }
            }
        })
        .catch(error => {
            console.error('❌ Error fetching real-time vessel:', error);
            // Silent fail - try again next interval
        });
}

/**
 * Display a single vessel on the map
 */
function displaySingleVesselOnMap(vessel, isEmpirical = false) {
    if (!maritimeMap) return;
    
    // Remove previous marker
    if (realTimeVesselMarker) {
        maritimeMap.removeLayer(realTimeVesselMarker);
    }
    
    const lat = vessel.lat || vessel.latitude;
    const lon = vessel.lon || vessel.longitude;
    
    if (!lat || !lon) {
        console.warn('Invalid vessel coordinates:', vessel);
        return;
    }
    
    // Choose color based on data source
    const color = isEmpirical ? '#28a745' : '#ffc107';  // Green for real, Yellow for fallback
    const iconClass = isEmpirical ? 'vessel-live-pulse' : 'vessel-fallback';
    
    // Create custom vessel icon
    const vesselIcon = L.divIcon({
        className: `real-time-vessel-marker ${iconClass}`,
        html: `
            <div style="
                background: ${color};
                width: 20px;
                height: 20px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                position: relative;
            ">
                <div style="
                    position: absolute;
                    top: -8px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 10px;
                    color: white;
                    background: rgba(0,0,0,0.6);
                    padding: 1px 3px;
                    border-radius: 3px;
                    white-space: nowrap;
                ">
                    ${isEmpirical ? '🚢 LIVE' : '📡 SIM'}
                </div>
            </div>
        `,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
    
    // Create marker
    realTimeVesselMarker = L.marker([lat, lon], {
        icon: vesselIcon,
        zIndexOffset: 1000,  // Bring to front
        title: vessel.name || 'Vessel'
    }).addTo(maritimeMap);
    
    // Create popup content
    const popupContent = createVesselPopup(vessel, isEmpirical);
    realTimeVesselMarker.bindPopup(popupContent);
    
    // Add tooltip
    realTimeVesselMarker.bindTooltip(`
        <b>${vessel.name || 'Unknown Vessel'}</b><br>
        ${isEmpirical ? '🚢 Real-time' : '📡 Empirical Fallback'}
    `);
    
    console.log(`📍 Vessel displayed: ${vessel.name} at ${lat.toFixed(4)}, ${lon.toFixed(4)}`);
}

/**
 * Create vessel popup HTML
 */
function createVesselPopup(vessel, isEmpirical) {
    const timestamp = vessel.timestamp ? new Date(vessel.timestamp).toLocaleTimeString() : 'Unknown';
    const speed = vessel.speed || vessel.speed_knots || vessel.sog || 0;
    const course = vessel.course || 0;
    const type = vessel.type || 'Unknown';
    const mmsi = vessel.mmsi || 'Unknown';
    
    return `
        <div style="min-width: 250px;">
            <div style="background: ${isEmpirical ? '#28a745' : '#ffc107'}; color: white; padding: 10px; border-radius: 5px 5px 0 0;">
                <i class="fas fa-ship"></i> ${vessel.name || 'Unknown Vessel'}
                <span style="float: right; font-size: 0.8em;">
                    ${isEmpirical ? '🚢 LIVE' : '📡 SIM'}
                </span>
            </div>
            <div style="padding: 10px; background: white;">
                <table style="width: 100%; font-size: 12px;">
                    <tr>
                        <td><strong>Type:</strong></td>
                        <td>${type}</td>
                    </tr>
                    <tr>
                        <td><strong>Speed:</strong></td>
                        <td>${speed.toFixed(1)} knots</td>
                    </tr>
                    <tr>
                        <td><strong>Course:</strong></td>
                        <td>${course.toFixed(0)}°</td>
                    </tr>
                    <tr>
                        <td><strong>MMSI:</strong></td>
                        <td>${mmsi}</td>
                    </tr>
                    <tr>
                        <td><strong>Source:</strong></td>
                        <td>${vessel.data_source || 'Unknown'}</td>
                    </tr>
                    <tr>
                        <td><strong>Updated:</strong></td>
                        <td>${timestamp}</td>
                    </tr>
                    ${vessel.destination ? `
                    <tr>
                        <td><strong>Destination:</strong></td>
                        <td>${vessel.destination}</td>
                    </tr>
                    ` : ''}
                </table>
                <div style="margin-top: 10px; font-size: 11px; color: #666; border-top: 1px solid #eee; padding-top: 5px;">
                    <i class="fas fa-info-circle"></i>
                    ${isEmpirical ? 
                        'Real-time position from Norwegian AIS data' : 
                        'Empirical simulation - real-time data currently unavailable'
                    }
                </div>
            </div>
        </div>
    `;
}

/**
 * Update vessel counter in UI
 */
function updateVesselCounter(sourceType) {
    const counterElement = document.getElementById('real-time-vessel-counter');
    if (!counterElement) return;
    
    counterElement.textContent = sourceType === 'real' ? '🚢 LIVE' : '📡 SIM';
    counterElement.title = sourceType === 'real' ? 'Real-time vessel tracking' : 'Empirical simulation (API offline)';
    
    // Update color
    counterElement.style.color = sourceType === 'real' ? '#28a745' : '#ffc107';
    counterElement.style.fontWeight = 'bold';
    
    // Update source text
    const sourceElement = document.getElementById('vessel-source');
    if (sourceElement) {
        sourceElement.textContent = sourceType === 'real' ? 'Real-time tracking' : 'Empirical simulation';
    }
    
    // Update time
    const timeElement = document.getElementById('vessel-update-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = `Updated: ${now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    }
}

/**
 * Start real-time vessel tracking
 */
function startVesselTracking(intervalSeconds = 30) {
    if (vesselUpdateInterval) {
        clearInterval(vesselUpdateInterval);
    }
    
    vesselTrackingActive = true;
    
    // Initial load
    updateRealTimeVessel();
    
    // Set up interval
    vesselUpdateInterval = setInterval(updateRealTimeVessel, intervalSeconds * 1000);
    
    console.log(`🚢 Vessel tracking started (${intervalSeconds}s interval)`);
}

/**
 * Stop real-time vessel tracking
 */
function stopVesselTracking() {
    vesselTrackingActive = false;
    
    if (vesselUpdateInterval) {
        clearInterval(vesselUpdateInterval);
        vesselUpdateInterval = null;
    }
    
    if (realTimeVesselMarker) {
        maritimeMap.removeLayer(realTimeVesselMarker);
        realTimeVesselMarker = null;
    }
    
    console.log('🚢 Vessel tracking stopped');
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize everything when page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌊 Maritime Map Module: DOM loaded, starting initialization...');
    
    // Initialize map immediately
    initMaritimeMap();
    
    // Load and display routes after short delay (let map initialize)
    setTimeout(() => {
        loadAndDisplayRTZRoutes();
    }, 500);
    
    // Add click handlers for route table buttons
    setTimeout(() => {
        addRouteTableEventListeners();
    }, 1500); // Give more time for routes to load
    
    // Make functions available globally
    window.loadRTZRoutes = loadAndDisplayRTZRoutes;
    window.initMaritimeMap = initMaritimeMap;
    window.showNotification = showNotification;
    window.startVesselTracking = startVesselTracking;
    window.stopVesselTracking = stopVesselTracking;
    window.updateRealTimeVessel = updateRealTimeVessel;
    
    console.log('✅ Maritime Map Module ready');
});

/**
 * Add event listeners to route table buttons
 */
function addRouteTableEventListeners() {
    console.log('🔗 Adding event listeners to route table buttons...');
    
    // Handle View Route buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.view-route-btn')) {
            const button = e.target.closest('.view-route-btn');
            const routeId = button.dataset.routeId;
            
            console.log(`🔍 View route button clicked: ${routeId}`, button);
            
            if (routeId) {
                // First try to find route by index (row number)
                const row = button.closest('tr');
                if (row) {
                    // Get all rows in the table body (excluding header)
                    const rows = Array.from(row.parentNode.querySelectorAll('tr:not(:first-child)'));
                    const rowIndex = rows.indexOf(row);
                    
                    if (rowIndex !== -1) {
                        console.log(`🔄 Found route at row index: ${rowIndex}`);
                        const success = window.zoomToRoute(rowIndex);
                        if (success) {
                            // Highlight the row
                            document.querySelectorAll('.route-row-highlighted').forEach(r => {
                                r.classList.remove('route-row-highlighted');
                            });
                            row.classList.add('route-row-highlighted');
                            return;
                        }
                    }
                }
                
                // If row index didn't work, try the routeId directly
                const success = window.zoomToRoute(routeId);
                if (!success) {
                    showNotification('Could not find the route on the map', 'error');
                } else {
                    // Highlight the row
                    const row = button.closest('tr');
                    if (row) {
                        document.querySelectorAll('.route-row-highlighted').forEach(r => {
                            r.classList.remove('route-row-highlighted');
                        });
                        row.classList.add('route-row-highlighted');
                    }
                }
            }
        }
    });
    
    // Handle Highlight Route buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.highlight-route-btn')) {
            const button = e.target.closest('.highlight-route-btn');
            const routeId = button.dataset.routeId;
            
            console.log(`🔦 Highlight route button clicked: ${routeId}`);
            
            if (routeId) {
                // Find route by row index first
                const row = button.closest('tr');
                if (row) {
                    const rows = Array.from(row.parentNode.querySelectorAll('tr:not(:first-child)'));
                    const rowIndex = rows.indexOf(row);
                    
                    if (rowIndex !== -1) {
                        window.highlightRoute(rowIndex);
                        return;
                    }
                }
                
                // Try to find by ID
                const routeIndex = activeRoutes.findIndex(r => 
                    (r.route_id && r.route_id.toString() === routeId) ||
                    (r.id && r.id.toString() === routeId)
                );
                
                if (routeIndex !== -1) {
                    window.highlightRoute(routeIndex);
                }
            }
        }
    });
}

// Add some CSS for the routes and animations - FIXED: No blinking waypoints
const routeStyles = document.createElement('style');
routeStyles.textContent = `
    .rtz-route-line {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .route-start-marker {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .route-end-marker {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .leaflet-control-legend {
        background: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 1px 5px rgba(0,0,0,0.4);
        font-size: 12px;
    }
    .legend-title {
        font-weight: bold;
        margin-bottom: 8px;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin: 4px 0;
    }
    .legend-color {
        width: 15px;
        height: 15px;
        border-radius: 3px;
        margin-right: 8px;
    }
    .legend-label {
        font-size: 11px;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .route-highlighted {
        animation: pulse 1s infinite;
        filter: drop-shadow(0 0 5px rgba(255, 87, 34, 0.7));
    }
    
    /* Real-time vessel marker styles */
    .real-time-vessel-marker {
        cursor: pointer;
        animation: none !important; /* Prevent blinking */
    }
    
    .real-time-vessel-marker:hover {
        filter: brightness(1.2);
        transform: scale(1.1);
        transition: all 0.2s ease;
    }
    
    /* Pulse animation for live vessel */
    @keyframes live-pulse {
        0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
    }
    
    .vessel-live-pulse {
        animation: live-pulse 2s infinite !important;
    }
    
    /* Fallback vessel style */
    .vessel-fallback {
        opacity: 0.8;
    }
    
    /* Waypoint marker styles - FIXED: NO BLINKING */
    .rtz-waypoint-marker {
        cursor: pointer;
        transition: all 0.2s ease;
        animation: none !important; /* FIX: Stop all animations */
        -webkit-animation: none !important; /* Safari/Chrome */
    }
    
    .rtz-waypoint-marker:hover {
        fill-opacity: 0.9;
        stroke-width: 3;
        transform: scale(1.1);
    }
    
    /* Additional fix for all waypoint markers */
    .leaflet-marker-icon[class*="waypoint"],
    .leaflet-marker-icon[class*="rtz"],
    .waypoint-marker {
        animation: none !important;
        -webkit-animation: none !important;
    }
    
    /* Fix for any parent elements that might cause blinking */
    .leaflet-marker-pane *,
    .leaflet-overlay-pane * {
        animation: none !important;
    }
    
    /* Vessel status indicator */
    #real-time-vessel-counter {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.9rem;
        margin-left: 10px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Route table row highlighting */
    .route-row-highlighted {
        background-color: rgba(52, 152, 219, 0.15) !important;
        border-left: 3px solid #3498db !important;
    }
`;
document.head.appendChild(routeStyles);