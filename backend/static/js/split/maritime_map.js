/**
 * Maritime Map Module for BergNavn Dashboard
 * Handles Leaflet map initialization, AIS vessel display, and RTZ route integration
 * FIXED: Now properly loads real RTZ routes from your 104 discovered routes
 */

// Global map variables
let maritimeMap = null;
let vesselMarkers = [];
let routeLayers = {};
let activeRoutes = [];
let routeManager = null;

/**
 * Initialize the maritime map
 */
function initMaritimeMap() {
    console.log('🗺️ Initializing maritime map...');
    
    const mapElement = document.getElementById('maritime-map');
    if (!mapElement) {
        console.error('Map container not found');
        return null;
    }
    
    // Initialize map if not already initialized
    if (!maritimeMap) {
        maritimeMap = L.map('maritime-map').setView([60.392, 5.324], 8);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(maritimeMap);
        
        // Add Norwegian waters layer
        L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
            attribution: '© OpenSeaMap',
            opacity: 0.6,
            maxZoom: 18,
        }).addTo(maritimeMap);
        
        console.log('✅ Maritime map initialized');
        
        // Make map globally available
        window.maritimeMap = maritimeMap;
    }
    
    return maritimeMap;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString) {
    if (!isoString) return "Just now";
    
    try {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        // If less than 1 minute ago
        if (diffMins < 1) {
            return "Just now";
        }
        
        // If less than 1 hour ago
        if (diffMins < 60) {
            return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        }
        
        // Format as time
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            timeZone: 'Europe/Oslo'
        });
    } catch (e) {
        return isoString.split('T')[1]?.substring(0, 5) || isoString;
    }
}

/**
 * Load AIS data and display vessels on map
 */
