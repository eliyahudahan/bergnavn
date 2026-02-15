// backend/static/js/split/rtz_waypoints.js
/**
 * RTZ Waypoints Display Module - Enhanced Integration Version
 * Shows all waypoints for RTZ routes on the map with dashboard controls integration
 * Features: Clear start/end points, route highlighting, proper integration with dashboard
 * 
 * FIXED: CRITICAL - Waypoints are stored with numeric keys (0,1,2...) not route-0
 * FIXED: Proper detection of waypoints from DOM using route.index
 * FIXED: Auto-drawing when data is loaded
 * FIXED: getRouteColor handles undefined route.source_city and missing routeColorMap
 */

class RTZWaypoints {
    constructor(map) {
        this.map = map;
        this.waypointsLayer = L.layerGroup();
        this.routesLayer = L.layerGroup();
        this.isVisible = true;
        this.waypointMarkers = {};
        this.routeLines = {};
        this.waypointsData = {}; // Store waypoints for external access
        this.routesData = []; // Store routes for external access
        
        console.log('📍 RTZ Waypoints module initialized - Enhanced Integration Version');
        
        // Define color groups for different source cities
        this.routeColorMap = {
            'bergen': '#3498db',      // Blue
            'oslo': '#2ecc71',        // Green
            'trondheim': '#e74c3c',   // Red
            'stavanger': '#f39c12',   // Orange
            'alesund': '#9b59b6',     // Purple
            'kristiansand': '#1abc9c', // Teal
            'drammen': '#d35400',     // Dark Orange
            'sandefjord': '#27ae60',  // Dark Green
            'flekkefjord': '#8e44ad', // Violet
            'andalsnes': '#16a085'    // Sea Green
        };
        
        this.defaultRouteColor = '#3498db';
        
        // Load waypoints from DOM
        this.loadWaypointsFromDOM();
        
        // Load routes from dashboardData
        this.loadRoutesFromDashboard();
    }
    
    /**
     * Load waypoints from DOM element
     */
    loadWaypointsFromDOM() {
        const waypointsElement = document.getElementById('waypoints-data');
        if (waypointsElement && waypointsElement.textContent) {
            try {
                const data = JSON.parse(waypointsElement.textContent);
                console.log('📍 Loaded waypoints from DOM:', Object.keys(data).length, 'routes');
                console.log('📍 Sample keys:', Object.keys(data).slice(0, 5));
                
                // Store directly - data has numeric keys (0, 1, 2...)
                this.waypointsData = data;
                
                // Auto-draw if routes are already loaded
                if (this.routesData.length > 0) {
                    console.log('🎯 Auto-drawing with waypoints...');
                    setTimeout(() => {
                        this.drawMultipleRoutes(this.routesData);
                    }, 500);
                }
                
                return true;
            } catch (e) {
                console.error('❌ Failed to parse waypoints:', e);
            }
        }
        console.log('⚠️ No waypoints found in DOM');
        return false;
    }
    
    /**
     * Load routes from window.dashboardData
     */
    loadRoutesFromDashboard() {
        if (window.dashboardData && window.dashboardData.routes) {
            this.routesData = window.dashboardData.routes;
            console.log(`📍 Loaded ${this.routesData.length} routes from dashboardData`);
            
            // Auto-draw if we have waypoints
            if (this.routesData.length > 0 && Object.keys(this.waypointsData).length > 0) {
                console.log('🎯 Auto-drawing routes with waypoints...');
                this.drawMultipleRoutes(this.routesData);
            }
            return true;
        }
        
        console.log('⚠️ No routes in dashboardData yet, waiting...');
        
        // Try again in a moment
        setTimeout(() => {
            if (window.dashboardData && window.dashboardData.routes && this.routesData.length === 0) {
                this.routesData = window.dashboardData.routes;
                console.log(`📍 Loaded ${this.routesData.length} routes from dashboardData (delayed)`);
                
                if (this.routesData.length > 0 && Object.keys(this.waypointsData).length > 0) {
                    console.log('🎯 Auto-drawing routes from dashboardData (delayed)...');
                    this.drawMultipleRoutes(this.routesData);
                }
            }
        }, 1000);
        
        return false;
    }
    
