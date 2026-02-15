// save as backend/static/js/split/scientific_norwegian_routes.js
// SCIENTIFIC NORWEGIAN COASTAL ROUTES DISPLAY
// Uses real GPS coordinates with mathematical precision

console.log('🔬 Loading Scientific Norwegian Route Display...');

// Scientific constants for maritime navigation
const EARTH_RADIUS_KM = 6371.0;
const NAUTICAL_MILE_KM = 1.852;
const DEG_TO_RAD = Math.PI / 180;
const RAD_TO_DEG = 180 / Math.PI;

/**
 * Haversine formula for great-circle distance between two points
 * @param {number} lat1 - Latitude of point 1 (degrees)
 * @param {number} lon1 - Longitude of point 1 (degrees)
 * @param {number} lat2 - Latitude of point 2 (degrees)
 * @param {number} lon2 - Longitude of point 2 (degrees)
 * @returns {Object} Distance in km and nautical miles
 */
function calculateGreatCircleDistance(lat1, lon1, lat2, lon2) {
    const φ1 = lat1 * DEG_TO_RAD;
    const φ2 = lat2 * DEG_TO_RAD;
    const Δφ = (lat2 - lat1) * DEG_TO_RAD;
    const Δλ = (lon2 - lon1) * DEG_TO_RAD;
    
    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distanceKm = EARTH_RADIUS_KM * c;
    const distanceNm = distanceKm / NAUTICAL_MILE_KM;
    
    return {
        kilometers: distanceKm,
        nauticalMiles: distanceNm,
        precise: true
    };
}

/**
 * Calculate initial bearing (forward azimuth) between two points
 * @param {number} lat1 - Starting latitude
 * @param {number} lon1 - Starting longitude
 * @param {number} lat2 - Destination latitude
 * @param {number} lon2 - Destination longitude
 * @returns {number} Bearing in degrees from north (0° = N, 90° = E)
 */
function calculateInitialBearing(lat1, lon1, lat2, lon2) {
    const φ1 = lat1 * DEG_TO_RAD;
    const φ2 = lat2 * DEG_TO_RAD;
    const λ1 = lon1 * DEG_TO_RAD;
    const λ2 = lon2 * DEG_TO_RAD;
    
    const y = Math.sin(λ2 - λ1) * Math.cos(φ2);
    const x = Math.cos(φ1) * Math.sin(φ2) -
              Math.sin(φ1) * Math.cos(φ2) * Math.cos(λ2 - λ1);
    
    let bearing = Math.atan2(y, x);
    bearing = bearing * RAD_TO_DEG;
    bearing = (bearing + 360) % 360;
    
    return Math.round(bearing * 100) / 100;
}

/**
 * Calculate intermediate point along a great circle path
 * @param {number} lat1 - Start latitude
 * @param {number} lon1 - Start longitude
 * @param {number} lat2 - End latitude
 * @param {number} lon2 - End longitude
 * @param {number} fraction - Fraction of distance (0-1)
 * @returns {Object} Intermediate coordinates
 */
function calculateIntermediatePoint(lat1, lon1, lat2, lon2, fraction) {
    const φ1 = lat1 * DEG_TO_RAD;
    const λ1 = lon1 * DEG_TO_RAD;
    const φ2 = lat2 * DEG_TO_RAD;
    const λ2 = lon2 * DEG_TO_RAD;
    
    // Angular distance
    const Δ = calculateGreatCircleDistance(lat1, lon1, lat2, lon2).kilometers / EARTH_RADIUS_KM;
    
    const a = Math.sin((1 - fraction) * Δ) / Math.sin(Δ);
    const b = Math.sin(fraction * Δ) / Math.sin(Δ);
    
    const x = a * Math.cos(φ1) * Math.cos(λ1) + b * Math.cos(φ2) * Math.cos(λ2);
    const y = a * Math.cos(φ1) * Math.sin(λ1) + b * Math.cos(φ2) * Math.sin(λ2);
    const z = a * Math.sin(φ1) + b * Math.sin(φ2);
    
    const φi = Math.atan2(z, Math.sqrt(x*x + y*y));
    const λi = Math.atan2(y, x);
    
    return {
        lat: φi * RAD_TO_DEG,
        lon: λi * RAD_TO_DEG,
        fraction: fraction
    };
}

/**
 * Calculate total route distance with scientific precision
 * @param {Array} waypoints - Array of {lat, lon} objects
 * @returns {Object} Total distance metrics
 */
