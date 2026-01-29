// backend/static/js/split/rtz_waypoints.js
/**
 * RTZ Waypoints Display Module
 * Shows all waypoints for RTZ routes on the map
 * ENHANCED VERSION: Clear start/end points, no blinking, proper route differentiation
 */

class RTZWaypoints {
    constructor(map) {
        this.map = map;
        this.waypointsLayer = L.layerGroup();
        this.routesLayer = L.layerGroup();
        this.isVisible = true;
        this.waypointMarkers = {};
        this.routeLines = {};
        console.log('📍 RTZ Waypoints module initialized - NO BLINKING VERSION');
        
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
    }
    
    /**
     * Draw complete route with waypoints
     */
    drawCompleteRoute(route, routeId) {
        if (!route.waypoints || !Array.isArray(route.waypoints)) {
            console.log(`⚠️ No waypoints array for route ${routeId}`);
            return;
        }
        
        console.log(`📍 Drawing complete route ${routeId} with ${route.waypoints.length} waypoints`);
        
        // Get route color based on source city
        const routeColor = this.getRouteColor(route);
        const sourceCity = (route.source_city || '').toLowerCase();
        
        // Clear previous markers for this route
        this.clearRouteWaypoints(routeId);
        
        // Store markers for this route
        this.waypointMarkers[routeId] = [];
        
        // Draw route line
        this.drawRouteLine(route, routeId, routeColor, sourceCity);
        
        // Draw all waypoints
        route.waypoints.forEach((waypoint, index) => {
            if (waypoint && waypoint.lat !== undefined && waypoint.lon !== undefined) {
                const marker = this.createWaypointMarker(waypoint, index, route, routeId, routeColor);
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
        console.log(`📍 Drawing ${routesData.length} routes with clear differentiation`);
        
        // Clear existing layers
        this.clearAllWaypoints();
        this.routesLayer.clearLayers();
        
        // Draw each route
        routesData.forEach((route, index) => {
            const routeId = route.route_id || `route-${index}`;
            this.drawCompleteRoute(route, routeId);
        });
        
        // Add to map if visible
        if (this.isVisible) {
            this.waypointsLayer.addTo(this.map);
            this.routesLayer.addTo(this.map);
        }
        
        console.log(`✅ Drew ${routesData.length} routes with clear start/end points`);
    }
    
    /**
     * Highlight a specific route
     */
    highlightRoute(routeId) {
        // Reset all routes to normal
        Object.values(this.routeLines).forEach(line => {
            line.setStyle({
                weight: 4,
                opacity: 0.85
            });
        });
        
        // Highlight the selected route
        if (this.routeLines[routeId]) {
            this.routeLines[routeId].setStyle({
                weight: 7,
                opacity: 1,
                className: this.routeLines[routeId].options.className + ' selected'
            });
            
            // Fit bounds to show the entire route
            const bounds = this.routeLines[routeId].getBounds();
            if (bounds.isValid()) {
                this.map.fitBounds(bounds, { padding: [50, 50] });
            }
            
            // Show notification
            if (window.showNotification) {
                window.showNotification(`Highlighted route: ${routeId}`, 'success');
            }
        }
    }
    
    /**
     * Show route details panel
     */
    showRouteDetails(route, routeId, color) {
        // Implementation for route details panel
        // ... (existing code)
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
        const sourceCity = (route.source_city || '').toLowerCase();
        return this.routeColorMap[sourceCity] || this.defaultRouteColor;
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
    clearAllWaypoints() {
        this.waypointsLayer.clearLayers();
        this.routesLayer.clearLayers();
        this.waypointMarkers = {};
        this.routeLines = {};
        console.log('🧹 All waypoints and routes cleared');
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const checkMap = setInterval(() => {
        if (window.map) {
            clearInterval(checkMap);
            
            // Initialize waypoints module
            window.rtzWaypoints = new RTZWaypoints(window.map);
            console.log('✅ RTZ Waypoints module ready (No Blinking Version)');
            
            // Listen for routes data
            document.addEventListener('routesDataLoaded', function(e) {
                if (e.detail && e.detail.routes) {
                    console.log('🎯 Got routes data, drawing routes with clear differentiation...');
                    window.rtzWaypoints.drawMultipleRoutes(e.detail.routes);
                }
            });
            
            // Auto-load from window.allRoutesData if available
            setTimeout(() => {
                if (window.allRoutesData && window.rtzWaypoints.waypointsLayer.getLayers().length === 0) {
                    console.log('🌐 Auto-loading routes from window.allRoutesData...');
                    window.rtzWaypoints.drawMultipleRoutes(window.allRoutesData);
                }
            }, 1000);
        }
    }, 100);
});

// Export for global use
window.RTZWaypoints = RTZWaypoints;