    /**
     * Draw complete route with waypoints
     */
    drawCompleteRoute(route, routeId) {
        console.log(`🎨 Drawing route ${routeId}, index: ${route.index}`);
        
        // Try to get waypoints from various sources
        let waypoints = [];
        
        // CRITICAL: The waypoints are stored with NUMERIC keys (0, 1, 2...)
        // Source 1: Try by index from the routesData array (MOST RELIABLE)
        if (route.index !== undefined && this.waypointsData[route.index] && 
            Array.isArray(this.waypointsData[route.index]) && 
            this.waypointsData[route.index].length > 0) {
            waypoints = this.waypointsData[route.index];
            console.log(`✅ Found waypoints at route.index ${route.index}: ${waypoints.length} waypoints`);
        }
        // Source 2: Try numeric key extracted from routeId
        else {
            const numericId = routeId.replace('route-', '');
            if (this.waypointsData[numericId] && 
                Array.isArray(this.waypointsData[numericId]) && 
                this.waypointsData[numericId].length > 0) {
                waypoints = this.waypointsData[numericId];
                console.log(`✅ Found waypoints at key "${numericId}": ${waypoints.length} waypoints`);
            }
            // Source 3: Try original routeId as fallback
            else if (this.waypointsData[routeId] && 
                     Array.isArray(this.waypointsData[routeId]) && 
                     this.waypointsData[routeId].length > 0) {
                waypoints = this.waypointsData[routeId];
                console.log(`✅ Found waypoints at key "${routeId}": ${waypoints.length} waypoints`);
            }
            // Source 4: Try route.waypoints
            else if (route.waypoints && 
                     Array.isArray(route.waypoints) && 
                     route.waypoints.length > 0) {
                waypoints = route.waypoints;
                console.log(`✅ Using route.waypoints: ${waypoints.length} waypoints`);
            }
        }
        
        if (waypoints.length === 0) {
            console.log(`⚠️ No waypoints found for route ${routeId} (index: ${route.index})`);
            return;
        }
        
        console.log(`📍 Drawing route ${routeId} with ${waypoints.length} waypoints`);
        
        // Store waypoints data for external access
        this.waypointsData[routeId] = waypoints;
        
        // Create a route object with waypoints
        const routeWithWaypoints = {
            ...route,
            waypoints: waypoints
        };
        
        // Get route color based on source city - with safety checks
        const routeColor = this.getRouteColor(route);
        // Source city for CSS class - use empty string if missing
        const sourceCity = route.source_city ? route.source_city.toLowerCase() : 'unknown';
        
        // Clear previous markers for this route
        this.clearRouteWaypoints(routeId);
        
        // Store markers for this route
        this.waypointMarkers[routeId] = [];
        
        // Draw route line
        this.drawRouteLine(routeWithWaypoints, routeId, routeColor, sourceCity);
        
        // Draw all waypoints
        waypoints.forEach((waypoint, index) => {
            if (waypoint && waypoint.lat !== undefined && waypoint.lon !== undefined) {
                const marker = this.createWaypointMarker(waypoint, index, routeWithWaypoints, routeId, routeColor);
                marker.addTo(this.waypointsLayer);
                this.waypointMarkers[routeId].push(marker);
            }
        });
        
        // Add route layer to map if visible
        if (this.isVisible) {
            this.waypointsLayer.addTo(this.map);
            this.routesLayer.addTo(this.map);
        }
    }
    
    /**
     * Draw route line
     */
    drawRouteLine(route, routeId, color, sourceCity) {
        const waypoints = route.waypoints || [];
        if (waypoints.length < 2) return;
        
        // Create polyline
        const points = waypoints.map(wp => [wp.lat, wp.lon]);
        const polyline = L.polyline(points, {
            color: color,
            weight: 4,
            opacity: 0.85,
            lineCap: 'round',
            lineJoin: 'round',
            className: `rtz-route-line route-group-${sourceCity}`
        });
        
        // Add to routes layer
        polyline.addTo(this.routesLayer);
        
        // Store reference
        this.routeLines[routeId] = polyline;
        
        // Store original color for resetting highlights
        polyline.options.originalColor = color;
        
        // Add popup with route info
        this.addRoutePopup(polyline, route, routeId, color);
        
        // Add hover effect
        polyline.on('mouseover', function(e) {
            this.setStyle({
                weight: 6,
                opacity: 1
            });
        });
        
        polyline.on('mouseout', function(e) {
            this.setStyle({
                weight: 4,
                opacity: 0.85
            });
        });
        
        // Add click handler
        polyline.on('click', (e) => {
            this.highlightRoute(routeId);
            this.showRouteDetails(route, routeId, color);
        });
    }
    
