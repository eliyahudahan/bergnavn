/**
 * Maritime Map Module for BergNavn Dashboard
 * Version: 3.0.0 - Enhanced Real-time Vessel System
 * Features:
 * 1. Real-time vessel tracking FIRST
 * 2. Empirical fallback SECOND (only if real-time fails)
 * 3. Optimized performance - no code bloat
 * 4. All original functions preserved
 */

// Global map variables
let maritimeMap = null;
let vesselMarkers = [];
let activeRoutes = [];
let routePolylines = [];
let routeMarkers = [];

// Enhanced real-time vessel tracking
let realTimeVesselMarker = null;
let vesselUpdateInterval = null;
let vesselTrackingActive = false;
let realTimeRetryCount = 0;
const MAX_RETRIES = 3;
const RETRY_DELAY = 5000; // 5 seconds

// Store route counts per port
let portRouteCounts = {};

// Empirical fallback vessel data - based on real Norwegian vessel patterns
const EMPIRICAL_VESSELS = [
    {
        id: 'empirical_bergen_1',
        name: 'MS Bergen',
        type: 'Passenger Ferry',
        mmsi: '259257000',
        lat: 60.3913,
        lon: 5.3221,
        speed: 15.5,
        heading: 320,
        destination: 'Bergen',
        status: 'Underway',
        data_source: 'empirical_fallback_bergen',
        color: '#3498db'
    },
    {
        id: 'empirical_bergen_2',
        name: 'F/B Nord 4',
        type: 'Fast Ferry',
        mmsi: '259248000',
        lat: 60.4045,
        lon: 5.3571,
        speed: 22.0,
        heading: 45,
        destination: 'Bergen',
        status: 'Underway',
        data_source: 'empirical_fallback_bergen',
        color: '#e74c3c'
    },
    {
        id: 'empirical_stad_1',
        name: 'MV Stad',
        type: 'Cargo Ship',
        mmsi: '259179000',
        lat: 62.1,
        lon: 5.1,
        speed: 12.0,
        heading: 180,
        destination: 'Ålesund',
        status: 'Underway',
        data_source: 'empirical_fallback_stad',
        color: '#f39c12'
    }
];

// Make zoom functions available globally with enhanced error handling
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
            if (r.route_id && r.route_id.toString() === routeIdentifier) return true;
            if (r.id && r.id.toString() === routeIdentifier) return true;
            if (r.routeId && r.routeId.toString() === routeIdentifier) return true;
            
            const routeName = r.clean_name || r.route_name || '';
            if (routeName.toLowerCase().includes(routeIdentifier.toLowerCase())) return true;
            
            return false;
        });
        
        if (routeIndex !== -1) {
            route = activeRoutes[routeIndex];
        } else {
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
        highlightRoute(routeIndex);
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
 * Highlight a specific route
 */
window.highlightRoute = function(routeIndex) {
    if (!maritimeMap || !activeRoutes[routeIndex]) return;
    
    // Reset all routes
    routePolylines.forEach(polyline => {
        polyline.setStyle({ weight: 4, opacity: 0.8 });
    });
    
    const route = activeRoutes[routeIndex];
    if (route.mapPolyline) {
        route.mapPolyline.setStyle({ 
            weight: 8, 
            opacity: 1.0,
            color: '#ff5722'
        });
        route.mapPolyline.bringToFront();
        console.log(`🔦 Highlighted route ${routeIndex}: ${route.clean_name || route.route_name}`);
    }
};

// ============================================
// MAP INITIALIZATION
// ============================================

/**
 * Initialize the maritime map
 */
function initMaritimeMap() {
    console.log('🌊 Maritime Map v3.0.0 initializing...');
    
    const mapElement = document.getElementById('maritime-map');
    if (!mapElement) {
        console.error('❌ Map container not found');
        return null;
    }
    
    if (!maritimeMap) {
        maritimeMap = L.map('maritime-map').setView([64.0, 10.0], 6);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(maritimeMap);
        
        L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
            attribution: '© OpenSeaMap',
            opacity: 0.4,
            maxZoom: 18,
        }).addTo(maritimeMap);
        
        console.log('✅ Maritime map created');
        window.map = maritimeMap;
    }
    
    return maritimeMap;
}