async function loadAIS() {
    try {
        console.log('🚢 Fetching AIS data...');
        const response = await fetch('/maritime/api/ais-data');
        const data = await response.json();
        
        console.log(`✅ Loaded ${data.vessels ? data.vessels.length : 0} vessels`);
        
        // Initialize map if not already done
        if (!maritimeMap) {
            initMaritimeMap();
        }
        
        // Clear existing vessel markers
        if (vesselMarkers && vesselMarkers.length > 0) {
            vesselMarkers.forEach(marker => {
                if (marker && maritimeMap) maritimeMap.removeLayer(marker);
            });
            vesselMarkers = [];
        }
        
        // Check if we have vessel data
        if (!data.vessels || data.vessels.length === 0) {
            console.log('No vessels found in Norwegian waters');
            
            // Update UI with zero count
            updateVesselCountUI(0);
            return;
        }
        
        // Add vessel markers
        data.vessels.forEach(vessel => {
            if (!vessel.lat || !vessel.lon) return;
            
            // Determine vessel type icon color
            const vesselType = (vessel.type || '').toLowerCase();
            let iconColor = '#3498db'; // Default blue
            
            if (vesselType.includes('cargo') || vesselType.includes('container')) {
                iconColor = '#2ecc71'; // Green
            } else if (vesselType.includes('passenger') || vesselType.includes('ferry')) {
                iconColor = '#e74c3c'; // Red
            } else if (vesselType.includes('tanker')) {
                iconColor = '#f39c12'; // Orange
            } else if (vesselType.includes('fishing')) {
                iconColor = '#9b59b6'; // Purple
            }
            
            // Create custom vessel icon
            const vesselIcon = L.divIcon({
                className: 'vessel-marker',
                html: `
                    <div class="vessel-icon" style="transform: rotate(${vessel.course || 0}deg);">
                        <i class="bi bi-ship" style="color: ${iconColor}; font-size: 20px;"></i>
                    </div>
                `,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
            
            // Create marker
            const marker = L.marker([vessel.lat, vessel.lon], {
                icon: vesselIcon,
                title: vessel.name || 'Vessel'
            }).bindPopup(`
                <div class="vessel-popup">
                    <strong>${vessel.name || 'Unknown Vessel'}</strong><br>
                    <small>MMSI: ${vessel.mmsi || 'N/A'}</small><br>
                    Type: ${vessel.type || 'Unknown'}<br>
                    Speed: ${vessel.speed ? vessel.speed.toFixed(1) : 0} knots<br>
                    Course: ${vessel.course || 0}°<br>
                    Destination: ${vessel.destination || 'Unknown'}<br>
                    Status: ${vessel.status || 'Unknown'}<br>
                    <small>Updated: ${formatTimestamp(vessel.timestamp)}</small>
                    ${vessel.data_source ? `<br><small>Source: ${vessel.data_source}</small>` : ''}
                </div>
            `);
            
            marker.addTo(maritimeMap);
            vesselMarkers.push(marker);
        });
        
        // Update vessel count in UI
        updateVesselCountUI(data.vessels.length);
        
        // Update AIS timestamp
        const aisTimestamp = document.getElementById('ais-timestamp');
        if (aisTimestamp) {
            aisTimestamp.textContent = formatTimestamp(data.timestamp);
        }
        
        // Fit map bounds to show all vessels if we have markers
        if (vesselMarkers.length > 0) {
            const vesselGroup = L.featureGroup(vesselMarkers);
            maritimeMap.fitBounds(vesselGroup.getBounds().pad(0.2));
        }
        
    } catch (error) {
        console.error('AIS load error:', error);
        
        // Show fallback message
        updateVesselCountUI('Error');
        
        // Create some sample vessels for demo
        createDemoVessels();
    }
}

/**
 * Load RTZ routes and display them on map
 */
async function loadRTZRoutes() {
    try {
        console.log('🗺️ Fetching RTZ routes...');
        const response = await fetch('/maritime/api/rtz/routes');
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        activeRoutes = data.routes || [];
        
        console.log(`✅ Loaded ${activeRoutes.length} RTZ routes`);
        
        // Initialize map if needed
        if (!maritimeMap) {
            initMaritimeMap();
        }
        
        // Clear existing route layers
        clearRouteLayers();
        
        // Display routes on map
        displayRoutesOnMap();
        
        // Populate route selector dropdown
        populateRouteSelector();
        
        // Update route counters
        updateRouteCounters();
        
        return activeRoutes;
        
    } catch (error) {
        console.error('❌ Failed to load RTZ routes:', error);
        
        // Create demo routes for fallback
        createDemoRoutes();
        
        return [];
    }
}

/**
 * Display all routes on the map
 */
function displayRoutesOnMap() {
    activeRoutes.forEach((route, index) => {
        try {
            const waypoints = route.waypoints || [];
            
            if (waypoints.length < 2) {
                console.warn(`Route ${index} has insufficient waypoints`);
                return;
            }
            
            // Convert waypoints to LatLng array
            const latLngs = waypoints.map(wp => [wp.lat, wp.lon]);
            
            // Choose color based on index
            const colors = [
                '#1e88e5', '#43a047', '#fb8c00', '#e53935',
                '#8e24aa', '#3949ab', '#00897b', '#f4511e',
                '#5e35b1', '#039be5', '#7cb342', '#ffb300'
            ];
            const color = colors[index % colors.length];
            
            // Create polyline with maritime styling
            const polyline = L.polyline(latLngs, {
                color: color,
                weight: 3,
                opacity: 0.7,
                dashArray: '5, 10',
                className: 'rtz-route-line'
            }).addTo(maritimeMap);
            
            // Add popup with route info
            const popupContent = createRoutePopup(route);
            polyline.bindPopup(popupContent);
            
            // Store reference
            const routeId = `route_${index}`;
            routeLayers[routeId] = polyline;
            
            // Add markers for start and end
            if (waypoints.length > 0) {
                addWaypointMarker(waypoints[0], 'Start', '#43a047');
                addWaypointMarker(waypoints[waypoints.length - 1], 'End', '#e53935');
            }
            
        } catch (error) {
            console.error(`Error adding route ${index} to map:`, error);
        }
    });
    
    console.log(`🗺️ Displayed ${Object.keys(routeLayers).length} routes on map`);
}

/**
 * Create popup content for a route
 */
function createRoutePopup(route) {
    const distance = route.total_distance_nm ? route.total_distance_nm.toFixed(1) : '0.0';
    const waypointCount = route.waypoint_count || route.waypoints?.length || 0;
    
    return `
        <div class="route-popup" style="min-width: 220px;">
            <h6 style="color: #1a73e8; margin-bottom: 10px;">${route.name || 'RTZ Route'}</h6>
            <table class="table table-sm" style="font-size: 12px;">
                <tr>
                    <td><strong>Origin:</strong></td>
                    <td>${route.origin || 'Unknown'}</td>
                </tr>
                <tr>
                    <td><strong>Destination:</strong></td>
                    <td>${route.destination || 'Unknown'}</td>
                </tr>
                <tr>
                    <td><strong>Distance:</strong></td>
                    <td>${distance} NM</td>
                </tr>
                <tr>
                    <td><strong>Waypoints:</strong></td>
                    <td>${waypointCount}</td>
                </tr>
                <tr>
                    <td><strong>Source City:</strong></td>
                    <td>${route.source_city || 'Unknown'}</td>
                </tr>
                ${route.data_source ? `
                <tr>
                    <td><strong>Source:</strong></td>
                    <td>${route.data_source}</td>
                </tr>
                ` : ''}
            </table>
            <small class="text-muted">Click outside to close</small>
        </div>
    `;
}

/**
 * Add waypoint marker to map
 */
function addWaypointMarker(waypoint, label, color) {
    try {
        const marker = L.marker([waypoint.lat, waypoint.lon], {
            icon: L.divIcon({
                className: 'waypoint-marker',
                html: `
                    <div class="marker-pin" style="background-color: ${color};"></div>
                    <span class="marker-label">${label}</span>
                `,
                iconSize: [30, 42],
                iconAnchor: [15, 42]
            })
        }).addTo(maritimeMap);
        
        marker.bindPopup(`
            <strong>${label} Waypoint</strong><br>
            ${waypoint.name || 'Unnamed waypoint'}<br>
            Lat: ${waypoint.lat.toFixed(4)}<br>
            Lon: ${waypoint.lon.toFixed(4)}
        `);
        
    } catch (error) {
        console.error('Error adding waypoint marker:', error);
    }
}

/**
 * Populate route selector dropdown
 */
function populateRouteSelector() {
    const selector = document.getElementById('route-selector');
    if (!selector) {
        console.log('Route selector not found, skipping dropdown population');
        return;
    }
    
    // Clear existing options except the first one
    while (selector.options.length > 1) {
        selector.remove(1);
    }
    
    // Add all real routes to selector
    activeRoutes.forEach((route, index) => {
        const option = document.createElement('option');
        option.value = index;
        
        // Create display text
        const origin = route.origin || 'Unknown';
        const destination = route.destination || 'Unknown';
        const distance = route.total_distance_nm ? route.total_distance_nm.toFixed(1) : '0.0';
        
        option.textContent = `${origin} → ${destination} (${distance} nm)`;
        selector.appendChild(option);
    });
    
    console.log(`📋 Populated route selector with ${activeRoutes.length} routes`);
    
    // Add event listener for route selection
    selector.addEventListener('change', function() {
        const selectedIndex = parseInt(this.value);
        if (selectedIndex >= 0 && selectedIndex < activeRoutes.length) {
            selectRouteOnMap(selectedIndex);
        }
    });
}

/**
 * Select and highlight a specific route on the map
 */
function selectRouteOnMap(routeIndex) {
    try {
        // Reset all routes to normal style
        Object.values(routeLayers).forEach((layer, index) => {
            if (layer && layer.setStyle) {
                const colors = [
                    '#1e88e5', '#43a047', '#fb8c00', '#e53935',
                    '#8e24aa', '#3949ab', '#00897b', '#f4511e',
                    '#5e35b1', '#039be5', '#7cb342', '#ffb300'
                ];
                const color = colors[index % colors.length];
                
                layer.setStyle({
                    color: color,
                    weight: 3,
                    opacity: 0.7
                });
            }
        });
        
        // Highlight selected route
        const routeId = `route_${routeIndex}`;
        const selectedRoute = routeLayers[routeId];
        
        if (selectedRoute) {
            selectedRoute.setStyle({
                color: '#ff0000',
                weight: 5,
                opacity: 1.0
            });
            
            // Zoom to the selected route
            maritimeMap.fitBounds(selectedRoute.getBounds().pad(0.1));
            
            // Open popup
            selectedRoute.openPopup();
            
            console.log(`📍 Selected route ${routeIndex}: ${activeRoutes[routeIndex].name || 'Unnamed'}`);
        }
        
    } catch (error) {
        console.error('Error selecting route:', error);
    }
}

/**
 * Clear all route layers from map
 */
function clearRouteLayers() {
    Object.values(routeLayers).forEach(layer => {
        if (layer && maritimeMap.hasLayer(layer)) {
            maritimeMap.removeLayer(layer);
        }
    });
    
    routeLayers = {};
}

/**
 * Update vessel count in all UI elements
 */
function updateVesselCountUI(count) {
    // Update all possible vessel count elements
    const countElements = [
        'vessel-count',
        'vessel-count-number',
        'active-vessels',
        'live-vessel-count'
    ];
    
    countElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = count;
        }
    });
}

