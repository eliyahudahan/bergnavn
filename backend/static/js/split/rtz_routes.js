/**
 * RTZ Route Loader for BergNavn Maritime Dashboard
 * Loads and displays Norwegian Coastal Administration RTZ routes on the map
 */

// Global RTZ manager instance
let rtzManager = null;

// Initialize RTZ routes when map is ready
function initRTZRoutes(map) {
    if (!map) {
        console.error('Cannot initialize RTZ routes: Map not found');
        return null;
    }
    
    if (!rtzManager) {
        rtzManager = new RTZRouteManager(map);
        window.rtzManager = rtzManager; // Make globally accessible
        console.log('RTZ Route Manager initialized successfully');
    }
    
    return rtzManager;
}

/**
 * RTZ Route Manager Class
 * Handles loading, displaying, and managing RTZ routes on the map
 */
class RTZRouteManager {
    constructor(map) {
        this.map = map;
        this.activeRoutes = new Map(); // routeId -> {polyline, startMarker, endMarker}
        this.routeData = [];
        this.isPanelVisible = false;
        
        this.initUI();
        this.loadRoutes();
    }
    
    /**
     * Initialize the RTZ control panel UI
     */
    initUI() {
        // Create control panel container
        this.panelContainer = document.createElement('div');
        this.panelContainer.className = 'rtz-panel';
        this.panelContainer.id = 'rtz-control-panel';
        this.panelContainer.style.cssText = `
            position: absolute;
            top: 150px;
            right: 20px;
            width: 300px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            border: 1px solid #dee2e6;
            display: none;
        `;
        
        // Panel HTML structure
        this.panelContainer.innerHTML = `
            <div class="rtz-panel-header" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                background: linear-gradient(135deg, #1a2980 0%, #26d0ce 100%);
                color: white;
                border-radius: 8px 8px 0 0;
            ">
                <h6 style="margin: 0; font-size: 14px; font-weight: 600;">
                    <i class="fas fa-route"></i> NCA RTZ Routes
                </h6>
                <button class="rtz-close-btn" onclick="window.rtzManager.togglePanel()" 
                    style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 0; line-height: 1;">
                    &times;
                </button>
            </div>
            <div class="rtz-panel-body" style="padding: 15px;">
                <div class="form-group mb-3">
                    <label class="small text-muted" style="display: block; margin-bottom: 5px;">
                        <i class="fas fa-map-signs"></i> Select Route:
                    </label>
                    <select class="form-control form-control-sm" id="rtz-route-select" 
                        onchange="window.rtzManager.onRouteSelect(this.value)"
                        style="width: 100%; padding: 6px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px;">
                        <option value="">-- Choose a route --</option>
                    </select>
                </div>
                
                <div id="rtz-route-info" style="display: none;">
                    <div class="rtz-info-card" style="
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 6px;
                        padding: 10px;
                        margin-top: 10px;
                    ">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="fw-bold" id="rtz-route-name" style="font-size: 14px;">-</span>
                            <span class="badge bg-primary" id="rtz-route-distance" style="font-size: 12px;">- nm</span>
                        </div>
                        <div class="small text-muted mb-2">
                            <i class="fas fa-city"></i> <span id="rtz-route-city">-</span> • 
                            <i class="fas fa-map-marker-alt"></i> <span id="rtz-waypoint-count">-</span> waypoints
                        </div>
                        <div class="rtz-actions d-flex gap-2" style="margin-top: 10px;">
                            <button class="btn btn-sm btn-outline-primary" onclick="window.rtzManager.zoomToRoute()"
                                style="flex: 1; font-size: 12px; padding: 4px 8px;">
                                <i class="fas fa-search-plus"></i> Zoom
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="window.rtzManager.clearRoute()"
                                style="flex: 1; font-size: 12px; padding: 4px 8px;">
                                <i class="fas fa-times"></i> Clear
                            </button>
                        </div>
                    </div>
                </div>
                
                <div id="rtz-loading" class="text-center py-3">
                    <div class="spinner-border spinner-border-sm text-primary" role="status" style="width: 1rem; height: 1rem;"></div>
                    <span class="small text-muted ms-2">Loading routes...</span>
                </div>
                
                <div id="rtz-error" class="text-center py-3" style="display: none;">
                    <span class="small text-danger">
                        <i class="fas fa-exclamation-triangle"></i> Failed to load routes
                    </span>
                </div>
                
                <div class="small text-muted mt-3" style="font-size: 11px; border-top: 1px solid #eee; padding-top: 10px;">
                    <i class="fas fa-info-circle"></i> Routes from Norwegian Coastal Administration (NCA)
                </div>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(this.panelContainer);
    }
    
    /**
     * Load RTZ routes from the backend API
     */
    async loadRoutes() {
        const loadingEl = document.getElementById('rtz-loading');
        const errorEl = document.getElementById('rtz-error');
        const selectEl = document.getElementById('rtz-route-select');
        
        try {
            const response = await fetch('/maritime/api/rtz/simple');
            const data = await response.json();
            
            if (data.status === 'success' && data.routes.length > 0) {
                this.routeData = data.routes;
                
                // Clear existing options except the first one
                while (selectEl.options.length > 1) {
                    selectEl.remove(1);
                }
                
                // Add routes to select dropdown
                data.routes.forEach(route => {
                    const option = document.createElement('option');
                    option.value = route.id;
                    option.textContent = `${route.city} - ${this.formatRouteName(route.name)} (${route.distance} nm)`;
                    selectEl.appendChild(option);
                });
                
                // Hide loading, show success
                if (loadingEl) loadingEl.style.display = 'none';
                if (errorEl) errorEl.style.display = 'none';
                
                console.log(`Loaded ${data.routes.length} RTZ routes`);
            } else {
                throw new Error('No routes available');
            }
        } catch (error) {
            console.error('Failed to load RTZ routes:', error);
            if (loadingEl) loadingEl.style.display = 'none';
            if (errorEl) errorEl.style.display = 'block';
            
            // Add sample option for testing
            const selectEl = document.getElementById('rtz-route-select');
            const option = document.createElement('option');
            option.value = 'sample';
            option.textContent = 'Sample Route (API Error)';
            selectEl.appendChild(option);
        }
    }
    
    /**
     * Format route name for display (remove NCA_ prefix and underscores)
     */
    formatRouteName(name) {
        return name.replace('NCA_', '').replace(/_/g, ' ').substring(0, 30) + (name.length > 30 ? '...' : '');
    }
    
    /**
     * Handle route selection from dropdown
     */
    onRouteSelect(routeId) {
        if (!routeId || routeId === '') {
            this.clearRoute();
            return;
        }
        
        // Handle sample route for testing
        if (routeId === 'sample') {
            this.showSampleRoute();
            return;
        }
        
        const route = this.routeData.find(r => r.id === routeId);
        if (!route || !route.points || route.points.length === 0) {
            console.error('Invalid route selected:', routeId);
            return;
        }
        
        if (!this.map) {
            console.error('Map not available for displaying route');
            return;
        }
        
        // Clear any existing route
        this.clearRoute();
        
        // Create polyline from route points
        const latlngs = route.points.map(p => [p.lat, p.lon]);
        const polyline = L.polyline(latlngs, {
            color: '#1a2980',
            weight: 4,
            opacity: 0.8,
            dashArray: '8, 4',
            lineCap: 'round',
            className: 'rtz-route-line'
        }).addTo(this.map);
        
        // Add start marker
        const startMarker = L.circleMarker(latlngs[0], {
            color: '#26d0ce',
            fillColor: '#26d0ce',
            fillOpacity: 0.9,
            radius: 7,
            weight: 2
        }).addTo(this.map)
        .bindPopup(`<b>Start:</b> ${this.formatRouteName(route.name)}<br><i class="fas fa-city"></i> ${route.city}`);
        
        // Add end marker
        const endMarker = L.circleMarker(latlngs[latlngs.length - 1], {
            color: '#ff6b6b',
            fillColor: '#ff6b6b',
            fillOpacity: 0.9,
            radius: 7,
            weight: 2
        }).addTo(this.map)
        .bindPopup(`<b>End:</b> ${this.formatRouteName(route.name)}<br>${route.distance} nm • ${route.city}`);
        
        // Store reference to active route
        this.activeRoutes.set(routeId, { polyline, startMarker, endMarker });
        
        // Update UI with route info
        this.updateRouteInfo(route);
        
        // Zoom to show the entire route
        this.map.fitBounds(polyline.getBounds());
        
        console.log(`Route loaded: ${route.city} - ${route.name}`);
    }
    
    /**
     * Update UI with selected route information
     */
    updateRouteInfo(route) {
        const infoContainer = document.getElementById('rtz-route-info');
        const routeNameEl = document.getElementById('rtz-route-name');
        const routeCityEl = document.getElementById('rtz-route-city');
        const routeDistanceEl = document.getElementById('rtz-route-distance');
        const waypointCountEl = document.getElementById('rtz-waypoint-count');
        
        if (infoContainer && routeNameEl && routeCityEl && routeDistanceEl && waypointCountEl) {
            routeNameEl.textContent = this.formatRouteName(route.name);
            routeCityEl.textContent = route.city;
            routeDistanceEl.textContent = `${route.distance} nm`;
            waypointCountEl.textContent = route.waypoint_count;
            infoContainer.style.display = 'block';
        }
    }
    
    /**
     * Show sample route for testing (when API fails)
     */
    showSampleRoute() {
        if (!this.map) return;
        
        this.clearRoute();
        
        // Sample Bergen route
        const samplePoints = [
            [60.3913, 5.3221], // Bergen
            [60.398, 5.315],
            [60.405, 5.305],
            [60.415, 5.295]
        ];
        
        const polyline = L.polyline(samplePoints, {
            color: '#1a2980',
            weight: 4,
            opacity: 0.8,
            dashArray: '8, 4'
        }).addTo(this.map);
        
        // Store reference
        this.activeRoutes.set('sample', { polyline });
        
        // Update UI
        const infoContainer = document.getElementById('rtz-route-info');
        const routeNameEl = document.getElementById('rtz-route-name');
        const routeCityEl = document.getElementById('rtz-route-city');
        const routeDistanceEl = document.getElementById('rtz-route-distance');
        
        if (infoContainer && routeNameEl && routeCityEl && routeDistanceEl) {
            routeNameEl.textContent = 'Sample Bergen Route';
            routeCityEl.textContent = 'Bergen';
            routeDistanceEl.textContent = '12.5 nm';
            infoContainer.style.display = 'block';
        }
        
        this.map.fitBounds(polyline.getBounds());
    }
    
    /**
     * Zoom to active route bounds
     */
    zoomToRoute() {
        const selectEl = document.getElementById('rtz-route-select');
        const routeId = selectEl.value;
        
        if (routeId && this.activeRoutes.has(routeId)) {
            const route = this.activeRoutes.get(routeId);
            this.map.fitBounds(route.polyline.getBounds());
        }
    }
    
    /**
     * Clear active route from map
     */
    clearRoute() {
        // Remove all active route layers from map
        this.activeRoutes.forEach(layers => {
            if (layers.polyline) this.map.removeLayer(layers.polyline);
            if (layers.startMarker) this.map.removeLayer(layers.startMarker);
            if (layers.endMarker) this.map.removeLayer(layers.endMarker);
        });
        
        // Clear references
        this.activeRoutes.clear();
        
        // Reset UI
        const selectEl = document.getElementById('rtz-route-select');
        const infoContainer = document.getElementById('rtz-route-info');
        
        if (selectEl) selectEl.value = '';
        if (infoContainer) infoContainer.style.display = 'none';
    }
    
    /**
     * Toggle RTZ control panel visibility
     */
    togglePanel() {
        const panel = document.getElementById('rtz-control-panel');
        
        if (!this.isPanelVisible) {
            // Show panel
            panel.style.display = 'block';
            this.isPanelVisible = true;
            
            // Reload routes if empty
            if (this.routeData.length === 0) {
                this.loadRoutes();
            }
        } else {
            // Hide panel and clear route
            panel.style.display = 'none';
            this.clearRoute();
            this.isPanelVisible = false;
        }
    }
    
    /**
     * Alias for togglePanel (for button compatibility)
     */
    toggle() {
        this.togglePanel();
    }
}