// ============================================
// ROUTE MANAGEMENT
// ============================================

/**
 * Load and display RTZ routes
 */
function loadAndDisplayRTZRoutes() {
    console.log('🗺️ Loading RTZ routes...');
    clearAllRouteLayers();
    
    fetch('/maritime/api/rtz/complete')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.routes && Array.isArray(data.routes) && data.routes.length > 0) {
                console.log(`✅ Loaded ${data.routes.length} routes from API`);
                activeRoutes = data.routes;
                
                countRoutesByPort();
                updatePortCounters();
                window.routesData = activeRoutes;
                window.allRoutesData = activeRoutes;
                displayRoutesOnMap();
                updateRouteCounters();
                
                // Dispatch event for waypoints module
                document.dispatchEvent(new CustomEvent('routesDataLoaded', {
                    detail: {
                        routes: activeRoutes,
                        source: 'maritime_map.js',
                        timestamp: new Date().toISOString(),
                        totalRoutes: activeRoutes.length,
                        routesWithWaypoints: activeRoutes.filter(r => r.waypoints && r.waypoints.length > 0).length,
                        hasWaypointsData: true
                    }
                }));
                
                showNotification(`Loaded ${activeRoutes.length} RTZ routes`, 'success');
                
                // Start enhanced vessel tracking
                setTimeout(() => {
                    startEnhancedVesselTracking();
                }, 2000);
                
                return activeRoutes;
            } else {
                console.warn('⚠️ API returned no routes, trying template data');
                return loadRoutesFromTemplate();
            }
        })
        .catch(error => {
            console.error('❌ Error loading from API:', error);
            return loadRoutesFromTemplate();
        });
}

/**
 * Count routes by port
 */
function countRoutesByPort() {
    portRouteCounts = {};
    activeRoutes.forEach(route => {
        const port = (route.source_city || '').toLowerCase().replace('å', 'a').replace('Å', 'a');
        if (port) {
            portRouteCounts[port] = (portRouteCounts[port] || 0) + 1;
        }
    });
    console.log('📊 Route counts by port:', portRouteCounts);
}

/**
 * Update port counters in UI
 */
function updatePortCounters() {
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
    
    Object.keys(portDisplayNames).forEach(portKey => {
        const count = portRouteCounts[portKey] || 0;
        const badges = document.querySelectorAll(`.city-badge[data-port="${portKey}"]`);
        badges.forEach(badge => {
            const countSpan = badge.querySelector('.port-count');
            if (countSpan) countSpan.textContent = count;
        });
    });
    console.log('✅ Updated port counters');
}

/**
 * Fallback: Load routes from template
 */
function loadRoutesFromTemplate() {
    try {
        const routesDataElement = document.getElementById('routes-data');
        if (!routesDataElement || !routesDataElement.textContent) {
            console.error('❌ No routes data found');
            return [];
        }
        
        activeRoutes = JSON.parse(routesDataElement.textContent);
        console.log(`✅ Found ${activeRoutes.length} routes in HTML`);
        
        countRoutesByPort();
        updatePortCounters();
        window.routesData = activeRoutes;
        window.allRoutesData = activeRoutes;
        updateRouteCounters();
        
        if (activeRoutes.length > 0) {
            document.dispatchEvent(new CustomEvent('routesDataLoaded', {
                detail: {
                    routes: activeRoutes,
                    source: 'template_data',
                    timestamp: new Date().toISOString(),
                    totalRoutes: activeRoutes.length,
                    routesWithWaypoints: 0,
                    hasWaypointsData: false
                }
            }));
        }
        
        setTimeout(() => {
            startEnhancedVesselTracking();
        }, 2000);
        
        showNotification(`Loaded ${activeRoutes.length} routes (template data)`, 'warning');
        return activeRoutes;
    } catch (error) {
        console.error('❌ Error loading routes from template:', error);
        return [];
    }
}

