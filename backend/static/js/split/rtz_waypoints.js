/* backend/static/js/split/rtz_waypoints.js */
/**
 * RTZ Waypoints Display Module
 * Shows all waypoints for RTZ routes on the map
 * IMPROVED VERSION: Shows real names and prevents duplicates
 */

class RTZWaypoints {
    constructor(map) {
        this.map = map;
        this.waypointsLayer = L.layerGroup();
        this.isVisible = true;
        this.waypointMarkers = {};
        console.log('📍 RTZ Waypoints module initialized');
    }
    
    /**
     * Add waypoints for a specific route
     */
    addRouteWaypoints(route, routeId) {
        if (!route.waypoints || !Array.isArray(route.waypoints)) {
            console.log(`⚠️ No waypoints array for route ${routeId}`);
            return;
        }
        
        console.log(`📍 Adding ${route.waypoints.length} waypoints for route ${routeId}`);
        
        // Store markers for this route
        this.waypointMarkers[routeId] = [];
        
        route.waypoints.forEach((waypoint, index) => {
            // Make sure waypoint has coordinates
            if (waypoint && waypoint.lat !== undefined && waypoint.lon !== undefined) {
                const marker = this.createWaypointMarker(waypoint, index, route, routeId);
                marker.addTo(this.waypointsLayer);
                this.waypointMarkers[routeId].push(marker);
            }
        });
    }
    
