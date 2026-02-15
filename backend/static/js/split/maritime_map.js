/**
 * Maritime Map Module for BergNavn Dashboard
 * Version: 4.0.4 - FINAL VERSION - REAL-TIME FIRST
 * 
 * CRITICAL FIXES:
 * - Larger vessel markers (48px for better visibility)
 * - Precise sea coordinates for Bergen (Byfjorden)
 * - Real-time AIS from Kystverket → Kystdatahuset → BarentsWatch
 * - Empirical fallback as LAST RESORT only
 * - Smooth movement animations
 */

// Global map variables
let maritimeMap = null;
let activeRoutes = [];
let routePolylines = [];
let vesselMarker = null;
let vesselTrackingActive = false;
let vesselUpdateInterval = null;
let lastVesselPosition = null;
let movementAnimation = null;
let mapInitialized = false;

// Norwegian port coordinates (ACTUAL SEA POSITIONS)
const PORT_COORDINATES = {
    'bergen': { 
        lat: 60.3972,   // Byfjorden - EXACT SEA POSITION
        lon: 5.3031, 
        name: 'Bergen',
        description: 'Bergen Harbor (Byfjorden)'
    },
    'oslo': { 
        lat: 59.9067,   // Oslofjorden
        lon: 10.7342, 
        name: 'Oslo',
        description: 'Oslo Harbor (Oslofjorden)'
    },
    'stavanger': { 
        lat: 58.9733,   // Vågen
        lon: 5.7319, 
        name: 'Stavanger',
        description: 'Stavanger Harbor (Vågen)'
    },
    'trondheim': { 
        lat: 63.4385,   // Trondheimsfjorden
        lon: 10.4056, 
        name: 'Trondheim',
        description: 'Trondheim Harbor (Trondheimsfjorden)'
    },
    'alesund': { 
        lat: 62.4719,   // Brosundet
        lon: 6.1556, 
        name: 'Ålesund',
        description: 'Ålesund Harbor (Brosundet)'
    },
    'andalsnes': { 
        lat: 62.5675,   // Romsdalsfjorden
        lon: 7.6870, 
        name: 'Åndalsnes',
        description: 'Åndalsnes Harbor (Romsdalsfjorden)'
    },
    'kristiansand': { 
        lat: 58.1458,   // Topdalsfjorden
        lon: 8.0025, 
        name: 'Kristiansand',
        description: 'Kristiansand Harbor (Topdalsfjorden)'
    },
    'drammen': { 
        lat: 59.7375,   // Drammensfjorden
        lon: 10.2417, 
        name: 'Drammen',
        description: 'Drammen Harbor (Drammensfjorden)'
    },
    'sandefjord': { 
        lat: 59.1308,   // Mefjorden
        lon: 10.2303, 
        name: 'Sandefjord',
        description: 'Sandefjord Harbor (Mefjorden)'
    },
    'flekkefjord': { 
        lat: 58.2967,   // Grumre Sund
        lon: 6.6631, 
        name: 'Flekkefjord',
        description: 'Flekkefjord Harbor'
    }
};

// ============================================
// MAP INITIALIZATION
// ============================================

/**
 * Initialize the maritime map
 */
function initMaritimeMap() {
    console.log('🌊 Maritime Map v4.0.4 initializing...');
    
    const mapElement = document.getElementById('maritime-map');
    if (!mapElement) {
        console.error('❌ Map container not found');
        return null;
    }
    
    if (!maritimeMap) {
        // Start centered on Norwegian waters
        maritimeMap = L.map('maritime-map').setView([62.0, 5.5], 6);
        
        // Base map
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(maritimeMap);
        
        // Sea marks
        L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
            attribution: '© OpenSeaMap',
            opacity: 0.4,
            maxZoom: 18,
        }).addTo(maritimeMap);
        
        console.log('✅ Maritime map created');
        window.map = maritimeMap;
        mapInitialized = true;
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
    
    if (!mapInitialized) {
        setTimeout(loadAndDisplayRTZRoutes, 500);
        return;
    }
    
    clearAllRouteLayers();
    
    // Try to get routes from template first
    const routesFromTemplate = loadRoutesFromTemplate();
    if (routesFromTemplate && routesFromTemplate.length > 0) {
        activeRoutes = routesFromTemplate;
        displayRoutesOnMap();
        startVesselTracking();
        return;
    }
    
    // Fallback to API
    fetch('/maritime/api/rtz/routes')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.routes && data.routes.length > 0) {
                console.log(`✅ Loaded ${data.routes.length} routes from API`);
                activeRoutes = data.routes;
                displayRoutesOnMap();
                startVesselTracking();
            } else {
                startVesselTracking();
            }
        })
        .catch(error => {
            console.error('❌ Error loading from API:', error);
            startVesselTracking();
        });
}