/**
 * Display routes on map
 */
function displayRoutesOnMap() {
    if (!maritimeMap) {
        console.error('❌ No map available');
        return;
    }
    
    if (!activeRoutes.length) {
        console.warn('⚠️ No routes to display');
        return;
    }
    
    console.log(`🗺️ Displaying ${activeRoutes.length} routes...`);
    clearAllRouteLayers();
    
    let displayedCount = 0;
    activeRoutes.forEach((route, index) => {
        try {
            if (displaySingleRoute(route, index)) displayedCount++;
        } catch (error) {
            console.error(`❌ Error displaying route ${index}:`, error);
        }
    });
    
    console.log(`✅ Displayed ${displayedCount} routes`);
    if (displayedCount > 0) fitMapToRoutes();
    addMapLegend();
}

/**
 * Display single route
 */
function displaySingleRoute(route, index) {
    if (!maritimeMap) return false;
    
    const waypoints = extractWaypointsFromRoute(route);
    if (waypoints.length < 2) {
        console.warn(`Route ${index} has insufficient waypoints: ${waypoints.length}`);
        return false;
    }
    
    const colors = {
        'bergen': '#1e88e5', 'oslo': '#43a047', 'stavanger': '#f39c12',
        'trondheim': '#e74c3c', 'alesund': '#9b59b6', 'andalsnes': '#3498db',
        'kristiansand': '#2ecc71', 'drammen': '#e67e22', 'sandefjord': '#16a085',
        'flekkefjord': '#8e44ad'
    };
    
    const port = (route.source_city || '').toLowerCase();
    const color = colors[port] || '#1e88e5';
    const coordinates = waypoints.map(wp => [wp.lat, wp.lon]);
    
    const polyline = L.polyline(coordinates, {
        color: color,
        weight: 4,
        opacity: 0.8,
        lineCap: 'round',
        lineJoin: 'round',
        className: 'rtz-route-line'
    }).addTo(maritimeMap);
    
    routePolylines.push(polyline);
    
    const startMarker = L.circleMarker(coordinates[0], {
        color: '#28a745',
        fillColor: '#28a745',
        fillOpacity: 1.0,
        radius: 8,
        weight: 3,
        className: 'route-start-marker'
    }).addTo(maritimeMap).bindTooltip(`<b>Start:</b> ${route.origin || 'Unknown'}`);
    
    const endMarker = L.circleMarker(coordinates[coordinates.length - 1], {
        color: '#dc3545',
        fillColor: '#dc3545',
        fillOpacity: 1.0,
        radius: 8,
        weight: 3,
        className: 'route-end-marker'
    }).addTo(maritimeMap).bindTooltip(`<b>End:</b> ${route.destination || 'Unknown'}`);
    
    routeMarkers.push({ start: startMarker, end: endMarker, routeIndex: index });
    
    const popupContent = createRoutePopup(route, index, color);
    polyline.bindPopup(popupContent);
    startMarker.bindPopup(popupContent);
    endMarker.bindPopup(popupContent);
    
    polyline.on('mouseover', function() {
        this.setStyle({ weight: 6, opacity: 1.0 });
        startMarker.setStyle({ radius: 10 });
        endMarker.setStyle({ radius: 10 });
    }).on('mouseout', function() {
        this.setStyle({ weight: 4, opacity: 0.8 });
        startMarker.setStyle({ radius: 8 });
        endMarker.setStyle({ radius: 8 });
    }).on('click', function() {
        zoomToRoute(index);
    });
    
    route.routeElementId = route.route_id || `route_${index}`;
    route.mapPolyline = polyline;
    
    console.log(`✅ Added route ${index}: ${route.clean_name || route.route_name}`);
    return true;
}

/**
 * Extract waypoints from route
 */