    /**
     * Create waypoint marker - NO BLINKING, CLEAR VISIBILITY
     */
    createWaypointMarker(waypoint, index, route, routeId, routeColor) {
        const isStartPoint = index === 0;
        const isEndPoint = index === route.waypoints.length - 1;
        
        let marker;
        
        if (isStartPoint) {
            // Start marker - green, permanent
            marker = L.circleMarker([waypoint.lat, waypoint.lon], {
                radius: 10,
                color: '#2ecc71',
                weight: 3,
                opacity: 1,
                fillColor: '#2ecc71',
                fillOpacity: 0.9,
                className: 'rtz-start-marker'
            });
        } else if (isEndPoint) {
            // End marker - red, permanent
            marker = L.circleMarker([waypoint.lat, waypoint.lon], {
                radius: 10,
                color: '#e74c3c',
                weight: 3,
                opacity: 1,
                fillColor: '#e74c3c',
                fillOpacity: 0.9,
                className: 'rtz-end-marker'
            });
        } else {
            // Regular waypoint - based on importance
            const isImportant = this.isImportantWaypoint(index, route.waypoints.length);
            marker = L.circleMarker([waypoint.lat, waypoint.lon], {
                radius: isImportant ? 8 : 6,
                color: isImportant ? '#f39c12' : routeColor,
                weight: isImportant ? 2 : 1.5,
                opacity: 0.9,
                fillColor: isImportant ? '#f39c12' : '#95a5a6',
                fillOpacity: 0.7,
                className: isImportant ? 'rtz-waypoint-important' : 'rtz-waypoint-regular'
            });
        }
        
        // Add tooltip
        const waypointName = this.getWaypointName(waypoint, index, route);
        const routeDisplayName = this.getRouteDisplayName(route, routeId);
        
        let tooltipContent = `<div style="font-size: 12px; max-width: 200px;">`;
        if (isStartPoint) {
            tooltipContent += `<strong>🚢 START: ${waypointName}</strong><br/>`;
        } else if (isEndPoint) {
            tooltipContent += `<strong>🏁 END: ${waypointName}</strong><br/>`;
        } else {
            tooltipContent += `<strong>📍 ${waypointName}</strong><br/>`;
        }
        tooltipContent += `<small>Route: ${routeDisplayName}</small><br/>`;
        tooltipContent += `<small>Position: ${waypoint.lat.toFixed(5)}°, ${waypoint.lon.toFixed(5)}°</small>`;
        tooltipContent += `</div>`;
        
        marker.bindTooltip(tooltipContent);
        
        // Add click handler
        marker.on('click', (e) => {
            this.highlightWaypoint(routeId, index);
            this.showWaypointDetails(waypoint, index, route, routeId);
        });
        
        // Add hover effect (no blinking)
        marker.on('mouseover', function(e) {
            const currentRadius = this.options.radius;
            this.setStyle({
                radius: currentRadius * 1.4,
                weight: 3
            });
        });
        
        marker.on('mouseout', function(e) {
            const originalRadius = isStartPoint || isEndPoint ? 10 : (this.options.className === 'rtz-waypoint-important' ? 8 : 6);
            this.setStyle({
                radius: originalRadius,
                weight: isStartPoint || isEndPoint ? 3 : (this.options.className === 'rtz-waypoint-important' ? 2 : 1.5)
            });
        });
        
        return marker;
    }
    
    /**
     * Add popup to route line
     */
    addRoutePopup(polyline, route, routeId, color) {
        const popupContent = this.createRoutePopup(route, routeId, color);
        polyline.bindPopup(popupContent, {
            className: 'route-popup',
            maxWidth: 350
        });
    }
    