function calculateRouteDistance(waypoints) {
    if (!waypoints || waypoints.length < 2) {
        return { totalKm: 0, totalNm: 0, legs: [] };
    }
    
    let totalKm = 0;
    let totalNm = 0;
    const legs = [];
    
    for (let i = 0; i < waypoints.length - 1; i++) {
        const wp1 = waypoints[i];
        const wp2 = waypoints[i + 1];
        
        const distance = calculateGreatCircleDistance(wp1.lat, wp1.lon, wp2.lat, wp2.lon);
        const bearing = calculateInitialBearing(wp1.lat, wp1.lon, wp2.lat, wp2.lon);
        
        totalKm += distance.kilometers;
        totalNm += distance.nauticalMiles;
        
        legs.push({
            from: i + 1,
            to: i + 2,
            distanceKm: distance.kilometers,
            distanceNm: distance.nauticalMiles,
            bearing: bearing,
            startPoint: { lat: wp1.lat, lon: wp1.lon, name: wp1.name || `Waypoint ${i+1}` },
            endPoint: { lat: wp2.lat, lon: wp2.lon, name: wp2.name || `Waypoint ${i+2}` }
        });
    }
    
    return {
        totalKm: totalKm,
        totalNm: totalNm,
        legs: legs,
        waypointCount: waypoints.length,
        legCount: legs.length,
        averageLegLengthNm: legs.length > 0 ? totalNm / legs.length : 0
    };
}

/**
 * Create scientific marker with precise navigation data
 * @param {Object} waypoint - Waypoint data
 * @param {string} type - 'start', 'end', or 'waypoint'
 * @param {number} sequence - Sequence number
 * @returns {L.DivIcon} Leaflet marker icon
 */
function createScientificMarker(waypoint, type = 'waypoint', sequence = 1) {
    const colors = {
        start: '#00FF00', // Green for start
        end: '#FF0000',   // Red for end
        waypoint: '#1E90FF' // Dodger Blue for waypoints
    };
    
    const symbols = {
        start: '⛵', // Ship
        end: '⚓',   // Anchor
        waypoint: '●' // Dot
    };
    
    const size = {
        start: 32,
        end: 32,
        waypoint: 24
    };
    
    const color = colors[type] || colors.waypoint;
    const symbol = symbols[type] || symbols.waypoint;
    
    return L.divIcon({
        className: 'scientific-marker',
        html: `
            <div style="
                background: ${color};
                color: white;
                width: ${size[type]}px;
                height: ${size[type]}px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: ${type === 'waypoint' ? '12px' : '14px'};
                position: relative;
            ">
                ${type === 'waypoint' ? sequence : symbol}
                ${type !== 'waypoint' ? `
                    <div style="
                        position: absolute;
                        top: -20px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: white;
                        color: #333;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 10px;
                        white-space: nowrap;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                    ">
                        ${type.toUpperCase()}
                    </div>
                ` : ''}
            </div>
        `,
        iconSize: [size[type] + 10, size[type] + 10],
        iconAnchor: [size[type]/2 + 5, size[type]/2 + 5],
        popupAnchor: [0, -size[type]/2 - 5]
    });
}

/**
 * Create precise polyline with scientific styling
 * @param {Array} waypoints - Array of coordinates
 * @param {string} color - Line color
 * @param {Object} routeInfo - Route information
 * @returns {L.Polyline} Leaflet polyline
 */
function createScientificPolyline(waypoints, color, routeInfo) {
    // Convert waypoints to LatLng array
    const latLngs = waypoints.map(wp => [wp.lat, wp.lon]);
    
    // Calculate distance for line weight
    const totalDistance = calculateRouteDistance(waypoints).totalNm;
    const weight = Math.min(Math.max(totalDistance / 50, 2), 6); // Scale with distance
    
    // Create polyline with scientific properties
    return L.polyline(latLngs, {
        color: color,
        weight: weight,
        opacity: 0.8,
        lineCap: 'round',
        lineJoin: 'round',
        className: 'scientific-route-line',
        dashArray: routeInfo && routeInfo.empirically_verified ? null : '5, 10'
    });
}

/**
 * Display route with scientific precision
 * @param {Object} route - Route data from API
 * @param {number} index - Route index
 * @param {L.Map} map - Leaflet map
 */