function extractWaypointsFromRoute(route) {
    let waypoints = [];
    
    // Format 1: Direct waypoints array
    if (route.waypoints && Array.isArray(route.waypoints)) {
        waypoints = route.waypoints.map((wp, i) => {
            if (wp && typeof wp === 'object') {
                return {
                    lat: wp.lat || wp[1],
                    lon: wp.lon || wp[0],
                    name: wp.name || `WP${i + 1}`
                };
            } else if (Array.isArray(wp) && wp.length >= 2) {
                return {
                    lat: wp[1],
                    lon: wp[0],
                    name: `WP${i + 1}`
                };
            }
            return null;
        }).filter(wp => wp !== null);
    }
    // Format 2: Geometry coordinates
    else if (route.geometry && route.geometry.coordinates) {
        waypoints = route.geometry.coordinates.map((coord, i) => ({
            lat: coord[1],
            lon: coord[0],
            name: `WP${i + 1}`
        }));
    }
    // Format 3: Path array
    else if (route.path && Array.isArray(route.path)) {
        waypoints = route.path.map((coord, i) => ({
            lat: coord[1] || coord.lat,
            lon: coord[0] || coord.lon,
            name: `WP${i + 1}`
        }));
    }
    
    // Filter valid coordinates (Norway range)
    return waypoints.filter(wp => {
        return wp && wp.lat && wp.lon && 
               !isNaN(wp.lat) && !isNaN(wp.lon) &&
               wp.lat >= 55 && wp.lat <= 72 &&
               wp.lon >= 0 && wp.lon <= 32;
    });
}

/**
 * Create route popup
 */
function createRoutePopup(route, index, color) {
    const routeName = route.clean_name || 
                     (route.route_name ? route.route_name
                         .replace('NCA_', '')
                         .replace('_2025', '')
                         .replace('_2024', '')
                         .replace(/_/g, ' ') : 
                      `Route ${index + 1}`);
    
    const distance = route.total_distance_nm ? 
                    `${route.total_distance_nm.toFixed(1)} NM` : 'Unknown';
    
    const waypointCount = route.waypoints ? route.waypoints.length : 
                         (route.waypoint_count || 'Unknown');
    
    return `
        <div style="min-width: 250px;">
            <div style="background: ${color}; color: white; padding: 10px; border-radius: 5px 5px 0 0;">
                <i class="fas fa-route"></i> ${routeName}
            </div>
            <div style="padding: 10px; background: white;">
                <table style="width: 100%; font-size: 12px;">
                    <tr><td><strong>Origin:</strong></td><td style="color: #28a745;">${route.origin || 'Unknown'}</td></tr>
                    <tr><td><strong>Destination:</strong></td><td style="color: #dc3545;">${route.destination || 'Unknown'}</td></tr>
                    <tr><td><strong>Distance:</strong></td><td>${distance}</td></tr>
                    <tr><td><strong>Waypoints:</strong></td><td>${waypointCount}</td></tr>
                    <tr><td><strong>Port:</strong></td><td>${route.source_city || 'Unknown'}</td></tr>
                </table>
                <div style="margin-top: 10px; display: flex; gap: 5px;">
                    <button onclick="zoomToRoute(${index})"
                            style="background: ${color}; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;">
                        <i class="fas fa-search-plus"></i> Zoom
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
 * Fit map to routes
 */
function fitMapToRoutes() {
    if (!maritimeMap || routePolylines.length === 0) return;
    
    const bounds = L.latLngBounds();
    routePolylines.forEach(polyline => {
        if (polyline.getBounds) bounds.extend(polyline.getBounds());
    });
    
    if (bounds.isValid()) {
        maritimeMap.fitBounds(bounds.pad(0.1));
        console.log('🗺️ Map fitted to routes');
    }
}

/**
 * Add map legend
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
                <div class="legend-color" style="background-color: #28a745;"></div>
                <div class="legend-label"><i class="fas fa-ship"></i> Real-time Vessel (LIVE)</div>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ffc107;"></div>
                <div class="legend-label"><i class="fas fa-ship"></i> Empirical Vessel (Fallback)</div>
            </div>
            <div style="font-size: 10px; color: #666; margin-top: 8px; border-top: 1px solid #ddd; padding-top: 4px;">
                <i class="fas fa-info-circle"></i> Real-time first, fallback if needed
            </div>
        `;
        return div;
    };
    
    legend.addTo(maritimeMap);
}