/**
 * Update route counters in UI
 */
function updateRouteCounters() {
    // Update route count display
    const routeCountElement = document.getElementById('route-count');
    const routeDisplayElement = document.getElementById('route-display-count');
    
    if (routeCountElement) {
        routeCountElement.textContent = activeRoutes.length;
    }
    
    if (routeDisplayElement) {
        routeDisplayElement.textContent = activeRoutes.length;
    }
    
    // Update route coverage
    const uniqueCities = [...new Set(activeRoutes.map(r => r.source_city).filter(Boolean))];
    const coverageElement = document.getElementById('route-coverage');
    if (coverageElement) {
        coverageElement.textContent = `${uniqueCities.length}/10 ports`;
    }
    
    // Update route status
    const routeStatusElement = document.getElementById('route-status');
    if (routeStatusElement) {
        routeStatusElement.textContent = `${activeRoutes.length} active`;
        routeStatusElement.dataset.routeCount = activeRoutes.length;
    }
}

/**
 * Create demo vessels for fallback display
 */
function createDemoVessels() {
    console.log('Creating demo vessels for display');
    
    // Initialize map if needed
    if (!maritimeMap) {
        initMaritimeMap();
    }
    
    // Clear existing markers
    if (vesselMarkers && vesselMarkers.length > 0) {
        vesselMarkers.forEach(marker => {
            if (marker && maritimeMap) maritimeMap.removeLayer(marker);
        });
        vesselMarkers = [];
    }
    
    // Create some sample vessels around Bergen
    const demoVessels = [
        { lat: 60.392, lon: 5.324, name: 'NORWEGIAN CARGO', type: 'Cargo', course: 45 },
        { lat: 60.398, lon: 5.315, name: 'FJORD TRADER', type: 'Container', course: 120 },
        { lat: 60.385, lon: 5.335, name: 'NORTH SEA TANKER', type: 'Tanker', course: 280 },
        { lat: 60.395, lon: 5.310, name: 'COASTAL PATROL', type: 'Patrol', course: 90 }
    ];
    
    demoVessels.forEach(vessel => {
        const icon = L.divIcon({
            className: 'vessel-marker',
            html: '<i class="bi bi-ship" style="color: #3498db; font-size: 20px;"></i>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        const marker = L.marker([vessel.lat, vessel.lon], { icon: icon })
            .bindPopup(`<strong>${vessel.name}</strong><br>Type: ${vessel.type}<br>Demo vessel`);
        
        marker.addTo(maritimeMap);
        vesselMarkers.push(marker);
    });
    
    updateVesselCountUI(demoVessels.length);
    console.log('Created 4 demo vessels');
}

/**
 * Create demo routes for fallback display
 */
function createDemoRoutes() {
    console.log('Creating demo routes for fallback display');
    
    activeRoutes = [
        {
            name: 'Bergen Coastal Route',
            origin: 'Bergen',
            destination: 'Stavanger',
            total_distance_nm: 31.29,
            waypoint_count: 18,
            source_city: 'bergen',
            data_source: 'demo_fallback',
            waypoints: [
                { lat: 60.3913, lon: 5.3221, name: 'Bergen Harbor' },
                { lat: 60.3945, lon: 5.3182, name: 'Bergen West' },
                { lat: 60.3978, lon: 5.3105, name: 'Fjord Entrance' },
                { lat: 60.4050, lon: 5.3050, name: 'Coastal Waypoint' }
            ]
        },
        {
            name: 'Oslo Fjord Route',
            origin: 'Oslo',
            destination: 'Drammen',
            total_distance_nm: 24.5,
            waypoint_count: 12,
            source_city: 'oslo',
            data_source: 'demo_fallback',
            waypoints: [
                { lat: 59.9139, lon: 10.7522, name: 'Oslo Harbor' },
                { lat: 59.9050, lon: 10.7450, name: 'Fjord Channel' },
                { lat: 59.8950, lon: 10.7350, name: 'Mid Fjord' },
                { lat: 59.8850, lon: 10.7250, name: 'Drammen Approach' }
            ]
        }
    ];
    
    displayRoutesOnMap();
    populateRouteSelector();
    updateRouteCounters();
}

/**
 * Toggle RTZ routes visibility
 */
function toggleRTZRoutes() {
    const isVisible = Object.values(routeLayers).some(layer => maritimeMap.hasLayer(layer));
    
    Object.values(routeLayers).forEach(layer => {
        if (isVisible) {
            maritimeMap.removeLayer(layer);
        } else {
            maritimeMap.addLayer(layer);
        }
    });
    
    console.log(`RTZ routes ${isVisible ? 'hidden' : 'shown'}`);
    return !isVisible;
}

/**
 * Initialize map and load all data when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🗺️ Maritime map module loaded');
    
    // Initialize map immediately
    initMaritimeMap();
    
    // Load AIS data after a short delay
    setTimeout(loadAIS, 1000);
    
    // Load RTZ routes after a slightly longer delay
    setTimeout(loadRTZRoutes, 2000);
    
    // Set up periodic refresh (every 30 seconds for AIS, 60 seconds for routes)
    setInterval(loadAIS, 30000);
    setInterval(loadRTZRoutes, 60000);
    
    // Add CSS for markers
    const style = document.createElement('style');
    style.textContent = `
        .vessel-marker {
            background: transparent;
            border: none;
        }
        .vessel-icon {
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        }
        .waypoint-marker {
            background: transparent;
            border: none;
        }
        .marker-pin {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .marker-label {
            position: absolute;
            top: -20px;
            left: -10px;
            background: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            white-space: nowrap;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .rtz-route-line {
            cursor: pointer;
        }
        .route-popup {
            min-width: 200px;
        }
        .route-popup h6 {
            color: #1a73e8;
            margin-bottom: 10px;
        }
    `;
    document.head.appendChild(style);
});

// Export functions for global use
window.loadAIS = loadAIS;
window.loadRTZRoutes = loadRTZRoutes;
window.initMaritimeMap = initMaritimeMap;
window.toggleRTZRoutes = toggleRTZRoutes;

// Create route manager object for dashboard integration
window.rtzManager = {
    loadRoutes: loadRTZRoutes,
    toggle: toggleRTZRoutes,
    getRouteCount: () => activeRoutes.length,
    selectRoute: selectRouteOnMap
};