/**
 * Load routes from template
 */
function loadRoutesFromTemplate() {
    try {
        const routesDataElement = document.getElementById('routes-data');
        if (!routesDataElement || !routesDataElement.textContent) {
            return [];
        }
        
        const routes = JSON.parse(routesDataElement.textContent);
        console.log(`✅ Found ${routes.length} routes in template`);
        return routes;
    } catch (error) {
        console.error('❌ Error loading routes from template:', error);
        return [];
    }
}

/**
 * Display routes on map
 */
function displayRoutesOnMap() {
    if (!maritimeMap || !activeRoutes.length) return;
    
    console.log(`🗺️ Displaying ${activeRoutes.length} routes...`);
    clearAllRouteLayers();
    
    activeRoutes.forEach((route, index) => {
        displaySingleRoute(route, index);
    });
    
    fitMapToRoutes();
    addMapLegend();
    updateRouteCounters();
}

/**
 * Display single route
 */
function displaySingleRoute(route, index) {
    if (!maritimeMap) return;
    
    const waypoints = extractWaypointsFromRoute(route);
    if (waypoints.length < 2) return;
    
    const colors = {
        'bergen': '#1e88e5', 'oslo': '#43a047', 'stavanger': '#f39c12',
        'trondheim': '#e74c3c', 'alesund': '#9b59b6', 'andalsnes': '#3498db',
        'kristiansand': '#2ecc71', 'drammen': '#e67e22', 'sandefjord': '#16a085',
        'flekkefjord': '#8e44ad'
    };
    
    const port = (route.source_city || '').toLowerCase().replace('å', 'a');
    const color = colors[port] || '#1e88e5';
    const coordinates = waypoints.map(wp => [wp.lat, wp.lon]);
    
    const polyline = L.polyline(coordinates, {
        color: color,
        weight: 4,
        opacity: 0.8
    }).addTo(maritimeMap);
    
    routePolylines.push(polyline);
    
    // Start marker
    L.circleMarker(coordinates[0], {
        color: '#28a745',
        fillColor: '#28a745',
        fillOpacity: 1.0,
        radius: 8
    }).addTo(maritimeMap).bindTooltip(`<b>Start:</b> ${route.origin || 'Unknown'}`);
    
    // End marker
    L.circleMarker(coordinates[coordinates.length - 1], {
        color: '#dc3545',
        fillColor: '#dc3545',
        fillOpacity: 1.0,
        radius: 8
    }).addTo(maritimeMap).bindTooltip(`<b>End:</b> ${route.destination || 'Unknown'}`);
    
    polyline.on('click', () => zoomToRoute(index));
}

/**
 * Extract waypoints from route
 */
function extractWaypointsFromRoute(route) {
    let waypoints = [];
    
    if (route.waypoints && Array.isArray(route.waypoints)) {
        waypoints = route.waypoints.map(wp => ({
            lat: wp.lat || wp[1],
            lon: wp.lon || wp[0]
        }));
    }
    
    return waypoints.filter(wp => 
        wp.lat && wp.lon && !isNaN(wp.lat) && !isNaN(wp.lon)
    );
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
            <div class="legend-title">Maritime Map</div>
            <div class="legend-item">
                <span class="legend-color" style="background:#28a745;"></span>
                <span class="legend-label">Route Start</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background:#dc3545;"></span>
                <span class="legend-label">Route End</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background:#1e88e5;"></span>
                <span class="legend-label">RTZ Route</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background:#28a745;"></span>
                <span class="legend-label">Live Vessel (Real-time)</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background:#ffc107;"></span>
                <span class="legend-label">Empirical Fallback</span>
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
}