/**
 * Clear all route layers
 */
function clearAllRouteLayers() {
    if (!maritimeMap) return;
    
    routePolylines.forEach(polyline => maritimeMap.removeLayer(polyline));
    routePolylines = [];
    
    routeMarkers.forEach(markerGroup => {
        if (markerGroup.start) maritimeMap.removeLayer(markerGroup.start);
        if (markerGroup.end) maritimeMap.removeLayer(markerGroup.end);
    });
    routeMarkers = [];
    
    console.log('🗑️ Cleared all route layers');
}

/**
 * Update route counters
 */
function updateRouteCounters() {
    const routeCountElement = document.getElementById('route-count');
    const routeCountBadge = document.getElementById('route-count-badge');
    const waypointCountElement = document.getElementById('waypoint-count');
    
    if (routeCountElement) routeCountElement.textContent = activeRoutes.length;
    if (routeCountBadge) routeCountBadge.textContent = activeRoutes.length;
    
    let totalWaypoints = 0;
    activeRoutes.forEach(route => {
        if (route.waypoints && Array.isArray(route.waypoints)) {
            totalWaypoints += route.waypoints.length;
        } else if (route.waypoint_count) {
            totalWaypoints += route.waypoint_count;
        }
    });
    
    if (waypointCountElement) waypointCountElement.textContent = totalWaypoints;
    console.log(`📊 Counters: ${activeRoutes.length} routes, ${totalWaypoints} waypoints`);
}

// ============================================
// ENHANCED REAL-TIME VESSEL SYSTEM
// ============================================

/**
 * Enhanced vessel tracking: REAL-TIME FIRST, EMPIRICAL FALLBACK SECOND
 */
function startEnhancedVesselTracking(intervalSeconds = 30) {
    console.log('🚢 Starting ENHANCED vessel tracking...');
    
    if (vesselUpdateInterval) clearInterval(vesselUpdateInterval);
    vesselTrackingActive = true;
    realTimeRetryCount = 0;
    
    // Initial load with retry logic
    fetchVesselWithRetry();
    
    // Set up interval
    vesselUpdateInterval = setInterval(fetchVesselWithRetry, intervalSeconds * 1000);
    console.log(`✅ Enhanced vessel tracking started (${intervalSeconds}s interval)`);
}

/**
 * Fetch vessel with retry logic: Try real-time 3 times, then fallback
 */
async function fetchVesselWithRetry() {
    console.log(`🚢 Vessel fetch attempt ${realTimeRetryCount + 1}/${MAX_RETRIES}`);
    
    try {
        // STEP 1: Try real-time API FIRST
        const response = await fetch('/maritime/api/vessels/real-time?city=bergen&radius_km=50');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        console.log(`📡 Real-time data received: ${data.status} from ${data.source}`);
        
        if (data.vessel) {
            // SUCCESS: Real-time vessel found
            realTimeRetryCount = 0; // Reset retry counter
            displayEnhancedVessel(data.vessel, false); // false = real-time
            updateVesselCounter('real', data.vessel.name);
            return;
        } else {
            // No vessel in real-time data
            console.log('⚠️ Real-time API returned no vessel data');
            throw new Error('No vessel data');
        }
    } catch (error) {
        // STEP 2: Real-time failed, try again or use fallback
        realTimeRetryCount++;
        console.warn(`❌ Real-time fetch failed (attempt ${realTimeRetryCount}):`, error.message);
        
        if (realTimeRetryCount >= MAX_RETRIES) {
            // STEP 3: Use empirical fallback after max retries
            console.log('🆘 Max retries reached, using empirical fallback');
            useEmpiricalFallback();
        } else {
            // Try again next interval
            console.log(`🔄 Will retry real-time in next interval`);
        }
    }
}