    /**
     * Create a waypoint marker - IMPROVED: Shows real names
     */
    createWaypointMarker(waypoint, index, route, routeId) {
        const marker = L.circleMarker([waypoint.lat, waypoint.lon], {
            radius: 6,
            color: '#007bff',
            weight: 2,
            opacity: 0.9,
            fillColor: '#007bff',
            fillOpacity: 0.7,
            className: 'rtz-waypoint-marker'
        });
        
        // Get the best name for this waypoint
        const waypointName = this.getWaypointName(waypoint, index, route);
        const routeDisplayName = this.getRouteDisplayName(route, routeId);
        
        // Tooltip content with real names
        let tooltipContent = `<div style="font-size: 12px; max-width: 200px;">`;
        tooltipContent += `<strong>${waypointName}</strong><br/>`;
        tooltipContent += `<small>Route: ${routeDisplayName}</small><br/>`;
        tooltipContent += `<small>Lat: ${waypoint.lat.toFixed(5)}</small><br/>`;
        tooltipContent += `<small>Lon: ${waypoint.lon.toFixed(5)}</small>`;
        
        if (waypoint.name && waypoint.name !== waypointName) {
            tooltipContent += `<br/><small>ID: ${waypoint.name}</small>`;
        }
        
        if (waypoint.radius) {
            tooltipContent += `<br/><small>Radius: ${waypoint.radius} NM</small>`;
        }
        
        tooltipContent += `</div>`;
        
        marker.bindTooltip(tooltipContent);
        
        // Optional: Add click event
        marker.on('click', function() {
            console.log(`📍 Waypoint ${waypointName} clicked for route ${routeDisplayName}`);
            
            // Simple popup with more info
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
                            ${waypoint.radius ? `<tr><td><strong>Radius:</strong></td><td>${waypoint.radius} NM</td></tr>` : ''}
                        </table>
                    </div>
                </div>
            `;
            
            marker.bindPopup(popupContent).openPopup();
        });
        
        return marker;
    }
    
    /**
     * Get the best name for a waypoint
     */
    getWaypointName(waypoint, index, route) {
        // 1. Use the name from waypoint object if it exists
        if (waypoint.name && waypoint.name.trim() !== '') {
            return waypoint.name;
        }
        
        // 2. Try to extract from route information
        const routeName = route.route_name || '';
        
        // Common Norwegian waypoint names
        const commonNames = {
            'Fedjeosen': 'Fedjeosen',
            'Marstein': 'Marstein',
            'Skudefjorden': 'Skudefjorden',
            'Breisundet': 'Breisundet',
            'Halten': 'Halten',
            'Stad': 'Stad',
            'Oksoy': 'Oksøy',
            'Feistein': 'Feistein',
            'Kobbaleia': 'Kobbaleia',
            'Vatlestr': 'Vatlestraum',
            'Bonden': 'Bonden',
            'Sydostgr': 'Sydostgrunnen',
            'Grande': 'Grande',
            'Rorvik': 'Rørvik',
            'Grip': 'Grip'
        };
        
        for (const [key, name] of Object.entries(commonNames)) {
            if (routeName.includes(key)) {
                return name;
            }
        }
        
        // 3. Use clean name if available
        if (route.clean_name) {
            const parts = route.clean_name.split(' ');
            if (parts.length > 0 && parts[0] !== 'Route') {
                return parts[0];
            }
        }
        
        // 4. Fallback to numbered waypoint
        return `Waypoint ${index + 1}`;
    }
    
    /**
     * Get clean display name for route
     */
    getRouteDisplayName(route, routeId) {
        let name = route.clean_name || route.route_name || routeId;
        
        // Clean up the name for display
        name = name
            .replace('NCA_', '')
            .replace(/_2025\d{4}/, '') // Remove dates
            .replace('_In', ' Inbound')
            .replace('_Out', ' Outbound')
            .replace(/_/g, ' ')
            .trim();
            
        return name;
    }
    
    /**
     * Add waypoints for multiple routes
     */
    addMultipleRoutesWaypoints(routesData) {
        console.log(`📍 Processing waypoints for ${routesData.length} routes`);
        
        // Clear existing waypoints
        this.clearAllWaypoints();
        
        // Add waypoints for each route
        routesData.forEach((route, index) => {
            const routeId = route.route_id || `route-${index}`;
            this.addRouteWaypoints(route, routeId);
        });
        
        // Add layer to map if visible
        if (this.isVisible) {
            this.waypointsLayer.addTo(this.map);
        }
        
        console.log(`✅ Added waypoints for ${routesData.length} routes`);
    }
    
    /**
     * Toggle visibility of waypoints
     */
    toggleVisibility(visible = null) {
        if (visible === null) {
            this.isVisible = !this.isVisible;
        } else {
            this.isVisible = visible;
        }
        
        if (this.isVisible) {
            this.waypointsLayer.addTo(this.map);
            console.log('📍 Waypoints layer shown');
        } else {
            this.map.removeLayer(this.waypointsLayer);
            console.log('📍 Waypoints layer hidden');
        }
        
        return this.isVisible;
    }
    
    /**
     * Clear all waypoints
     */
    clearAllWaypoints() {
        this.waypointsLayer.clearLayers();
        this.waypointMarkers = {};
        console.log('🧹 All waypoints cleared');
    }
    
    /**
     * Clear waypoints for a specific route
     */
    clearRouteWaypoints(routeId) {
        if (this.waypointMarkers[routeId]) {
            this.waypointMarkers[routeId].forEach(marker => {
                this.waypointsLayer.removeLayer(marker);
            });
            delete this.waypointMarkers[routeId];
            console.log(`🧹 Cleared waypoints for route ${routeId}`);
        }
    }
    
    /**
     * Highlight a specific waypoint
     */
    highlightWaypoint(routeId, waypointIndex) {
        // Reset all waypoints to normal
        Object.values(this.waypointMarkers).flat().forEach(marker => {
            marker.setStyle({
                color: '#007bff',
                fillColor: '#007bff',
                radius: 6
            });
        });
        
        // Highlight the specific waypoint
        if (this.waypointMarkers[routeId] && this.waypointMarkers[routeId][waypointIndex]) {
            const marker = this.waypointMarkers[routeId][waypointIndex];
            marker.setStyle({
                color: '#ffc107',
                fillColor: '#ffc107',
                radius: 8,
                weight: 3
            });
            
            // Open tooltip
            marker.openTooltip();
            
            // Pan to waypoint
            this.map.panTo(marker.getLatLng());
            
            console.log(`🔦 Highlighted waypoint ${waypointIndex + 1} for route ${routeId}`);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait for map to be ready
    const checkMap = setInterval(() => {
        if (window.map) {
            clearInterval(checkMap);
            
            // Initialize waypoints module
            window.rtzWaypoints = new RTZWaypoints(window.map);
            console.log('✅ RTZ Waypoints module ready');
            
            // Listen for routes data
            document.addEventListener('routesDataLoaded', function(e) {
                if (e.detail && e.detail.routes) {
                    console.log('🎯 Got routes data, adding waypoints...');
                    window.rtzWaypoints.addMultipleRoutesWaypoints(e.detail.routes);
                }
            });
            
            // Auto-load from window.allRoutesData if available
            setTimeout(() => {
                if (window.allRoutesData && window.rtzWaypoints.waypointsLayer.getLayers().length === 0) {
                    console.log('🌐 Auto-loading waypoints from window.allRoutesData...');
                    window.rtzWaypoints.addMultipleRoutesWaypoints(window.allRoutesData);
                }
            }, 1000);
        }
    }, 100);
});

// Add CSS for waypoints
const waypointStyles = document.createElement('style');
waypointStyles.textContent = `
    .rtz-waypoint-marker {
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .rtz-waypoint-marker:hover {
        fill-opacity: 0.9;
        stroke-width: 3;
        transform: scale(1.1);
    }
    
    /* Highlighted waypoint */
    .waypoint-highlighted {
        animation: pulse-waypoint 1.5s infinite;
        box-shadow: 0 0 10px rgba(255, 193, 7, 0.8);
    }
    
    @keyframes pulse-waypoint {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
`;
document.head.appendChild(waypointStyles);

// Export for global use
window.RTZWaypoints = RTZWaypoints;