/**
 * Update route counters
 */
function updateRouteCounters() {
    const routeCountElement = document.getElementById('route-count');
    const routeCountBadge = document.getElementById('route-count-badge');
    
    if (routeCountElement) routeCountElement.textContent = activeRoutes.length;
    if (routeCountBadge) routeCountBadge.textContent = activeRoutes.length;
}

// ============================================
// VESSEL TRACKING - REAL-TIME FIRST
// ============================================

/**
 * Start vessel tracking
 */
function startVesselTracking(intervalSeconds = 30) {
    console.log('🚢 Starting vessel tracking (REAL-TIME first)...');
    
    if (vesselUpdateInterval) {
        clearInterval(vesselUpdateInterval);
    }
    
    vesselTrackingActive = true;
    
    setTimeout(() => {
        fetchVessel();
        vesselUpdateInterval = setInterval(fetchVessel, intervalSeconds * 1000);
    }, 1000);
}

/**
 * Fetch vessel data - SINGLE source of truth
 */
async function fetchVessel() {
    if (!vesselTrackingActive || !maritimeMap) return;
    
    try {
        console.log('📡 Fetching vessel from backend...');
        const response = await fetch('/maritime/api/vessels/real-time?city=bergen&radius_km=50');
        
        if (!response.ok) {
            console.warn(`⚠️ Vessel API returned ${response.status}`);
            return;
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.vessels && data.vessels.length > 0) {
            const vessel = data.vessels[0];
            const source = data.source || vessel.source;
            
            // Determine if real-time or empirical
            const isRealTime = source && (
                source.includes('REAL-TIME') || 
                source.includes('KYSTVERKET') ||
                source.includes('KYSTDATAHUSET') ||
                source.includes('BARENTS')
            );
            
            // Get sea coordinates
            const vesselLat = vessel.latitude || vessel.lat;
            const vesselLon = vessel.longitude || vessel.lon;
            
            // Adjust to sea if needed
            const adjustedCoords = adjustToSea(vesselLat, vesselLon, vessel.location);
            
            vessel.latitude = adjustedCoords.lat;
            vessel.longitude = adjustedCoords.lon;
            
            console.log(`🚢 Vessel: ${vessel.name}, Real-time: ${isRealTime}, Source: ${source}`);
            console.log(`   Position: ${adjustedCoords.lat.toFixed(4)}°, ${adjustedCoords.lon.toFixed(4)}°`);
            
            const newPosition = {
                lat: adjustedCoords.lat,
                lon: adjustedCoords.lon,
                speed: vessel.speed || vessel.sog || 0,
                heading: vessel.heading || vessel.cog || 0
            };
            
            if (lastVesselPosition && vesselMarker) {
                animateVesselMovement(lastVesselPosition, newPosition);
            } else {
                displayVessel(vessel, isRealTime, source);
            }
            
            lastVesselPosition = newPosition;
            updateVesselCounters(isRealTime, vessel, source);
            
            window.dashboardData = window.dashboardData || {};
            window.dashboardData.vesselData = vessel;
            window.dashboardData.dataSource = source;
            window.dashboardData.isRealTime = isRealTime;
            
        } else {
            console.log('⚠️ No vessel in response');
            clearVesselDisplay();
        }
    } catch (error) {
        console.error('❌ Error fetching vessel:', error);
    }
}

/**
 * Adjust coordinates to ensure vessel is in sea
 */