function displayScientificRoute(route, index, map) {
    try {
        console.log(`🔬 Displaying route ${index + 1}: ${route.route_name}`);
        
        // Get waypoints for this route
        fetch(`/nca/api/nca/route/${encodeURIComponent(route.route_name)}/waypoints`)
            .then(response => response.json())
            .then(data => {
                if (!data.success || !data.waypoints) {
                    console.log(`No waypoints for ${route.route_name}`);
                    return;
                }
                
                const waypoints = data.waypoints;
                console.log(`📊 ${route.route_name}: ${waypoints.length} waypoints loaded`);
                
                // Calculate scientific metrics
                const distanceMetrics = calculateRouteDistance(waypoints);
                
                // Choose color based on route characteristics
                const colors = ['#1e88e5', '#43a047', '#fb8c00', '#e53935', '#8e24aa'];
                const color = colors[index % colors.length];
                
                // Create polyline
                const polyline = createScientificPolyline(waypoints, color, route);
                polyline.addTo(map);
                
                // Add start marker (exact first waypoint)
                if (waypoints.length > 0) {
                    const startMarker = L.marker(
                        [waypoints[0].lat, waypoints[0].lon],
                        { icon: createScientificMarker(waypoints[0], 'start', 1) }
                    ).addTo(map);
                    
                    startMarker.bindPopup(`
                        <div style="min-width: 250px;">
                            <h6 style="color: ${color}; margin-bottom: 10px;">
                                ⛵ ${route.clean_name || route.route_name}
                            </h6>
                            <table class="table table-sm">
                                <tr><td><strong>Start Point:</strong></td><td>${waypoints[0].name || 'Waypoint 1'}</td></tr>
                                <tr><td><strong>Coordinates:</strong></td><td>${waypoints[0].lat.toFixed(6)}°, ${waypoints[0].lon.toFixed(6)}°</td></tr>
                                <tr><td><strong>Sequence:</strong></td><td>1/${waypoints.length}</td></tr>
                                <tr><td><strong>Route:</strong></td><td>${route.origin || 'Unknown'} → ${route.destination || 'Unknown'}</td></tr>
                            </table>
                        </div>
                    `);
                }
                
                // Add end marker (exact last waypoint)
                if (waypoints.length > 1) {
                    const endMarker = L.marker(
                        [waypoints[waypoints.length - 1].lat, waypoints[waypoints.length - 1].lon],
                        { icon: createScientificMarker(waypoints[waypoints.length - 1], 'end', waypoints.length) }
                    ).addTo(map);
                    
                    endMarker.bindPopup(`
                        <div style="min-width: 250px;">
                            <h6 style="color: ${color}; margin-bottom: 10px;">
                                ⚓ ${route.clean_name || route.route_name}
                            </h6>
                            <table class="table table-sm">
                                <tr><td><strong>End Point:</strong></td><td>${waypoints[waypoints.length - 1].name || 'Final Waypoint'}</td></tr>
                                <tr><td><strong>Coordinates:</strong></td><td>${waypoints[waypoints.length - 1].lat.toFixed(6)}°, ${waypoints[waypoints.length - 1].lon.toFixed(6)}°</td></tr>
                                <tr><td><strong>Sequence:</strong></td><td>${waypoints.length}/${waypoints.length}</td></tr>
                                <tr><td><strong>Total Distance:</strong></td><td>${distanceMetrics.totalNm.toFixed(1)} NM</td></tr>
                                <tr><td><strong>Waypoints:</strong></td><td>${waypoints.length}</td></tr>
                            </table>
                        </div>
                    `);
                }
                
                // Add key waypoint markers (every 5th waypoint for readability)
                const keyWaypoints = waypoints.filter((wp, i) => 
                    i === 0 || 
                    i === waypoints.length - 1 || 
                    i % 5 === 0
                );
                
                keyWaypoints.forEach((wp, i) => {
                    if (i === 0 || i === keyWaypoints.length - 1) return; // Skip start/end
                    
                    const marker = L.marker(
                        [wp.lat, wp.lon],
                        { icon: createScientificMarker(wp, 'waypoint', wp.id) }
                    ).addTo(map);
                    
                    marker.bindPopup(`
                        <div style="min-width: 220px;">
                            <h6 style="color: ${color}; margin-bottom: 10px;">
                                ● ${wp.name || `Waypoint ${wp.id}`}
                            </h6>
                            <table class="table table-sm">
                                <tr><td><strong>Coordinates:</strong></td><td>${wp.lat.toFixed(6)}°, ${wp.lon.toFixed(6)}°</td></tr>
                                <tr><td><strong>Sequence:</strong></td><td>${wp.id}/${waypoints.length}</td></tr>
                                <tr><td><strong>Route Segment:</strong></td><td>${Math.floor(wp.id/waypoints.length * 100)}% complete</td></tr>
                            </table>
                        </div>
                    `);
                });
                
                // Create scientific popup for the polyline
                const scientificPopup = createScientificPopup(route, waypoints, distanceMetrics, color);
                polyline.bindPopup(scientificPopup);
                
                console.log(`✅ Route ${index + 1} displayed with ${waypoints.length} precise waypoints`);
                
            })
            .catch(error => {
                console.error(`Error loading waypoints for ${route.route_name}:`, error);
            });
            
    } catch (error) {
        console.error(`Error displaying route ${index + 1}:`, error);
    }
}

