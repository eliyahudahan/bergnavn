/**
 * Dashboard Routes Manager for BergNavn Maritime Dashboard
 * Simplified version that uses server-rendered table data
 * FIXED: No API dependency, uses existing table data
 */

class DashboardRoutesManager {
    constructor() {
        this.map = null;
        this.routeLayers = [];
        this.routesVisible = false;
        this.routesData = this.extractRoutesFromTable();
        
        console.log(`DashboardRoutesManager initialized with ${this.routesData.length} routes`);
    }
    
    /**
     * Extract route data from the server-rendered HTML table
     * This avoids API dependency and uses what's already on the page
     */
    extractRoutesFromTable() {
        const routes = [];
        const tableRows = document.querySelectorAll('tbody tr.route-row');
        
        tableRows.forEach((row, index) => {
            try {
                const routeId = row.dataset.routeId || index;
                const cells = row.cells;
                
                if (cells.length >= 6) {
                    const routeName = cells[0].querySelector('strong')?.textContent || 'Route ' + (index + 1);
                    const origin = cells[1].textContent.trim();
                    const destination = cells[2].textContent.trim();
                    const distanceText = cells[3].textContent;
                    
                    // Extract numeric distance
                    const distanceMatch = distanceText.match(/(\d+\.?\d*)/);
                    const distance = distanceMatch ? parseFloat(distanceMatch[1]) : 0;
                    
                    routes.push({
                        id: routeId,
                        name: routeName,
                        origin: origin,
                        destination: destination,
                        total_distance_nm: distance,
                        source: 'Table Data'
                    });
                }
            } catch (error) {
                console.warn('Error extracting route from table row:', error);
            }
        });
        
        return routes;
    }
    
    /**
     * Initialize with map reference
     */
    init() {
        // Wait for map to be available
        this.waitForMap().then(() => {
            console.log('DashboardRoutesManager: Map ready');
        }).catch(error => {
            console.warn('DashboardRoutesManager: Map not available, routes will be table-only');
        });
    }
    
    /**
     * Wait for the map to be initialized
     */
    waitForMap() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 20; // 10 seconds total
            
            const checkMap = () => {
                attempts++;
                
                if (window.maritimeMap && typeof window.maritimeMap === 'object') {
                    this.map = window.maritimeMap;
                    resolve(this.map);
                    return;
                }
                
                if (attempts >= maxAttempts) {
                    reject(new Error('Map not available after timeout'));
                    return;
                }
                
                setTimeout(checkMap, 500);
            };
            
            checkMap();
        });
    }
    
    /**
     * Toggle routes on the map
     * Uses sample coordinates since we don't have waypoint data in table
     */
    toggleMapRoutes() {
        if (!this.map) {
            console.warn('Cannot show routes: Map not available');
            alert('Map is not ready. Please wait for map to load.');
            return;
        }
        
        if (this.routesVisible) {
            this.hideRoutes();
        } else {
            this.showRoutes();
        }
        
        this.routesVisible = !this.routesVisible;
        
        // Update button state
        const btn = document.getElementById('rtz-btn');
        if (btn) {
            if (this.routesVisible) {
                btn.classList.add('active');
                btn.title = 'Hide routes from map';
            } else {
                btn.classList.remove('active');
                btn.title = 'Show routes on map';
            }
        }
    }
    
    /**
     * Show sample routes on the map (for demonstration)
     * In production, this would use actual waypoint data
     */
    showRoutes() {
        if (!this.map || this.routesData.length === 0) {
            console.warn('No route data available to display');
            return;
        }
        
        // Clear any existing routes
        this.hideRoutes();
        
        // For each route, draw a line between origin and destination cities
        // Using approximate coordinates for Norwegian ports
        const portCoordinates = {
            'bergen': [60.3913, 5.3221],
            'oslo': [59.9139, 10.7522],
            'stavanger': [58.9699, 5.7331],
            'trondheim': [63.4305, 10.3951],
            'ålesund': [62.4722, 6.1495],
            'andalsnes': [62.5675, 7.6869],
            'drammen': [59.7439, 10.2045],
            'kristiansand': [58.1599, 8.0182],
            'sandefjord': [59.1315, 10.2167],
            'flekkefjord': [58.2975, 6.6606]
        };
        
        this.routesData.forEach((route, index) => {
            try {
                const originKey = route.origin.toLowerCase().replace('å', 'a');
                const destKey = route.destination.toLowerCase().replace('å', 'a');
                
                const originCoords = portCoordinates[originKey] || [59.0, 10.0];
                const destCoords = portCoordinates[destKey] || [60.0, 11.0];
                
                // Create a polyline for the route
                const polyline = L.polyline([originCoords, destCoords], {
                    color: this.getRouteColor(index),
                    weight: 3,
                    opacity: 0.7,
                    dashArray: '5, 5',
                    className: 'dashboard-route-line'
                }).addTo(this.map);
                
                // Add markers for origin and destination
                const originMarker = L.circleMarker(originCoords, {
                    color: '#28a745',
                    fillColor: '#28a745',
                    fillOpacity: 0.8,
                    radius: 6
                }).addTo(this.map)
                .bindPopup(`<b>Origin:</b> ${route.origin}<br><b>Route:</b> ${route.name}`);
                
                const destMarker = L.circleMarker(destCoords, {
                    color: '#dc3545',
                    fillColor: '#dc3545',
                    fillOpacity: 0.8,
                    radius: 6
                }).addTo(this.map)
                .bindPopup(`<b>Destination:</b> ${route.destination}<br><b>Distance:</b> ${route.total_distance_nm || 'N/A'} nm`);
                
                // Store references
                this.routeLayers.push({
                    polyline: polyline,
                    originMarker: originMarker,
                    destMarker: destMarker,
                    route: route
                });
                
            } catch (error) {
                console.warn(`Failed to draw route ${route.name}:`, error);
            }
        });
        
        console.log(`Displayed ${this.routeLayers.length} routes on map`);
        
        // Fit map to show all routes if we have any
        if (this.routeLayers.length > 0) {
            const bounds = L.latLngBounds(
                this.routeLayers.map(layer => [
                    layer.polyline.getBounds().getSouthWest(),
                    layer.polyline.getBounds().getNorthEast()
                ]).flat()
            );
            
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
    
    /**
     * Hide all routes from the map
     */
    hideRoutes() {
        this.routeLayers.forEach(layer => {
            if (layer.polyline && this.map.hasLayer(layer.polyline)) {
                this.map.removeLayer(layer.polyline);
            }
            if (layer.originMarker && this.map.hasLayer(layer.originMarker)) {
                this.map.removeLayer(layer.originMarker);
            }
            if (layer.destMarker && this.map.hasLayer(layer.destMarker)) {
                this.map.removeLayer(layer.destMarker);
            }
        });
        
        this.routeLayers = [];
        console.log('All routes hidden from map');
    }
    
    /**
     * Get distinct color for each route
     */
    getRouteColor(index) {
        const colors = [
            '#1e88e5', // Blue
            '#43a047', // Green
            '#fb8c00', // Orange
            '#e53935', // Red
            '#8e24aa', // Purple
            '#00897b', // Teal
            '#f4511e', // Deep Orange
            '#3949ab', // Indigo
            '#d81b60', // Pink
            '#546e7a'  // Blue Grey
        ];
        
        return colors[index % colors.length];
    }
    
    /**
     * Alias for toggleMapRoutes (for backward compatibility)
     */
    toggle() {
        this.toggleMapRoutes();
    }
}

// Initialize and expose globally
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardRoutes = new DashboardRoutesManager();
});