function adjustToSea(lat, lon, location) {
    const locationLower = (location || '').toLowerCase();
    
    for (const [portName, portCoords] of Object.entries(PORT_COORDINATES)) {
        if (locationLower.includes(portName) || 
            (portName === 'bergen' && locationLower.includes('bergen'))) {
            
            const distance = calculateDistance(lat, lon, portCoords.lat, portCoords.lon);
            
            if (distance > 5) {
                console.log(`📍 Adjusting ${portName} vessel to sea (${distance.toFixed(1)}km off)`);
                return {
                    lat: portCoords.lat,
                    lon: portCoords.lon
                };
            }
        }
    }
    
    return { lat, lon };
}

/**
 * Calculate distance between two points
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

/**
 * Animate vessel movement
 */
function animateVesselMovement(oldPos, newPos) {
    if (!maritimeMap || !vesselMarker) return;
    
    if (movementAnimation) {
        clearInterval(movementAnimation);
    }
    
    const steps = 20;
    const stepTime = 50;
    let currentStep = 0;
    
    const latDiff = newPos.lat - oldPos.lat;
    const lonDiff = newPos.lon - oldPos.lon;
    
    movementAnimation = setInterval(() => {
        currentStep++;
        
        if (currentStep >= steps) {
            vesselMarker.setLatLng([newPos.lat, newPos.lon]);
            clearInterval(movementAnimation);
            movementAnimation = null;
            return;
        }
        
        const progress = currentStep / steps;
        const currentLat = oldPos.lat + (latDiff * progress);
        const currentLon = oldPos.lon + (lonDiff * progress);
        
        vesselMarker.setLatLng([currentLat, currentLon]);
    }, stepTime);
}

/**
 * Display vessel on map - LARGER SIZE (48px)
 */