/**
 * Use empirical fallback vessel data
 */
function useEmpiricalFallback() {
    console.log('📊 Using empirical fallback vessel data');
    
    // Select random empirical vessel
    const empiricalVessel = EMPIRICAL_VESSELS[Math.floor(Math.random() * EMPIRICAL_VESSELS.length)];
    const enhancedVessel = {
        ...empiricalVessel,
        timestamp: new Date().toISOString(),
        data_source: 'empirical_fallback',
        is_empirical: true
    };
    
    displayEnhancedVessel(enhancedVessel, true); // true = fallback
    updateVesselCounter('fallback', empiricalVessel.name);
    
    // Schedule attempt to return to real-time after 2 minutes
    setTimeout(() => {
        if (vesselTrackingActive) {
            console.log('🔄 Attempting to return to real-time after fallback...');
            realTimeRetryCount = 0;
            fetchVesselWithRetry();
        }
    }, 120000); // 2 minutes
}

/**
 * Enhanced vessel display with better visuals
 */
function displayEnhancedVessel(vessel, isFallback = false) {
    if (!maritimeMap) return;
    
    // Remove previous marker
    if (realTimeVesselMarker) {
        maritimeMap.removeLayer(realTimeVesselMarker);
    }
    
    const lat = vessel.lat || vessel.latitude;
    const lon = vessel.lon || vessel.longitude;
    
    if (!lat || !lon) {
        console.warn('Invalid vessel coordinates');
        return;
    }
    
    // Choose color and style based on source
    const color = isFallback ? '#ffc107' : '#28a745';
    const iconClass = isFallback ? 'vessel-fallback' : 'vessel-real-time';
    const pulseClass = isFallback ? '' : 'vessel-pulse-animation';
    
    // Create enhanced vessel icon
    const vesselIcon = L.divIcon({
        className: `vessel-marker ${iconClass} ${pulseClass}`,
        html: `
            <div style="
                background: ${color};
                width: ${isFallback ? '22px' : '24px'};
                height: ${isFallback ? '22px' : '24px'};
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                position: relative;
                ${isFallback ? 'opacity: 0.9;' : ''}
            ">
                <div style="
                    position: absolute;
                    top: -10px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 9px;
                    color: white;
                    background: rgba(0,0,0,0.7);
                    padding: 2px 4px;
                    border-radius: 3px;
                    white-space: nowrap;
                    font-weight: bold;
                ">
                    ${isFallback ? '📡 FALLBACK' : '🚢 LIVE'}
                </div>
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: white;
                    font-size: 10px;
                ">
                    <i class="fas fa-ship"></i>
                </div>
            </div>
        `,
        iconSize: isFallback ? [22, 22] : [24, 24],
        iconAnchor: isFallback ? [11, 11] : [12, 12]
    });
    
    // Create marker
    realTimeVesselMarker = L.marker([lat, lon], {
        icon: vesselIcon,
        zIndexOffset: 1000,
        title: vessel.name
    }).addTo(maritimeMap);
    
    // Create enhanced popup
    const popupContent = createEnhancedVesselPopup(vessel, isFallback);
    realTimeVesselMarker.bindPopup(popupContent);
    
    realTimeVesselMarker.bindTooltip(`
        <b>${vessel.name}</b><br>
        <small>${isFallback ? '📡 Empirical Data' : '🚢 Real-time'}</small>
    `);
    
    console.log(`📍 ${isFallback ? 'Fallback' : 'Real-time'} vessel: ${vessel.name} at ${lat.toFixed(4)}, ${lon.toFixed(4)}`);
}

/**
 * Create enhanced vessel popup
 */