/**
 * Create scientific popup with detailed navigation data
 */
function createScientificPopup(route, waypoints, distanceMetrics, color) {
    const startWp = waypoints[0];
    const endWp = waypoints[waypoints.length - 1];
    
    // Calculate bearing from start to end
    const initialBearing = calculateInitialBearing(startWp.lat, startWp.lon, endWp.lat, endWp.lon);
    
    // Calculate average leg length
    const avgLegLength = distanceMetrics.legs.length > 0 
        ? distanceMetrics.totalNm / distanceMetrics.legs.length 
        : 0;
    
    return `
        <div style="min-width: 280px; font-family: 'Segoe UI', sans-serif;">
            <div style="background: linear-gradient(135deg, ${color}40, ${color}20); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h5 style="margin: 0; color: ${color};">
                    <i class="fas fa-ship"></i> ${route.clean_name || route.route_name}
                </h5>
                <p style="margin: 5px 0 0 0; font-size: 14px;">
                    ${route.origin || 'Unknown'} → ${route.destination || 'Unknown'}
                </p>
            </div>
            
            <div style="margin-bottom: 15px;">
                <h6 style="color: #333; border-bottom: 2px solid ${color}; padding-bottom: 5px;">
                    <i class="fas fa-ruler-combined"></i> Scientific Metrics
                </h6>
                <table class="table table-sm" style="font-size: 13px;">
                    <tr>
                        <td><strong>Total Distance:</strong></td>
                        <td><span style="color: ${color}; font-weight: bold;">${distanceMetrics.totalNm.toFixed(1)} NM</span></td>
                    </tr>
                    <tr>
                        <td><strong>Waypoints:</strong></td>
                        <td>${waypoints.length} precise points</td>
                    </tr>
                    <tr>
                        <td><strong>Navigation Legs:</strong></td>
                        <td>${distanceMetrics.legs.length}</td>
                    </tr>
                    <tr>
                        <td><strong>Avg Leg Length:</strong></td>
                        <td>${avgLegLength.toFixed(1)} NM</td>
                    </tr>
                    <tr>
                        <td><strong>Initial Bearing:</strong></td>
                        <td>${initialBearing}° from N</td>
                    </tr>
                </table>
            </div>
            
            <div style="margin-bottom: 15px;">
                <h6 style="color: #333; border-bottom: 2px solid ${color}; padding-bottom: 5px;">
                    <i class="fas fa-map-marker-alt"></i> Key Waypoints
                </h6>
                <div style="max-height: 150px; overflow-y: auto; font-size: 12px;">
                    ${waypoints.filter((wp, i) => i === 0 || i === waypoints.length - 1 || i % 10 === 0)
                        .map(wp => `
                            <div style="padding: 3px 0; border-bottom: 1px solid #eee;">
                                <strong>${wp.id}.</strong> ${wp.name || 'Waypoint'} 
                                <span style="color: #666; font-family: monospace;">
                                    (${wp.lat.toFixed(4)}°, ${wp.lon.toFixed(4)}°)
                                </span>
                            </div>
                        `).join('')}
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 11px; color: #666;">
                <i class="fas fa-info-circle"></i>
                <strong>Data Source:</strong> Norwegian Coastal Administration<br>
                <strong>Precision:</strong> GPS coordinates to 6 decimal places (~10 cm)<br>
                <strong>Method:</strong> Great-circle navigation (Haversine)
            </div>
        </div>
    `;
}

/**
 * Main function to load and display scientific Norwegian routes
 */