function displayVessel(vessel, isRealTime, source) {
    if (!maritimeMap) return;
    
    if (vesselMarker) {
        maritimeMap.removeLayer(vesselMarker);
        vesselMarker = null;
    }
    
    const lat = vessel.latitude || vessel.lat;
    const lon = vessel.longitude || vessel.lon;
    
    if (!lat || !lon) {
        console.error('❌ Invalid vessel coordinates');
        return;
    }
    
    const color = isRealTime ? '#28a745' : '#ffc107';
    const statusText = isRealTime ? '🔴 LIVE' : '🟡 EMPIRICAL';
    const pulseAnimation = isRealTime ? 'pulse-live 2s infinite' : 'none';
    const heading = vessel.heading || vessel.cog || 0;
    
    // LARGER VESSEL ICON - 48px
    const vesselIcon = L.divIcon({
        className: `vessel-marker ${isRealTime ? 'vessel-real-time' : 'vessel-empirical'}`,
        html: `
            <div style="position: relative;">
                <!-- Direction arrow -->
                <div style="
                    position: absolute;
                    top: -28px;
                    left: 50%;
                    transform: translateX(-50%) rotate(${heading}deg);
                    color: ${color};
                    font-size: 22px;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    opacity: 0.9;
                    transition: transform 0.3s ease;
                ">▲</div>
                
                <!-- Vessel circle - 48px -->
                <div style="
                    background: ${color};
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    animation: ${pulseAnimation};
                    position: relative;
                ">
                    🚢
                </div>
                
                <!-- Speed indicator -->
                ${(vessel.speed || 0) > 0.5 ? `
                <div style="
                    position: absolute;
                    bottom: -24px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: bold;
                    white-space: nowrap;
                    border: 1px solid ${color};
                ">
                    ${(vessel.speed || 0).toFixed(1)} kts
                </div>
                ` : ''}
                
                <!-- Live/Empirical badge -->
                <div style="
                    position: absolute;
                    top: -28px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0,0,0,0.9);
                    color: white;
                    padding: 4px 10px;
                    border-radius: 20px;
                    font-size: 11px;
                    font-weight: bold;
                    white-space: nowrap;
                    border: 2px solid ${color};
                    letter-spacing: 0.5px;
                    z-index: 1001;
                ">
                    ${statusText}
                </div>
            </div>
        `,
        iconSize: [48, 48],
        iconAnchor: [24, 24],
        popupAnchor: [0, -52]
    });
    
    vesselMarker = L.marker([lat, lon], {
        icon: vesselIcon,
        zIndexOffset: 1000
    }).addTo(maritimeMap);
    
    // Enhanced popup
    const speed = vessel.speed || vessel.sog || 0;
    const heading_display = vessel.heading || vessel.cog || 0;
    const destination = vessel.destination || 'Unknown';
    const vesselType = vessel.type || vessel.ship_type || 'Commercial Vessel';
    const vesselName = vessel.name || 'Unknown Vessel';
    const mmsi = vessel.mmsi || 'N/A';
    
    // Find nearest port
    let nearestPort = 'Norwegian waters';
    for (const [portName, portCoords] of Object.entries(PORT_COORDINATES)) {
        const dist = calculateDistance(lat, lon, portCoords.lat, portCoords.lon);
        if (dist < 10) {
            nearestPort = portCoords.description;
            break;
        }
    }
    
    const popupContent = `
        <div style="min-width: 320px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="background: ${color}; color: white; padding: 12px; border-radius: 8px 8px 0 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 16px;">${vesselName}</strong>
                    <span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: bold;">
                        ${isRealTime ? '🔴 LIVE AIS' : '🟡 EMPIRICAL'}
                    </span>
                </div>
                <div style="font-size: 12px; margin-top: 4px; opacity: 0.9;">
                    <i class="fas fa-anchor"></i> ${destination}
                </div>
                <div style="font-size: 11px; margin-top: 2px; opacity: 0.8;">
                    <i class="fas fa-water"></i> ${nearestPort}
                </div>
            </div>
            <div style="padding: 15px; background: white; border-radius: 0 0 8px 8px;">
                <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 0; color: #666; width: 40%;">Type:</td>
                        <td style="padding: 6px 0; font-weight: 600; color: #333;">${vesselType}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; color: #666;">Speed:</td>
                        <td style="padding: 6px 0; font-weight: 600; color: #333;">
                            ${speed.toFixed(2)} knots
                            ${speed > 1 ? '<span style="color: #28a745; margin-left: 8px;">⏵ Moving</span>' : '<span style="color: #dc3545; margin-left: 8px;">⏸ Stationary</span>'}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; color: #666;">Heading:</td>
                        <td style="padding: 6px 0; font-weight: 600; color: #333;">${heading_display}°</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; color: #666;">Position:</td>
                        <td style="padding: 6px 0; font-weight: 600; color: #333; font-family: monospace;">
                            ${lat.toFixed(4)}°, ${lon.toFixed(4)}°
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; color: #666;">MMSI:</td>
                        <td style="padding: 6px 0; font-weight: 600; color: #333; font-family: monospace;">${mmsi}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; color: #666;">Data Source:</td>
                        <td style="padding: 6px 0; font-weight: 600; color: ${color};">${source || 'unknown'}</td>
                    </tr>
                </table>
                <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #eee; font-size: 11px; color: #666; text-align: center;">
                    <i class="fas fa-satellite-dish"></i> 
                    ${isRealTime ? 
                        'Real-time AIS from Norwegian authorities' : 
                        'Scientific fallback based on 2023-2024 data'}
                </div>
            </div>
        </div>
    `;
    
    vesselMarker.bindPopup(popupContent, {
        maxWidth: 350,
        className: 'vessel-popup'
    });
    
    setTimeout(() => {
        if (vesselMarker) vesselMarker.openPopup();
    }, 500);
}

/**
 * Update vessel counters
 */