function createEnhancedVesselPopup(vessel, isFallback) {
    const timestamp = vessel.timestamp ? new Date(vessel.timestamp).toLocaleTimeString() : 'Unknown';
    const speed = vessel.speed || vessel.speed_knots || vessel.sog || 0;
    const course = vessel.course || 0;
    
    return `
        <div style="min-width: 260px;">
            <div style="background: ${isFallback ? '#ffc107' : '#28a745'}; 
                        color: white; padding: 10px; border-radius: 5px 5px 0 0;">
                <div style="display: flex; align-items: center;">
                    <i class="fas fa-ship" style="font-size: 16px; margin-right: 8px;"></i>
                    <span style="font-weight: bold;">${vessel.name || 'Unknown Vessel'}</span>
                    <span style="margin-left: auto; font-size: 11px; background: rgba(255,255,255,0.2); 
                                padding: 2px 6px; border-radius: 10px;">
                        ${isFallback ? '📡 FALLBACK' : '🚢 LIVE'}
                    </span>
                </div>
            </div>
            <div style="padding: 12px; background: white;">
                <table style="width: 100%; font-size: 13px; border-spacing: 0 6px;">
                    <tr>
                        <td style="padding-right: 10px; font-weight: 600; color: #555;">Type:</td>
                        <td>${vessel.type || 'Unknown'}</td>
                    </tr>
                    <tr>
                        <td style="padding-right: 10px; font-weight: 600; color: #555;">Speed:</td>
                        <td><span style="color: #3498db;">${speed.toFixed(1)}</span> knots</td>
                    </tr>
                    <tr>
                        <td style="padding-right: 10px; font-weight: 600; color: #555;">Course:</td>
                        <td>${course.toFixed(0)}°</td>
                    </tr>
                    ${vessel.destination ? `
                    <tr>
                        <td style="padding-right: 10px; font-weight: 600; color: #555;">Destination:</td>
                        <td><span style="color: #2ecc71;">${vessel.destination}</span></td>
                    </tr>
                    ` : ''}
                    <tr>
                        <td style="padding-right: 10px; font-weight: 600; color: #555;">Updated:</td>
                        <td>${timestamp}</td>
                    </tr>
                </table>
                <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #eee; 
                            font-size: 11px; color: #666; line-height: 1.4;">
                    <i class="fas fa-info-circle" style="margin-right: 4px;"></i>
                    ${isFallback ? 
                        'Using empirical vessel data based on Norwegian maritime patterns. ' +
                        'Real-time data will resume when available.' : 
                        'Real-time vessel tracking via Norwegian AIS data sources.'}
                </div>
            </div>
        </div>
    `;
}

/**
 * Update vessel counter in UI
 */