    /**
     * Create route popup content
     */
    createRoutePopup(route, routeId, color) {
        const waypointCount = route.waypoints ? route.waypoints.length : 0;
        const sourceCity = route.source_city || 'Unknown';
        const routeName = this.getRouteDisplayName(route, routeId);
        
        return `
            <div class="route-popup">
                <div class="route-popup-header" style="background: ${color};">
                    <span><i class="fas fa-route"></i> ${routeName}</span>
                    <span style="font-size: 0.8em; opacity: 0.9;">${sourceCity}</span>
                </div>
                <div class="route-popup-body">
                    <div class="route-info-item">
                        <span class="route-info-label"><i class="fas fa-ship"></i> Source:</span>
                        <span class="route-info-value">${sourceCity}</span>
                    </div>
                    <div class="route-info-item">
                        <span class="route-info-label"><i class="fas fa-map-marker-alt"></i> Waypoints:</span>
                        <span class="route-info-value">${waypointCount}</span>
                    </div>
                    <div class="route-info-item">
                        <span class="route-info-label"><i class="fas fa-flag"></i> Start:</span>
                        <span class="route-info-value">${route.origin || 'Unknown'}</span>
                    </div>
                    <div class="route-info-item">
                        <span class="route-info-label"><i class="fas fa-flag-checkered"></i> End:</span>
                        <span class="route-info-value">${route.destination || 'Unknown'}</span>
                    </div>
                    ${route.total_distance_nm ? `
                    <div class="route-info-item">
                        <span class="route-info-label"><i class="fas fa-ruler"></i> Distance:</span>
                        <span class="route-info-value">${route.total_distance_nm.toFixed(1)} NM</span>
                    </div>
                    ` : ''}
                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ecf0f1; text-align: center;">
                        <button onclick="window.rtzWaypoints.highlightRoute('${routeId}')" 
                                style="background: ${color}; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.9em;">
                            <i class="fas fa-search-plus"></i> Highlight This Route
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Draw multiple routes
     */
    drawMultipleRoutes(routesData) {
        if (!routesData || routesData.length === 0) {
            console.log('⚠️ No routes data to draw');
            return;
        }
        
        console.log(`📍 Drawing ${routesData.length} routes with clear differentiation`);
        console.log(`📍 Waypoints data available for ${Object.keys(this.waypointsData).length} routes`);
        
        // Clear layers but preserve waypointsData
        this.clearAllWaypoints(true);
        this.routesLayer.clearLayers();
        
        // Draw each route - CRITICAL: Add index to route object
        routesData.forEach((route, index) => {
            const routeId = route.route_id || `route-${index}`;
            // Add the index to the route object for waypoint lookup
            route.index = index;
            this.drawCompleteRoute(route, routeId);
        });
        
        // Add to map if visible
        if (this.isVisible) {
            this.waypointsLayer.addTo(this.map);
            this.routesLayer.addTo(this.map);
        }
        
        console.log(`✅ Drew ${routesData.length} routes with clear start/end points`);
        console.log(`✅ Total route lines drawn: ${Object.keys(this.routeLines).length}`);
    }
    
    /**
     * Highlight a specific route by ID - DASHBOARD INTEGRATION METHOD
     */
    highlightRoute(routeId) {
        console.log(`🔦 rtzWaypoints.highlightRoute called for: ${routeId}`);
        
        // Reset all routes to normal
        Object.values(this.routeLines).forEach(line => {
            line.setStyle({
                weight: 4,
                opacity: 0.85,
                color: line.options.originalColor || line.options.color
            });
        });
        
        // Highlight the selected route
        if (this.routeLines[routeId]) {
            this.routeLines[routeId].setStyle({
                weight: 8,
                opacity: 1,
                color: '#FFD700', // Gold color for highlighting
                className: 'rtz-route-highlighted'
            });
            
            // Fit bounds to show the entire route
            const bounds = this.routeLines[routeId].getBounds();
            if (bounds.isValid()) {
                this.map.fitBounds(bounds, { 
                    padding: [50, 50],
                    animate: true,
                    duration: 1
                });
            }
            
            console.log(`✅ Highlighted route: ${routeId}`);
            return true;
        } else {
            console.log(`❌ Route not found: ${routeId}`);
            console.log(`Available routes:`, Object.keys(this.routeLines));
            return false;
        }
    }
    
    /**
     * Clear all routes highlighting
     */
    clearAllHighlights() {
        Object.values(this.routeLines).forEach(line => {
            line.setStyle({
                weight: 4,
                opacity: 0.85,
                color: line.options.originalColor || line.options.color
            });
        });
        console.log('🧹 Cleared all route highlights');
    }
    
    /**
     * Get waypoints data for a specific route - FOR DASHBOARD INTEGRATION
     */
    getWaypointsData(routeId) {
        // Return stored waypoints if available
        if (this.waypointsData[routeId]) {
            return this.waypointsData[routeId];
        }
        
        // If we have markers for this route, extract coordinates
        if (this.waypointMarkers[routeId]) {
            const waypoints = this.waypointMarkers[routeId].map(marker => {
                const latLng = marker.getLatLng();
                return {
                    lat: latLng.lat,
                    lon: latLng.lng,
                    name: marker._tooltip ? marker._tooltip._content : 'Waypoint'
                };
            });
            
            // Store in cache
            this.waypointsData[routeId] = waypoints;
            return waypoints;
        }
        
        return [];
    }
    
    /**
     * Clear all routes (dashboard integration method)
     */
    clearAllRoutes() {
        this.clearAllWaypoints();
        console.log('🧹 Cleared all RTZ routes (dashboard integration)');
    }
    
    /**
     * Show route details panel
     */
    showRouteDetails(route, routeId, color) {
        // Create detailed route information panel
        const waypointCount = route.waypoints ? route.waypoints.length : 0;
        const routeName = this.getRouteDisplayName(route, routeId);
        
        const detailsContent = `
            <div style="min-width: 300px; max-width: 400px; padding: 15px;">
                <h4 style="margin-top: 0; color: ${color};">
                    <i class="fas fa-route"></i> ${routeName}
                </h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                    <div>
                        <strong>Origin:</strong><br>
                        <span>${route.origin || 'Unknown'}</span>
                    </div>
                    <div>
                        <strong>Destination:</strong><br>
                        <span>${route.destination || 'Unknown'}</span>
                    </div>
                    <div>
                        <strong>Waypoints:</strong><br>
                        <span>${waypointCount}</span>
                    </div>
                    <div>
                        <strong>Distance:</strong><br>
                        <span>${route.total_distance_nm ? route.total_distance_nm.toFixed(1) + ' NM' : 'N/A'}</span>
                    </div>
                </div>
                ${route.description ? `
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                    <strong>Description:</strong><br>
                    <small>${route.description}</small>
                </div>
                ` : ''}
                <div style="margin-top: 15px; text-align: center;">
                    <button onclick="window.rtzWaypoints.zoomToRoute('${routeId}')" 
                            style="background: ${color}; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px;">
                        <i class="fas fa-search"></i> Zoom to Route
                    </button>
                    <button onclick="window.rtzWaypoints.highlightRoute('${routeId}')" 
                            style="background: #FFD700; color: #000; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        <i class="fas fa-star"></i> Highlight
                    </button>
                </div>
            </div>
        `;
        
        L.popup()
            .setLatLng(this.routeLines[routeId] ? this.routeLines[routeId].getBounds().getCenter() : [60, 10])
            .setContent(detailsContent)
            .openOn(this.map);
    }
    
    /**
     * Zoom to specific route
     */
    zoomToRoute(routeId) {
        if (this.routeLines[routeId]) {
            const bounds = this.routeLines[routeId].getBounds();
            if (bounds.isValid()) {
                this.map.fitBounds(bounds, {
                    padding: [100, 100],
                    maxZoom: 12,
                    animate: true,
                    duration: 1
                });
                console.log(`✅ Zoomed to route: ${routeId}`);
                return true;
            }
        }
        console.log(`❌ Could not zoom to route: ${routeId}`);
        return false;
    }
    
    /**
     * Show waypoint details
     */
    showWaypointDetails(waypoint, index, route, routeId) {
        const waypointName = this.getWaypointName(waypoint, index, route);
        const routeDisplayName = this.getRouteDisplayName(route, routeId);
        
        const popupContent = `
            <div style="min-width: 250px;">
                <div style="background: #007bff; color: white; padding: 10px; border-radius: 5px 5px 0 0;">
                    <i class="fas fa-map-marker-alt"></i> ${waypointName}
                </div>
                <div style="padding: 10px; background: white;">
                    <table style="width: 100%; font-size: 12px;">
                        <tr><td><strong>Route:</strong></td><td>${routeDisplayName}</td></tr>
                        <tr><td><strong>Position:</strong></td><td>${waypoint.lat.toFixed(5)}°, ${waypoint.lon.toFixed(5)}°</td></tr>
                        <tr><td><strong>Sequence:</strong></td><td>${index + 1} of ${route.waypoints.length}</td></tr>
                        ${waypoint.radius ? `<tr><td><strong>Turn Radius:</strong></td><td>${waypoint.radius} NM</td></tr>` : ''}
                        ${index === 0 ? `<tr><td><strong>Type:</strong></td><td><span style="color: #2ecc73;">START POINT</span></td></tr>` : ''}
                        ${index === route.waypoints.length - 1 ? `<tr><td><strong>Type:</strong></td><td><span style="color: #e74c3c;">END POINT</span></td></tr>` : ''}
                    </table>
                </div>
            </div>
        `;
        
        L.popup()
            .setLatLng([waypoint.lat, waypoint.lon])
            .setContent(popupContent)
            .openOn(this.map);
    }
    
    /**
     * Helper methods
     */
    getRouteColor(route) {
        // Safety check - if routeColorMap is missing (should not happen), reinitialize
        if (!this.routeColorMap) {
            console.warn('⚠️ routeColorMap missing, reinitializing');
            this.routeColorMap = {
                'bergen': '#3498db', 'oslo': '#2ecc71', 'trondheim': '#e74c3c',
                'stavanger': '#f39c12', 'alesund': '#9b59b6', 'kristiansand': '#1abc9c',
                'drammen': '#d35400', 'sandefjord': '#27ae60', 'flekkefjord': '#8e44ad',
                'andalsnes': '#16a085'
            };
        }
        
        // Safety check - if route is undefined, return default
        if (!route) {
            return this.defaultRouteColor;
        }
        
        // If source_city exists and is a string, use it
        if (route.source_city && typeof route.source_city === 'string') {
            const sourceCity = route.source_city.toLowerCase();
            return this.routeColorMap[sourceCity] || this.defaultRouteColor;
        }
        
        // Default fallback
        return this.defaultRouteColor;
    }
    
    isImportantWaypoint(index, totalWaypoints) {
        // Mark every 5th waypoint as important, or turns (simplified logic)
        return index % 5 === 0 || index === Math.floor(totalWaypoints / 2);
    }
    
    getWaypointName(waypoint, index, route) {
        if (waypoint.name && waypoint.name.trim() !== '') {
            return waypoint.name;
        }
        
        if (index === 0) return 'Start Point';
        if (index === route.waypoints.length - 1) return 'End Point';
        
        const commonNames = {
            'Fedjeosen': 'Fedjeosen',
            'Marstein': 'Marstein',
            'Skudefjorden': 'Skudefjorden',
            'Breisundet': 'Breisundet',
            'Halten': 'Halten',
            'Stad': 'Stad',
            'Oksoy': 'Oksøy',
            'Feistein': 'Feistein',
            'Kobbaleia': 'Kobbaleia'
        };
        
        const routeName = route.route_name || '';
        for (const [key, name] of Object.entries(commonNames)) {
            if (routeName.includes(key)) {
                return name;
            }
        }
        
        return `Waypoint ${index + 1}`;
    }
    
    getRouteDisplayName(route, routeId) {
        let name = route.clean_name || route.route_name || routeId;
        
        name = name
            .replace('NCA_', '')
            .replace(/_2025\d{4}/, '')
            .replace('_In', ' Inbound')
            .replace('_Out', ' Outbound')
            .replace(/_/g, ' ')
            .trim();
            
        return name;
    }
    
    /**
     * Toggle visibility
     */
    toggleVisibility(visible = null) {
        if (visible === null) {
            this.isVisible = !this.isVisible;
        } else {
            this.isVisible = visible;
        }
        
        if (this.isVisible) {
            this.waypointsLayer.addTo(this.map);
            this.routesLayer.addTo(this.map);
            console.log('📍 Waypoints and routes shown');
        } else {
            this.map.removeLayer(this.waypointsLayer);
            this.map.removeLayer(this.routesLayer);
            console.log('📍 Waypoints and routes hidden');
        }
        
        return this.isVisible;
    }
    
    /**
     * Clear all waypoints and routes
     */
    clearAllWaypoints(preserveData = false) {
        this.waypointsLayer.clearLayers();
        this.routesLayer.clearLayers();
        this.waypointMarkers = {};
        this.routeLines = {};
        
        // Only clear waypointsData if not preserving
        if (!preserveData) {
            this.waypointsData = {};
            console.log('🧹 All waypoints and routes cleared (including data)');
        } else {
            console.log('🧹 Cleared layers only, preserving waypointsData');
        }
    }
    
    /**
     * Clear specific route
     */
    clearRouteWaypoints(routeId) {
        if (this.waypointMarkers[routeId]) {
            this.waypointMarkers[routeId].forEach(marker => {
                this.waypointsLayer.removeLayer(marker);
            });
            delete this.waypointMarkers[routeId];
        }
        
        if (this.routeLines[routeId]) {
            this.routesLayer.removeLayer(this.routeLines[routeId]);
            delete this.routeLines[routeId];
        }
        
        if (this.waypointsData[routeId]) {
            delete this.waypointsData[routeId];
        }
        
        console.log(`🧹 Cleared route ${routeId}`);
    }
    
    /**
     * Highlight specific waypoint
     */
    highlightWaypoint(routeId, waypointIndex) {
        // Reset all waypoints
        Object.values(this.waypointMarkers).flat().forEach(marker => {
            const originalStyle = marker.options;
            marker.setStyle({
                radius: originalStyle.radius,
                color: originalStyle.color,
                fillColor: originalStyle.fillColor,
                weight: originalStyle.weight
            });
        });
        
        // Highlight the specific waypoint
        if (this.waypointMarkers[routeId] && this.waypointMarkers[routeId][waypointIndex]) {
            const marker = this.waypointMarkers[routeId][waypointIndex];
            marker.setStyle({
                radius: marker.options.radius * 1.5,
                color: '#ffc107',
                fillColor: '#ffc107',
                weight: 3
            });
            
            marker.openTooltip();
            this.map.panTo(marker.getLatLng());
            
            console.log(`🔦 Highlighted waypoint ${waypointIndex + 1} for route ${routeId}`);
        }
    }
    
    /**
     * Debug method to show available routes
     */
    debugRoutes() {
        console.log('=== 🔧 RTZ WAYPOINTS DEBUG ===');
        console.log('Total routes drawn:', Object.keys(this.routeLines).length);
        console.log('Available route IDs:', Object.keys(this.routeLines));
        console.log('Waypoints data stored for:', Object.keys(this.waypointsData).length, 'routes');
        
        if (Object.keys(this.waypointsData).length > 0) {
            const firstKey = Object.keys(this.waypointsData)[0];
            const data = this.waypointsData[firstKey];
            console.log(`Sample route key "${firstKey}" has:`, data?.length || 0, 'waypoints');
            if (data && data.length > 0) {
                console.log('First waypoint:', data[0]);
            }
        }
        
        console.log('Routes in dashboardData:', window.dashboardData?.routes?.length || 0);
        console.log('=== END DEBUG ===');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const checkMap = setInterval(() => {
        if (window.map) {
            clearInterval(checkMap);
            
            // Initialize waypoints module
            window.rtzWaypoints = new RTZWaypoints(window.map);
            console.log('✅ RTZ Waypoints module ready (Enhanced Integration Version)');
            
            // Debug after 2 seconds
            setTimeout(() => {
                window.rtzWaypoints.debugRoutes();
            }, 2000);
        }
    }, 100);
});

// Export for global use
window.RTZWaypoints = RTZWaypoints;