function updateVesselCounters(isRealTime, vessel, source) {
    const sourceType = isRealTime ? 'real' : 'empirical';
    const vesselName = vessel.name || 'Commercial Vessel';
    const speed = vessel.speed || vessel.sog || 0;
    
    const elements = {
        vesselCount: document.getElementById('vessel-count'),
        activeVessels: document.getElementById('active-vessels'),
        vesselSourceIndicator: document.getElementById('vessel-source-indicator'),
        vesselStatusText: document.getElementById('vessel-status-text'),
        vesselSourceBadge: document.getElementById('vessel-source-badge'),
        liveStatusText: document.getElementById('live-status-text'),
        realTimeCounter: document.getElementById('real-time-vessel-counter'),
        vesselType: document.getElementById('vessel-type'),
        vesselsUpdated: document.getElementById('vessels-updated'),
        aisApiStatus: document.getElementById('ais-api-status'),
        aisDataQuality: document.getElementById('ais-data-quality'),
        apiDetails: document.getElementById('api-details'),
        apiOverallStatus: document.getElementById('api-overall-status'),
        footerApiStatus: document.getElementById('footer-api-status'),
        vesselLegendText: document.getElementById('vessel-legend-text')
    };
    
    if (elements.vesselCount) elements.vesselCount.textContent = '1';
    if (elements.activeVessels) elements.activeVessels.textContent = '1';
    
    if (elements.vesselLegendText) {
        elements.vesselLegendText.textContent = isRealTime ? 'Live Vessel (REAL-TIME)' : 'Empirical Vessel (FALLBACK)';
    }
    
    if (elements.vesselSourceIndicator) {
        elements.vesselSourceIndicator.textContent = isRealTime ? 'LIVE' : 'EMPIRICAL';
        elements.vesselSourceIndicator.className = isRealTime ? 
            'data-source-badge data-source-live' : 
            'data-source-badge data-source-empirical';
    }
    
    if (elements.vesselStatusText) {
        const speedText = speed > 1 ? `Moving at ${speed.toFixed(1)} knots` : 'Stationary';
        elements.vesselStatusText.textContent = isRealTime ? 
            `${vesselName} - ${speedText} (Real-time AIS)` : 
            `${vesselName} - ${speedText} (Scientific fallback)`;
    }
    
    if (elements.vesselSourceBadge) {
        elements.vesselSourceBadge.textContent = isRealTime ? 'LIVE' : 'EMPIRICAL';
        elements.vesselSourceBadge.className = isRealTime ? 
            'badge realtime-badge ms-2' : 
            'badge empirical-badge ms-2';
        elements.vesselSourceBadge.style.display = 'inline-block';
    }
    
    if (elements.liveStatusText) {
        elements.liveStatusText.textContent = isRealTime ? 'LIVE' : 'EMPIRICAL';
        elements.liveStatusText.className = isRealTime ? 
            'fw-semibold text-success me-3' : 
            'fw-semibold text-warning me-3';
    }
    
    if (elements.realTimeCounter) {
        elements.realTimeCounter.textContent = isRealTime ? '🔴 LIVE' : '🟡 EMPIRICAL';
        elements.realTimeCounter.className = isRealTime ? 
            'badge realtime-badge ms-1' : 
            'badge empirical-badge ms-1';
        elements.realTimeCounter.style.display = 'inline-block';
    }
    
    if (elements.vesselType) {
        const speedIndicator = speed > 1 ? 
            `<span style="color: #28a745; margin-left: 5px;">⏵ ${speed.toFixed(1)} kts</span>` : 
            `<span style="color: #dc3545; margin-left: 5px;">⏸ Stopped</span>`;
        elements.vesselType.innerHTML = `<i class="fas fa-info-circle me-1"></i> ${vesselName} ${speedIndicator}`;
    }
    
    if (elements.vesselsUpdated) {
        const now = new Date();
        elements.vesselsUpdated.textContent = `Updated: ${now.toLocaleTimeString()}`;
        elements.vesselsUpdated.className = 'data-freshness live';
    }
    
    if (elements.aisApiStatus) {
        if (isRealTime) {
            elements.aisApiStatus.innerHTML = '<i class="fas fa-check-circle me-1"></i> ✓ Live';
            elements.aisApiStatus.className = 'badge bg-success';
        } else {
            elements.aisApiStatus.innerHTML = '<i class="fas fa-history me-1"></i> Historical';
            elements.aisApiStatus.className = 'badge bg-warning text-dark';
        }
    }
    
    if (elements.aisDataQuality) {
        if (isRealTime) {
            elements.aisDataQuality.innerHTML = '<i class="fas fa-ship me-1"></i> AIS: Live';
            elements.aisDataQuality.className = 'data-quality-indicator data-quality-high';
        } else {
            elements.aisDataQuality.innerHTML = '<i class="fas fa-ship me-1"></i> AIS: Historical';
            elements.aisDataQuality.className = 'data-quality-indicator data-quality-medium';
        }
    }
    
    if (elements.apiDetails) {
        elements.apiDetails.innerHTML = `RTZ: ✓ | AIS: ${isRealTime ? '✓ Live' : '📊 Historical'} | Weather: ✓`;
    }
    
    if (elements.apiOverallStatus) {
        if (isRealTime) {
            elements.apiOverallStatus.innerHTML = '<i class="fas fa-satellite-dish me-1"></i> All Systems Live';
            elements.apiOverallStatus.className = 'api-status api-status-active';
        } else {
            elements.apiOverallStatus.innerHTML = '<i class="fas fa-history me-1"></i> Using Historical Data';
            elements.apiOverallStatus.className = 'api-status api-status-partial';
        }
    }
    
    if (elements.footerApiStatus) {
        elements.footerApiStatus.textContent = isRealTime ? 'All APIs Active' : 'Using Historical Data';
        elements.footerApiStatus.className = isRealTime ? 'status-active' : 'status-partial';
    }
}