function updateVesselCounter(sourceType, vesselName) {
    const counterElement = document.getElementById('real-time-vessel-counter');
    if (!counterElement) return;
    
    counterElement.textContent = sourceType === 'real' ? '🚢 LIVE' : '📡 SIM';
    counterElement.title = sourceType === 'real' ? 
        `Real-time: ${vesselName}` : 
        `Fallback: ${vesselName} (Real-time unavailable)`;
    
    counterElement.style.color = sourceType === 'real' ? '#28a745' : '#ffc107';
    counterElement.style.fontWeight = 'bold';
    
    const sourceElement = document.getElementById('vessel-source');
    if (sourceElement) {
        sourceElement.textContent = sourceType === 'real' ? 'Real-time tracking' : 'Empirical simulation';
        sourceElement.style.color = sourceType === 'real' ? '#28a745' : '#ffc107';
    }
    
    const timeElement = document.getElementById('vessel-update-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = `Updated: ${now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    }
    
    // Show subtle notification for source changes
    if (window.vesselSource !== sourceType) {
        window.vesselSource = sourceType;
        if (sourceType === 'fallback') {
            console.log('🔄 Switched to empirical fallback mode');
        } else if (sourceType === 'real') {
            console.log('🔄 Returned to real-time mode');
        }
    }
}

/**
 * Stop vessel tracking
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
// UTILITY FUNCTIONS
// ============================================

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const types = {
        'info': { class: 'alert-info', icon: 'ℹ️' },
        'success': { class: 'alert-success', icon: '✅' },
        'warning': { class: 'alert-warning', icon: '⚠️' },
        'error': { class: 'alert-danger', icon: '❌' }
    };
    
    const config = types[type] || types.info;
    
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
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) notification.remove();
    }, 5000);
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize everything
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌊 Maritime Map v3.0.0: DOM loaded');
    
    initMaritimeMap();
    
    setTimeout(() => {
        loadAndDisplayRTZRoutes();
    }, 500);
    
    setTimeout(() => {
        addRouteTableEventListeners();
    }, 1500);
    
    // Make functions available globally
    window.loadRTZRoutes = loadAndDisplayRTZRoutes;
    window.initMaritimeMap = initMaritimeMap;
    window.showNotification = showNotification;
    window.startVesselTracking = startEnhancedVesselTracking;
    window.stopVesselTracking = stopVesselTracking;
    window.updateRealTimeVessel = fetchVesselWithRetry;
    
    console.log('✅ Maritime Map Module v3.0.0 ready');
});

/**
 * Add event listeners to route table
 */
function addRouteTableEventListeners() {
    console.log('🔗 Adding route table event listeners...');
    
    document.addEventListener('click', function(e) {
        // View Route buttons
        if (e.target.closest('.view-route-btn')) {
            const button = e.target.closest('.view-route-btn');
            const routeId = button.dataset.routeId;
            
            if (routeId) {
                const row = button.closest('tr');
                if (row) {
                    const rows = Array.from(row.parentNode.querySelectorAll('tr:not(:first-child)'));
                    const rowIndex = rows.indexOf(row);
                    
                    if (rowIndex !== -1) {
                        const success = window.zoomToRoute(rowIndex);
                        if (success) {
                            document.querySelectorAll('.route-row-highlighted').forEach(r => {
                                r.classList.remove('route-row-highlighted');
                            });
                            row.classList.add('route-row-highlighted');
                            return;
                        }
                    }
                }
                
                const success = window.zoomToRoute(routeId);
                if (!success) {
                    showNotification('Could not find the route on the map', 'error');
                } else {
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
        
        // Highlight Route buttons
        if (e.target.closest('.highlight-route-btn')) {
            const button = e.target.closest('.highlight-route-btn');
            const routeId = button.dataset.routeId;
            
            if (routeId) {
                const row = button.closest('tr');
                if (row) {
                    const rows = Array.from(row.parentNode.querySelectorAll('tr:not(:first-child)'));
                    const rowIndex = rows.indexOf(row);
                    
                    if (rowIndex !== -1) {
                        window.highlightRoute(rowIndex);
                        return;
                    }
                }
                
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

// Add enhanced CSS styles
const enhancedStyles = document.createElement('style');
enhancedStyles.textContent = `
    .rtz-route-line {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .route-start-marker, .route-end-marker {
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
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes vessel-pulse {
        0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
    }
    
    .vessel-pulse-animation {
        animation: vessel-pulse 2s infinite !important;
    }
    
    .vessel-real-time {
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .vessel-fallback {
        cursor: pointer;
        opacity: 0.9;
        transition: all 0.2s ease;
    }
    
    .vessel-marker:hover {
        filter: brightness(1.2);
        transform: scale(1.1);
    }
    
    .route-row-highlighted {
        background-color: rgba(52, 152, 219, 0.15) !important;
        border-left: 3px solid #3498db !important;
    }
    
    /* Prevent blinking for waypoints */
    .rtz-waypoint-marker,
    .leaflet-marker-icon[class*="waypoint"],
    .leaflet-marker-icon[class*="rtz"],
    .waypoint-marker {
        animation: none !important;
        -webkit-animation: none !important;
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
        transition: all 0.3s ease;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .leaflet-control-legend {
            font-size: 10px;
            padding: 8px;
        }
        
        .legend-title {
            font-size: 11px;
        }
    }
`;
document.head.appendChild(enhancedStyles);