async function loadScientificNorwegianRoutes() {
    console.log('🔬 Loading scientific Norwegian coastal routes...');
    
    try {
        // Fetch route metadata from NCA API
        const response = await fetch('/nca/api/nca/routes');
        if (!response.ok) {
            throw new Error(`NCA API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success || !data.routes) {
            throw new Error('NCA API returned no routes');
        }
        
        console.log(`📊 Scientific analysis: ${data.total_routes} routes, ${data.total_waypoints} waypoints`);
        
        // Get map instance
        const map = window.maritimeMap || window.map;
        if (!map) {
            console.error('Map not initialized');
            return;
        }
        
        // Display each route with scientific precision
        console.log(`🗺️ Displaying ${Math.min(data.routes.length, 10)} routes with scientific precision...`);
        
        // Display first 10 routes for performance
        const routesToDisplay = data.routes.slice(0, Math.min(10, data.routes.length));
        
        routesToDisplay.forEach((route, index) => {
            setTimeout(() => {
                displayScientificRoute(route, index, map);
            }, index * 500); // Stagger loading for better UX
        });
        
        console.log(`✅ Scientific route display initiated for ${routesToDisplay.length} routes`);
        
        // Update dashboard with scientific metrics
        updateScientificDashboard(data);
        
    } catch (error) {
        console.error('❌ Scientific route loading failed:', error);
        
        // Fallback to standard display
        if (typeof loadRealNCARoutes === 'function') {
            console.log('🔄 Falling back to standard NCA routes...');
            loadRealNCARoutes();
        }
    }
}

/**
 * Update dashboard with scientific information
 */
function updateScientificDashboard(data) {
    const badge = document.getElementById('data-truth-badge');
    if (badge) {
        badge.innerHTML = `
            <i class="fas fa-microscope me-1"></i>
            <span id="route-count-badge">${data.total_routes}</span> Scientific Routes
            <span class="badge bg-success ms-1">
                <i class="fas fa-dna"></i> ${data.total_waypoints.toLocaleString()} Waypoints
            </span>
        `;
    }
    
    // Add scientific info to dashboard
    const dashboardHeader = document.querySelector('.dashboard-header');
    if (dashboardHeader && !document.getElementById('scientific-info')) {
        const scientificInfo = document.createElement('div');
        scientificInfo.id = 'scientific-info';
        scientificInfo.className = 'alert alert-info mt-3';
        scientificInfo.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-microscope me-3 fa-2x"></i>
                <div>
                    <strong>Scientific Route Analysis Active</strong>
                    <p class="mb-0 small">
                        Displaying <strong>${data.total_routes}</strong> Norwegian coastal routes with 
                        <strong>${data.total_waypoints.toLocaleString()}</strong> GPS waypoints.
                        <br>
                        <span class="text-success">
                            <i class="fas fa-check-circle"></i> Great-circle navigation • Haversine formula • Precise bearings
                        </span>
                    </p>
                </div>
            </div>
        `;
        dashboardHeader.appendChild(scientificInfo);
    }
}

/**
 * Initialize scientific routes when page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔬 Scientific Norwegian Routes module loaded');
    
    // Wait for map to be ready
    const checkMapInterval = setInterval(() => {
        if (window.maritimeMap || window.map) {
            clearInterval(checkMapInterval);
            
            // Load scientific routes after 3 seconds
            setTimeout(() => {
                loadScientificNorwegianRoutes();
            }, 3000);
        }
    }, 500);
});

// CSS for scientific display
const scientificStyles = `
    .scientific-marker {
        background: transparent;
        border: none;
    }
    
    .scientific-route-line {
        cursor: pointer;
        transition: stroke-width 0.3s;
    }
    
    .scientific-route-line:hover {
        stroke-width: 8;
        opacity: 1;
    }
    
    .scientific-popup {
        min-width: 300px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .scientific-popup h5 {
        color: #1a73e8;
        margin-bottom: 15px;
    }
    
    .scientific-popup table {
        font-size: 13px;
    }
    
    .scientific-popup table tr:hover {
        background-color: #f8f9fa;
    }
`;

// Add styles to document
if (document && !document.getElementById('scientific-styles')) {
    const styleElement = document.createElement('style');
    styleElement.id = 'scientific-styles';
    styleElement.textContent = scientificStyles;
    document.head.appendChild(styleElement);
}

// Export for global use
window.loadScientificNorwegianRoutes = loadScientificNorwegianRoutes;
window.displayScientificRoute = displayScientificRoute;