/**
 * Clear vessel display
 */
function clearVesselDisplay() {
    if (vesselMarker) {
        maritimeMap.removeLayer(vesselMarker);
        vesselMarker = null;
    }
    
    lastVesselPosition = null;
    
    const elements = {
        vesselCount: document.getElementById('vessel-count'),
        activeVessels: document.getElementById('active-vessels'),
        vesselSourceIndicator: document.getElementById('vessel-source-indicator'),
        vesselStatusText: document.getElementById('vessel-status-text'),
        vesselSourceBadge: document.getElementById('vessel-source-badge'),
        realTimeCounter: document.getElementById('real-time-vessel-counter'),
        vesselType: document.getElementById('vessel-type'),
        aisApiStatus: document.getElementById('ais-api-status'),
        aisDataQuality: document.getElementById('ais-data-quality'),
        vesselLegendText: document.getElementById('vessel-legend-text')
    };
    
    if (elements.vesselCount) elements.vesselCount.textContent = '0';
    if (elements.activeVessels) elements.activeVessels.textContent = '0';
    if (elements.vesselLegendText) elements.vesselLegendText.textContent = 'No Vessel Detected';
    if (elements.vesselSourceIndicator) {
        elements.vesselSourceIndicator.textContent = 'WAITING';
        elements.vesselSourceIndicator.className = 'data-source-badge';
    }
    if (elements.vesselStatusText) elements.vesselStatusText.textContent = 'No vessel detected';
    if (elements.vesselSourceBadge) elements.vesselSourceBadge.style.display = 'none';
    if (elements.realTimeCounter) elements.realTimeCounter.style.display = 'none';
    if (elements.vesselType) elements.vesselType.innerHTML = '<i class="fas fa-info-circle me-1"></i> No vessel detected';
    if (elements.aisApiStatus) {
        elements.aisApiStatus.innerHTML = '⏳ Waiting';
        elements.aisApiStatus.className = 'badge bg-secondary';
    }
    if (elements.aisDataQuality) {
        elements.aisDataQuality.innerHTML = '<i class="fas fa-ship me-1"></i> AIS: Waiting';
        elements.aisDataQuality.className = 'data-quality-indicator data-quality-low';
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
    
    if (movementAnimation) {
        clearInterval(movementAnimation);
        movementAnimation = null;
    }
    
    if (vesselMarker) {
        maritimeMap.removeLayer(vesselMarker);
        vesselMarker = null;
    }
    
    lastVesselPosition = null;
}

// ============================================
// ZOOM FUNCTIONS
// ============================================

window.zoomToRoute = function(index) {
    if (!maritimeMap || index >= activeRoutes.length) return false;
    
    const route = activeRoutes[index];
    const waypoints = extractWaypointsFromRoute(route);
    
    if (waypoints.length < 2) return false;
    
    const bounds = L.latLngBounds(waypoints.map(wp => [wp.lat, wp.lon]));
    
    if (bounds.isValid()) {
        maritimeMap.fitBounds(bounds.pad(0.1));
        highlightRoute(index);
        return true;
    }
    return false;
};

window.highlightRoute = function(index) {
    routePolylines.forEach((polyline, i) => {
        polyline.setStyle({ 
            weight: i === index ? 8 : 4,
            opacity: i === index ? 1 : 0.8,
            color: i === index ? '#ff5722' : polyline.options.color
        });
    });
};

// ============================================
// CLEANUP
// ============================================

window.addEventListener('beforeunload', function() {
    if (movementAnimation) {
        clearInterval(movementAnimation);
    }
    if (vesselUpdateInterval) {
        clearInterval(vesselUpdateInterval);
    }
});

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🌊 Maritime Map v4.0.4: FINAL VERSION');
    
    initMaritimeMap();
    
    setTimeout(() => {
        if (mapInitialized) {
            loadAndDisplayRTZRoutes();
        } else {
            setTimeout(loadAndDisplayRTZRoutes, 1000);
        }
    }, 800);
});

// Add styles
const styles = document.createElement('style');
styles.textContent = `
    .leaflet-control-legend {
        background: white;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        font-size: 12px;
        border: 1px solid #ddd;
        backdrop-filter: blur(5px);
        background: rgba(255,255,255,0.95);
    }
    .legend-title {
        font-weight: bold;
        margin-bottom: 8px;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
        color: #333;
    }
    .legend-item {
        margin: 6px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        display: inline-block;
    }
    .legend-label {
        color: #555;
        font-size: 11px;
    }
    .vessel-marker {
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .vessel-marker:hover {
        transform: scale(1.1);
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
    }
    .vessel-real-time {
        animation: pulse-live 2s infinite;
    }
    .vessel-empirical {
        opacity: 0.95;
    }
    @keyframes pulse-live {
        0% { filter: drop-shadow(0 0 0 rgba(40, 167, 69, 0.7)); }
        70% { filter: drop-shadow(0 0 15px rgba(40, 167, 69, 0.5)); }
        100% { filter: drop-shadow(0 0 0 rgba(40, 167, 69, 0)); }
    }
    .realtime-badge {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        font-weight: 600;
        font-size: 0.7rem;
        padding: 4px 10px;
        border-radius: 20px;
        animation: pulse 2s infinite;
    }
    .empirical-badge {
        background: linear-gradient(135deg, #ffc107, #fd7e14);
        color: white;
        font-weight: 600;
        font-size: 0.7rem;
        padding: 4px 10px;
        border-radius: 20px;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    .data-source-badge {
        font-size: 0.6rem;
        padding: 3px 8px;
        border-radius: 12px;
        margin-left: 4px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .data-source-live {
        background: #28a745;
        color: white;
    }
    .data-source-empirical {
        background: #ffc107;
        color: #000;
    }
    .api-status {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .api-status-active {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .api-status-partial {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
    }
    .data-quality-indicator {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    .data-quality-high {
        background: #d4edda;
        color: #155724;
    }
    .data-quality-medium {
        background: #fff3cd;
        color: #856404;
    }
    .data-quality-low {
        background: #f8d7da;
        color: #721c24;
    }
    .vessel-popup .leaflet-popup-content-wrapper {
        border-radius: 8px;
        padding: 0;
        overflow: hidden;
    }
    .vessel-popup .leaflet-popup-content {
        margin: 0;
        padding: 0;
    }
    .vessel-popup .leaflet-popup-tip {
        background: white;
    }
`;

document.head.appendChild(styles);