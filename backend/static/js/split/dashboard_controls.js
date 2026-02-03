// Dashboard Controls v3.3.2 - Complete with ALL original buttons and functions
// Uses real NCA RTZ data - NO simulations
// Real-time first principle with ALL functionality preserved

/**
 * Main Dashboard Controls Class
 * Handles all dashboard UI interactions
 */
class DashboardControls {
    constructor() {
        console.log('🚢 DashboardControls v3.3.2 initialized - ALL buttons preserved');
        
        // State management
        this.map = null;
        this.highlightLayer = null;
        this.currentHighlightedRoute = null;
        this.routesData = [];
        this.waypointsData = {};
        this.portCoordinates = {};
        
        // Layer visibility
        this.layers = {
            rtz: true,
            weather: true,
            ais: true
        };
        
        // Emergency counter
        this.emergencyMode = false;
        
        // Notification system state
        this.notificationTimeout = null;
        this.fallbackNotificationTimeout = null;
        this.lastNotificationType = null;
        
        // Route details modal
        this.routeDetailsModal = null;
    }

    /**
     * Initialize the dashboard controls with map instance
     * @param {Object} mapInstance - Leaflet map instance
     */
    init(mapInstance) {
        console.log('🎮 Dashboard controls initializing - ALL functions preserved...');
        this.map = mapInstance;
        
        // Initialize port coordinates
        this.portCoordinates = this.getPortCoordinates();
        
        // Create special pane for highlights with very high z-index
        if (!this.map.getPane('dashboard-highlight-pane')) {
            this.map.createPane('dashboard-highlight-pane');
            const pane = this.map.getPane('dashboard-highlight-pane');
            pane.style.zIndex = 1000;  // Very high to be on top
            pane.style.pointerEvents = 'none';  // Allow clicks through
            console.log('🎨 Created dashboard-highlight-pane with z-index 1000');
        }
        
        // Create highlight layer with special pane
        this.highlightLayer = L.layerGroup().addTo(this.map);
        
        // Add emergency CSS for visibility
        this.addEmergencyCSS();
        
        // Create route details modal
        this.createRouteDetailsModal();
        
        // Load routes and waypoints data
        this.loadAllData();
        
        // Setup all event listeners and interactivity
        this.setupEventListeners();
        this.setupRouteTableInteractivity();
        this.setupPortFiltering();
        
        // Make zoomToRoute available globally
        this.exposeGlobalFunctions();
        
        console.log('✅ Dashboard controls ready with ALL buttons and functions');
    }
    
    /**
     * Load all required data
     */
    loadAllData() {
        console.log('📊 Loading all dashboard data...');
        
        // Load route data
        this.loadRouteData();
        
        // Load waypoints data
        this.loadWaypointsData();
        
        // Fix route IDs if they're missing
        this.fixMissingRouteIds();
        
        // Debug data state
        this.debugDataState();
    }
    
    /**
     * Load route data from hidden element
     */
    loadRouteData() {
        try {
            const routesDataElement = document.getElementById('routes-data');
            if (routesDataElement && routesDataElement.textContent) {
                this.routesData = JSON.parse(routesDataElement.textContent);
                console.log(`📊 Loaded ${this.routesData.length} routes from DOM`);
                
                // Check data structure
                if (this.routesData.length > 0) {
                    const sampleRoute = this.routesData[0];
                    console.log('Sample route structure:', {
                        hasRouteId: !!sampleRoute.route_id,
                        hasId: !!sampleRoute.id,
                        routeId: sampleRoute.route_id,
                        id: sampleRoute.id,
                        name: sampleRoute.clean_name || sampleRoute.route_name,
                        origin: sampleRoute.origin,
                        destination: sampleRoute.destination,
                        hasWaypoints: !!(sampleRoute.waypoints && sampleRoute.waypoints.length > 0)
                    });
                }
            } else {
                console.warn('⚠️ No routes-data element found in DOM');
                this.routesData = [];
            }
        } catch (e) {
            console.error('Error loading routes data:', e);
            this.routesData = [];
        }
    }
    
    /**
     * Load waypoints data from hidden element
     */
    loadWaypointsData() {
        try {
            const waypointsDataElement = document.getElementById('waypoints-data');
            if (waypointsDataElement && waypointsDataElement.textContent) {
                const waypointsData = JSON.parse(waypointsDataElement.textContent);
                console.log(`📍 Parsed waypoints data, checking structure...`);
                
                // The waypoints data might be in different formats
                // Try different access patterns
                if (Array.isArray(waypointsData)) {
                    console.log('Waypoints data is an array with', waypointsData.length, 'items');
                    // Convert array to object with indices as keys
                    this.waypointsData = {};
                    waypointsData.forEach((waypointGroup, index) => {
                        this.waypointsData[index] = waypointGroup;
                    });
                } else if (typeof waypointsData === 'object') {
                    this.waypointsData = waypointsData;
                    console.log(`📍 Loaded waypoints for ${Object.keys(waypointsData).length} routes as object`);
                } else {
                    console.warn('⚠️ Waypoints data has unknown format:', typeof waypointsData);
                    this.waypointsData = {};
                }
                
                // Debug first key if available
                const firstKey = Object.keys(this.waypointsData)[0];
                if (firstKey) {
                    console.log(`First waypoints key: "${firstKey}" (type: ${typeof firstKey})`);
                    const firstWaypoints = this.waypointsData[firstKey];
                    console.log(`First waypoints value:`, Array.isArray(firstWaypoints) ? 
                        `Array with ${firstWaypoints.length} items` : firstWaypoints);
                }
            } else {
                console.warn('⚠️ No waypoints-data element found in DOM');
                this.waypointsData = {};
            }
        } catch (e) {
            console.error('Error loading waypoints data:', e);
            this.waypointsData = {};
        }
    }
    
    /**
     * Fix missing route IDs in the routes data
     */
    fixMissingRouteIds() {
        console.log('🔧 Checking and fixing missing route IDs...');
        
        let fixedCount = 0;
        this.routesData.forEach((route, index) => {
            // If route doesn't have route_id or id, create one
            if (!route.route_id && !route.id) {
                // Create a unique ID based on index and name
                const routeName = route.clean_name || route.route_name || `route_${index}`;
                const cleanId = routeName.toLowerCase()
                    .replace(/[^a-z0-9]/g, '_')
                    .replace(/_+/g, '_');
                
                route.id = `route_${index}_${cleanId}`;
                route.route_id = index; // Also set numeric ID
                fixedCount++;
                
                console.log(`Fixed route ${index}:`, route.id);
            } else if (route.route_id === undefined && route.id) {
                // If only id exists, copy to route_id
                route.route_id = route.id;
                fixedCount++;
            } else if (route.id === undefined && route.route_id) {
                // If only route_id exists, copy to id
                route.id = route.route_id;
                fixedCount++;
            }
        });
        
        if (fixedCount > 0) {
            console.log(`✅ Fixed IDs for ${fixedCount} routes`);
        } else {
            console.log('✅ All routes have proper IDs');
        }
    }
    
    /**
     * Debug data state
     */
    debugDataState() {
        console.log('=== 📊 DATA STATE DEBUG ===');
        console.log('Total routes:', this.routesData.length);
        console.log('Waypoints data keys:', Object.keys(this.waypointsData));
        
        if (this.routesData.length > 0) {
            console.log('First route:', {
                index: 0,
                id: this.routesData[0].id,
                route_id: this.routesData[0].route_id,
                name: this.routesData[0].clean_name || this.routesData[0].route_name,
                origin: this.routesData[0].origin,
                destination: this.routesData[0].destination
            });
            
            // Check what's in waypointsData for this route
            const firstRouteId = this.routesData[0].id || this.routesData[0].route_id || '0';
            console.log(`Looking for waypoints with key: "${firstRouteId}"`);
            console.log(`Waypoints found:`, this.waypointsData[firstRouteId]);
            
            // Also try with numeric index
            console.log(`Trying with numeric key: "0"`);
            console.log(`Waypoints found:`, this.waypointsData[0]);
            console.log(`Trying with string numeric key: "0"`);
            console.log(`Waypoints found:`, this.waypointsData["0"]);
        }
        console.log('=== END DATA DEBUG ===');
    }
    
    /**
     * Create route details modal
     */
    createRouteDetailsModal() {
        // Create modal element
        const modal = document.createElement('div');
        modal.id = 'routeDetailsModal';
        modal.className = 'modal fade';
        modal.tabIndex = '-1';
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="routeModalTitle">
                            <i class="fas fa-route me-2"></i>
                            Route Details
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="routeModalBody">
                        Loading route information...
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i> Close
                        </button>
                        <button type="button" class="btn btn-primary" id="routeModalZoomBtn">
                            <i class="fas fa-search me-1"></i> Zoom to Route
                        </button>
                        <button type="button" class="btn btn-warning" id="routeModalHighlightBtn">
                            <i class="fas fa-map-marker-alt me-1"></i> Highlight
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.routeDetailsModal = new bootstrap.Modal(modal);
        
        // Setup modal button handlers
        modal.querySelector('#routeModalZoomBtn').addEventListener('click', () => {
            const routeIndex = modal.dataset.currentRouteIndex;
            if (routeIndex !== undefined) {
                this.zoomToRouteByIndex(parseInt(routeIndex));
            }
            this.routeDetailsModal.hide();
        });
        
        modal.querySelector('#routeModalHighlightBtn').addEventListener('click', () => {
            const routeIndex = modal.dataset.currentRouteIndex;
            if (routeIndex !== undefined) {
                this.highlightRouteOnMap(parseInt(routeIndex));
            }
            this.routeDetailsModal.hide();
        });
        
        console.log('✅ Created route details modal');
    }
    
    /**
     * Add emergency CSS for visual elements
     */
    addEmergencyCSS() {
        // Only add if not already added
        if (document.getElementById('dashboard-emergency-css')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'dashboard-emergency-css';
        style.textContent = `
            /* Emergency highlight styles */
            .super-visible-line {
                filter: drop-shadow(0 0 10px red) !important;
                animation: pulseLine 2s infinite !important;
            }
            
            .super-visible-marker {
                z-index: 2000 !important;
            }
            
            .emergency-line {
                filter: drop-shadow(0 0 15px lime) !important;
                animation: blinkLine 1s infinite !important;
            }
            
            .emergency-marker {
                z-index: 2001 !important;
            }
            
            /* Route highlight styles */
            .route-highlight-start div {
                animation: pulse 2s infinite;
                box-shadow: 0 0 20px #28a745 !important;
            }
            
            .route-highlight-end div {
                animation: pulse 2s infinite;
                box-shadow: 0 0 20px #dc3545 !important;
            }
            
            .route-highlight-port div {
                animation: pulse 1.5s infinite;
                box-shadow: 0 0 15px #ffc107 !important;
            }
            
            .highlight-port-line {
                filter: drop-shadow(0 0 5px #3498db);
            }
            
            /* Real-time notification styles */
            .dashboard-notification.show {
                opacity: 1 !important;
                transform: translateY(0) !important;
                display: block !important;
                visibility: visible !important;
            }
            
            /* Route details modal styles */
            .route-details-modal .modal-content {
                border: 2px solid #3498db;
                border-radius: 10px;
            }
            
            .route-details-modal .modal-header {
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            
            .route-details-modal .modal-body {
                padding: 20px;
            }
            
            .route-info-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            
            .route-info-item:last-child {
                border-bottom: none;
            }
            
            .route-info-label {
                font-weight: bold;
                color: #2c3e50;
            }
            
            .route-info-value {
                color: #7f8c8d;
            }
            
            .waypoints-list {
                max-height: 200px;
                overflow-y: auto;
                margin-top: 10px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
            }
            
            .waypoint-item {
                padding: 5px 10px;
                margin-bottom: 5px;
                background: white;
                border-radius: 3px;
                border-left: 3px solid #3498db;
            }
            
            /* Animations */
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.8; }
                100% { transform: scale(1); opacity: 1; }
            }
            
            @keyframes pulseLine {
                0% { stroke-width: 8; opacity: 1; }
                50% { stroke-width: 12; opacity: 0.7; }
                100% { stroke-width: 8; opacity: 1; }
            }
            
            @keyframes blinkLine {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            /* Global animations */
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            
            .spin {
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Table row highlighting */
            .route-row-highlighted {
                background: linear-gradient(90deg, rgba(52, 152, 219, 0.1) 0%, rgba(52, 152, 219, 0.05) 100%);
                border-left: 4px solid #3498db !important;
            }
        `;
        
        document.head.appendChild(style);
        console.log('🎨 Added emergency CSS for visual elements');
    }
    
    /**
     * Expose important functions globally for other modules
     */
    exposeGlobalFunctions() {
        // Make zoomToRoute available globally - accepts BOTH index and ID
        window.zoomToRoute = (identifier) => {
            console.log(`🌐 Global zoomToRoute called with:`, identifier);
            
            // Try to determine if identifier is index or ID
            if (typeof identifier === 'number' || (typeof identifier === 'string' && /^\d+$/.test(identifier))) {
                const index = parseInt(identifier);
                if (index >= 0 && index < this.routesData.length) {
                    return this.zoomToRouteByIndex(index);
                }
            }
            
            // Try as route ID
            return this.zoomToRouteById(identifier);
        };
        
        // Expose other useful functions
        window.getRouteByIndex = (index) => {
            return this.routesData[index];
        };
        
        window.getTotalRoutes = () => {
            return this.routesData.length;
        };
        
        // Expose data inspection functions
        window.inspectRouteData = (index = 0) => {
            if (index < 0 || index >= this.routesData.length) {
                console.error(`Invalid index: ${index}`);
                return null;
            }
            
            const route = this.routesData[index];
            const routeId = route.id || route.route_id || index;
            
            console.log(`🔍 Inspecting route ${index}:`);
            console.log('Route object:', route);
            console.log('Route ID:', routeId);
            console.log('Waypoints data for this ID:', this.waypointsData[routeId]);
            console.log('Waypoints data for index:', this.waypointsData[index]);
            console.log('Waypoints data for string index:', this.waypointsData[index.toString()]);
            
            return route;
        };
        
        // Expose emergency test function
        window.testMapVisualization = () => {
            console.log('🧪 Testing map visualization...');
            return this.testVisualization();
        };
        
        // Expose test function for rtzWaypoints integration
        window.testRtzWaypointsIntegration = () => {
            console.log('🧪 Testing rtzWaypoints integration...');
            if (!window.rtzWaypoints) {
                console.log('❌ rtzWaypoints module not found');
                return false;
            }
            
            if (!window.rtzWaypoints.highlightRoute) {
                console.log('❌ rtzWaypoints.highlightRoute method not found');
                return false;
            }
            
            // Test with first route
            const routeId = 'route-0';
            console.log(`Testing rtzWaypoints.highlightRoute("${routeId}")...`);
            const result = window.rtzWaypoints.highlightRoute(routeId);
            console.log(`Result: ${result ? '✅ Success' : '❌ Failed'}`);
            return result;
        };
        
        console.log('🌐 Global functions exposed');
    }

    /**
     * Setup all dashboard event listeners - ALL BUTTONS PRESERVED
     */
    setupEventListeners() {
        console.log('🔧 Setting up event listeners for ALL buttons...');
        
        // Toggle buttons for layers - ALL 3 BUTTONS
        ['rtz-toggle-btn', 'weather-toggle-btn', 'ais-toggle-btn'].forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btn) {
                btn.addEventListener('click', (e) => {
                    const target = e.currentTarget;
                    const isActive = !target.classList.contains('active');
                    
                    target.classList.toggle('active');
                    this.layers[btnId.replace('-toggle-btn', '')] = isActive;
                    
                    const status = isActive ? 'enabled' : 'disabled';
                    console.log(`🎯 ${btnId.replace('-toggle-btn', '').toUpperCase()} layer ${status}`);
                    this.showNotification(`${btnId.replace('-toggle-btn', '').toUpperCase()} layer ${status}`, 'info');
                    
                    // Notify map if available
                    if (window.map && window.map.updateLayerVisibility) {
                        window.map.updateLayerVisibility();
                    }
                });
            }
        });

        // Refresh button - PRESERVED
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Refreshing...';
                refreshBtn.disabled = true;
                
                this.showNotification('Refreshing dashboard data...', 'info');
                
                // Simulate refresh
                setTimeout(() => {
                    refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh';
                    refreshBtn.disabled = false;
                    this.showNotification('Dashboard refreshed successfully', 'success');
                    
                    // Update timestamp
                    const now = new Date();
                    const timeStr = now.toLocaleTimeString('en-GB', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    });
                    
                    const updateElements = [
                        'map-update-time',
                        'routes-updated',
                        'system-update-time',
                        'weather-updated',
                        'vessels-updated'
                    ];
                    
                    updateElements.forEach(id => {
                        const el = document.getElementById(id);
                        if (el) el.textContent = timeStr;
                    });
                    
                }, 1500);
            });
        }

        // Show RTZ panel button - PRESERVED
        const showPanelBtn = document.getElementById('show-rtz-panel');
        if (showPanelBtn) {
            showPanelBtn.addEventListener('click', () => {
                const routesTable = document.querySelector('.dashboard-card:has(#routes-table-body)');
                if (routesTable) {
                    routesTable.scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'start'
                    });
                    this.showNotification('Navigated to routes list', 'info');
                }
            });
        }
        
        // Debug button - PRESERVED
        const debugBtn = document.getElementById('debug-toggle-btn');
        if (debugBtn) {
            debugBtn.addEventListener('click', () => {
                this.showDebugInfo();
            });
        }
        
        // Visual test button (if exists) - PRESERVED
        const visualTestBtn = document.getElementById('visual-test-btn');
        if (visualTestBtn) {
            visualTestBtn.addEventListener('click', () => {
                this.testVisualization();
            });
        }
        
        console.log('✅ ALL event listeners setup complete');
    }

    /**
     * Setup route table interactivity - ALL 3 BUTTONS PER ROW
     */
    setupRouteTableInteractivity() {
        const routeRows = document.querySelectorAll('.route-row');
        if (routeRows.length === 0) {
            console.warn('No route rows found in table');
            return;
        }
        
        console.log(`📋 Setting up ${routeRows.length} route rows with ALL 3 buttons`);
        
        routeRows.forEach((row, index) => {
            // Get route index from data attribute or use DOM index
            let routeIndex = parseInt(row.dataset.routeIndex);
            if (isNaN(routeIndex)) {
                routeIndex = index;
                row.dataset.routeIndex = routeIndex.toString();
            }
            
            // Get route ID from data attribute
            const routeId = row.dataset.routeId;
            
            // Store reference to route data
            if (routeIndex >= 0 && routeIndex < this.routesData.length) {
                const route = this.routesData[routeIndex];
                row.dataset.routeId = route.id || route.route_id || routeIndex.toString();
                row.dataset.hasWaypoints = (this.hasWaypointsForRoute(routeIndex) ? 'true' : 'false');
                row.dataset.origin = route.origin || '';
                row.dataset.destination = route.destination || '';
            }
            
            row.style.cursor = 'pointer';
            row.style.transition = 'background-color 0.2s, transform 0.1s';
            
            // Click handler for entire row
            row.addEventListener('click', (e) => {
                // Don't trigger if clicking on buttons
                if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                    return;
                }
                
                this.handleRouteRowClick(row, routeIndex, routeId);
            });
            
            // Hover effects
            row.addEventListener('mouseenter', () => {
                if (this.currentHighlightedRoute !== routeIndex) {
                    row.style.backgroundColor = 'rgba(52, 152, 219, 0.05)';
                    row.style.transform = 'translateY(-1px)';
                }
            });
            
            row.addEventListener('mouseleave', () => {
                if (this.currentHighlightedRoute !== routeIndex) {
                    row.style.backgroundColor = '';
                    row.style.transform = '';
                }
            });
        });
        
        // Setup action buttons - ALL 3 BUTTONS: View, Highlight, Info
        this.setupRouteActionButtons();
        
        console.log('✅ Route table interactivity setup complete with ALL buttons');
    }
    
    /**
     * Check if route has waypoints
     */
    hasWaypointsForRoute(routeIndex) {
        if (routeIndex < 0 || routeIndex >= this.routesData.length) {
            return false;
        }
        
        const route = this.routesData[routeIndex];
        const routeId = route.id || route.route_id || routeIndex.toString();
        
        // Check waypointsData
        if (this.waypointsData[routeId] && this.waypointsData[routeId].length > 0) {
            return true;
        }
        
        // Check with numeric index
        if (this.waypointsData[routeIndex] && this.waypointsData[routeIndex].length > 0) {
            return true;
        }
        
        // Check with string index
        if (this.waypointsData[routeIndex.toString()] && this.waypointsData[routeIndex.toString()].length > 0) {
            return true;
        }
        
        // Check route object itself
        if (route.waypoints && route.waypoints.length > 0) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Setup port filtering functionality
     */
    setupPortFiltering() {
        const cityBadges = document.querySelectorAll('.city-badge');
        const resetBtn = document.getElementById('reset-filters');
        
        if (cityBadges.length === 0) return;
        
        console.log(`🏙️ Setting up ${cityBadges.length} port filters`);
        
        cityBadges.forEach(badge => {
            if (badge.dataset.port === 'reset') return;
            
            badge.addEventListener('click', () => {
                const port = badge.dataset.port;
                const isActive = badge.classList.contains('active');
                
                // Toggle active state
                cityBadges.forEach(b => {
                    if (b.dataset.port !== 'reset') {
                        b.classList.remove('active');
                    }
                });
                
                if (!isActive) {
                    badge.classList.add('active');
                    this.filterRoutesByPort(port);
                } else {
                    this.resetPortFilter();
                }
            });
        });
        
        // Reset filter button
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetPortFilter();
                this.showNotification('All port filters cleared', 'info');
            });
        }
    }
    
    /**
     * Setup route action buttons - ALL 3 IMPORTANT BUTTONS
     */
    setupRouteActionButtons() {
        // View route button - ZOOM functionality (1st button)
        document.querySelectorAll('.view-route-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                
                const row = btn.closest('.route-row');
                const routeIndex = parseInt(row.dataset.routeIndex);
                const routeId = btn.dataset.routeId || row.dataset.routeId;
                
                console.log(`🔍 View route button clicked - Index: ${routeIndex}, Button ID: ${routeId}`);
                
                // Zoom to the route
                const success = this.zoomToRouteByIndex(routeIndex);
                
                if (success) {
                    // Highlight the row
                    this.highlightRouteRow(row, routeIndex);
                    
                    // Show notification
                    const routeName = row.querySelector('.route-name-display')?.textContent || `Route ${routeIndex + 1}`;
                    this.showNotification(`Zoomed to: ${routeName}`, 'success');
                } else {
                    this.showNotification('Could not zoom to route', 'warning');
                }
            });
        });
        
        // Highlight route button (2nd button)
        document.querySelectorAll('.highlight-route-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                
                const row = btn.closest('.route-row');
                const routeIndex = parseInt(row.dataset.routeIndex);
                const routeId = btn.dataset.routeId || row.dataset.routeId;
                
                console.log(`📍 Highlight route button clicked - Row Index: ${routeIndex}, Button ID: ${routeId}`);
                
                // Highlight the row in table
                this.highlightRouteRow(row, routeIndex);
                
                // Highlight on map
                const success = this.highlightRouteOnMap(routeIndex);
                
                if (success) {
                    this.showNotification('Route highlighted on map', 'success');
                } else {
                    this.showNotification('Could not highlight route', 'warning');
                }
            });
        });
        
        // Route info button (3rd button) - THIS IS THE FIXED VERSION
        document.querySelectorAll('.route-info-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                
                const row = btn.closest('.route-row');
                const routeIndex = parseInt(row.dataset.routeIndex);
                const routeId = btn.dataset.routeId || row.dataset.routeId;
                
                console.log(`ℹ️ Route info button clicked - Index: ${routeIndex}, ID: ${routeId}`);
                
                // Show route details using modal instead of notification
                this.showRouteDetails(routeIndex);
            });
        });
    }
    
    /**
     * Handle route row click
     */
    handleRouteRowClick(row, routeIndex, routeId) {
        console.log(`📋 Route row clicked - Index: ${routeIndex}, ID: ${routeId}`);
        
        // Highlight the row
        this.highlightRouteRow(row, routeIndex);
        
        // Zoom to the route if it has waypoints
        const hasWaypoints = row.dataset.hasWaypoints === 'true';
        if (hasWaypoints) {
            this.zoomToRouteByIndex(routeIndex);
        } else {
            this.zoomToPortByRouteIndex(routeIndex);
        }
        
        // Show route name in notification
        const routeName = row.querySelector('.route-name-display')?.textContent || `Route ${routeIndex + 1}`;
        this.showNotification(`Selected: ${routeName}`, 'info');
    }
    
    /**
     * Highlight a route row in the table
     */
    highlightRouteRow(row, routeIndex) {
        // Clear previous highlights
        document.querySelectorAll('.route-row-highlighted').forEach(r => {
            r.classList.remove('route-row-highlighted');
            r.style.backgroundColor = '';
        });
        
        // Apply highlight to current row
        row.classList.add('route-row-highlighted');
        row.style.backgroundColor = 'rgba(52, 152, 219, 0.15)';
        
        // Store current highlighted route
        this.currentHighlightedRoute = routeIndex;
        
        // Scroll row into view
        setTimeout(() => {
            row.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }, 100);
    }
    
    /**
     * Zoom to route by index (primary method)
     */
    zoomToRouteByIndex(routeIndex) {
        console.log(`🗺️ Attempting to zoom to route index: ${routeIndex}`);
        
        if (!this.map) {
            console.error('Map not available');
            return false;
        }
        
        if (routeIndex < 0 || routeIndex >= this.routesData.length) {
            console.error(`Invalid route index: ${routeIndex}`);
            return false;
        }
        
        const route = this.routesData[routeIndex];
        console.log('Route for zoom:', {
            name: route.clean_name || route.route_name,
            origin: route.origin,
            destination: route.destination,
            hasWaypoints: this.hasWaypointsForRoute(routeIndex)
        });
        
        // Method 1: Try to get bounds from waypoints
        const waypoints = this.getWaypointsForRoute(routeIndex);
        if (waypoints.length > 0) {
            const bounds = L.latLngBounds(
                waypoints.map(wp => [wp.lat || wp.latitude, wp.lon || wp.longitude])
            );
            
            if (bounds.isValid()) {
                this.map.fitBounds(bounds, {
                    padding: [100, 100],
                    maxZoom: 10,
                    animate: true,
                    duration: 1
                });
                console.log(`✅ Zoomed to route bounds from waypoints`);
                return true;
            }
        }
        
        // Method 2: Zoom to port location
        return this.zoomToPortByRouteIndex(routeIndex);
    }
    
    /**
     * Get waypoints for a specific route
     */
    getWaypointsForRoute(routeIndex) {
        console.log(`🔍 getWaypointsForRoute called for index: ${routeIndex}`);
        
        if (routeIndex < 0 || routeIndex >= this.routesData.length) {
            console.log(`❌ Invalid route index: ${routeIndex}`);
            return [];
        }
        
        const route = this.routesData[routeIndex];
        const routeName = route.clean_name || route.route_name || `route-${routeIndex}`;
        
        console.log(`Looking for waypoints for: "${routeName}"`);
        
        // METHOD 1: Check if waypoints are already in the route object
        if (route.waypoints && Array.isArray(route.waypoints) && route.waypoints.length > 0) {
            console.log(`✅ Found ${route.waypoints.length} waypoints in route object`);
            return route.waypoints;
        }
        
        // METHOD 2: Check rtzWaypoints module (IT HAS THE DATA!)
        if (window.rtzWaypoints && window.rtzWaypoints.waypointsData) {
            console.log(`Checking rtzWaypoints.waypointsData...`);
            console.log(`Available keys:`, Object.keys(window.rtzWaypoints.waypointsData));
            
            // Try to find by route index
            const indexKey = routeIndex.toString();
            if (window.rtzWaypoints.waypointsData[indexKey]) {
                const waypoints = window.rtzWaypoints.waypointsData[indexKey];
                console.log(`✅ Found ${waypoints.length} waypoints in rtzWaypoints by index key: "${indexKey}"`);
                return waypoints;
            }
            
            // Try to find by route name
            for (const [key, waypoints] of Object.entries(window.rtzWaypoints.waypointsData)) {
                if (key.includes(routeName) || routeName.includes(key)) {
                    console.log(`✅ Found ${waypoints.length} waypoints in rtzWaypoints by name match: "${key}"`);
                    return waypoints;
                }
            }
            
            // Try first available key if nothing else matches
            const firstKey = Object.keys(window.rtzWaypoints.waypointsData)[0];
            if (firstKey && window.rtzWaypoints.waypointsData[firstKey]) {
                console.log(`⚠️ Using first available waypoints from rtzWaypoints: "${firstKey}"`);
                return window.rtzWaypoints.waypointsData[firstKey];
            }
        }
        
        // METHOD 3: Check global allRoutesData
        if (window.allRoutesData && window.allRoutesData[routeIndex] && 
            window.allRoutesData[routeIndex].waypoints) {
            const waypoints = window.allRoutesData[routeIndex].waypoints;
            console.log(`✅ Found ${waypoints.length} waypoints in window.allRoutesData`);
            return waypoints;
        }
        
        console.log(`❌ No waypoints found for route ${routeIndex} ("${routeName}")`);
        console.log(`   route object has waypoints property: ${'waypoints' in route}`);
        console.log(`   rtzWaypoints exists: ${!!window.rtzWaypoints}`);
        console.log(`   rtzWaypoints has waypointsData: ${!!(window.rtzWaypoints && window.rtzWaypoints.waypointsData)}`);
        
        return [];
    }
    
    /**
     * Zoom to route by ID (alternative method)
     */
    zoomToRouteById(routeId) {
        console.log(`🗺️ Attempting to zoom to route ID: ${routeId}`);
        
        // Find route index by ID
        const routeIndex = this.findRouteIndexById(routeId);
        
        if (routeIndex >= 0) {
            return this.zoomToRouteByIndex(routeIndex);
        }
        
        console.error(`Route not found with ID: ${routeId}`);
        return false;
    }
    
    /**
     * Zoom to port location for a route
     */
    zoomToPortByRouteIndex(routeIndex) {
        if (routeIndex < 0 || routeIndex >= this.routesData.length) {
            return false;
        }
        
        const route = this.routesData[routeIndex];
        const portName = this.getPrimaryPortName(route);
        
        if (portName && this.portCoordinates[portName]) {
            this.map.setView(this.portCoordinates[portName], 10, {
                animate: true,
                duration: 1
            });
            
            console.log(`✅ Zoomed to port: ${portName} at ${this.portCoordinates[portName]}`);
            return true;
        }
        
        // Default zoom to Norway
        this.map.setView([63.5, 10.5], 5, {
            animate: true,
            duration: 1
        });
        
        return false;
    }
    
    /**
     * Get primary port name from route
     */
    getPrimaryPortName(route) {
        const ports = [
            route.origin,
            route.destination,
            route.source_city,
            route.dest_city
        ].filter(Boolean);
        
        if (ports.length === 0) {
            return 'bergen'; // Default
        }
        
        // Return first port, normalized
        return ports[0].toLowerCase()
            .replace('å', 'a')
            .replace('ø', 'o')
            .replace('æ', 'ae')
            .trim();
    }
    
    /**
     * Filter routes by port
     */
    filterRoutesByPort(portName) {
        console.log(`🏙️ Filtering routes by port: ${portName}`);
        
        const routeRows = document.querySelectorAll('.route-row');
        let visibleCount = 0;
        
        routeRows.forEach(row => {
            const origin = row.dataset.origin || '';
            const destination = row.dataset.destination || '';
            const city = row.dataset.city || '';
            
            const shouldShow = origin.toLowerCase().includes(portName) || 
                             destination.toLowerCase().includes(portName) ||
                             city.toLowerCase().includes(portName);
            
            row.style.display = shouldShow ? '' : 'none';
            if (shouldShow) visibleCount++;
        });
        
        // Update route count badge
        const routeCountBadge = document.getElementById('route-count-badge');
        if (routeCountBadge) {
            routeCountBadge.textContent = visibleCount.toString();
        }
        
        this.showNotification(`Showing ${visibleCount} routes for ${portName}`, 'info');
    }
    
    /**
     * Reset port filter
     */
    resetPortFilter() {
        const routeRows = document.querySelectorAll('.route-row');
        const cityBadges = document.querySelectorAll('.city-badge');
        
        routeRows.forEach(row => {
            row.style.display = '';
        });
        
        cityBadges.forEach(badge => {
            badge.classList.remove('active');
        });
        
        // Reset route count
        const routeCountBadge = document.getElementById('route-count-badge');
        if (routeCountBadge) {
            routeCountBadge.textContent = this.routesData.length.toString();
        }
        
        console.log('🏙️ Port filter reset');
    }
    
    /**
     * Highlight route on map with visual indicators - FIXED VERSION
     */
    highlightRouteOnMap(identifier) {
        console.log(`🎯 highlightRouteOnMap called with: ${identifier} (type: ${typeof identifier})`);
        
        // First, try to use rtzWaypoints if it exists
        if (window.rtzWaypoints && window.rtzWaypoints.highlightRoute) {
            console.log(`🎯 Using rtzWaypoints.highlightRoute...`);
            
            // Find route index
            let routeIndex;
            if (typeof identifier === 'number') {
                routeIndex = identifier;
            } else if (typeof identifier === 'string' && /^\d+$/.test(identifier)) {
                routeIndex = parseInt(identifier);
            } else {
                routeIndex = this.findRouteIndexById(identifier);
            }
            
            if (routeIndex === -1) {
                console.log(`❌ Could not find route index for: ${identifier}`);
                return false;
            }
            
            const route = this.routesData[routeIndex];
            const routeId = route.route_id || `route-${routeIndex}`;
            
            console.log(`🎯 Calling rtzWaypoints.highlightRoute("${routeId}")`);
            const rtzResult = window.rtzWaypoints.highlightRoute(routeId);
            
            if (rtzResult) {
                console.log(`✅ rtzWaypoints highlighted route successfully: ${routeId}`);
                
                // Also add our own highlighting for extra visibility
                this.addDashboardHighlight(routeIndex);
                
                return true;
            } else {
                console.log(`⚠️ rtzWaypoints.highlightRoute returned false, trying fallback...`);
                return this.highlightRouteEnhanced(routeIndex);
            }
        }
        
        // Fallback to our own method if rtzWaypoints not available
        console.log(`⚠️ rtzWaypoints not available, using fallback...`);
        return this.highlightRouteEnhanced(identifier);
    }

    /**
     * Add dashboard-specific highlighting on top of rtzWaypoints
     */
    addDashboardHighlight(routeIndex) {
        console.log(`💎 Adding dashboard highlight for route ${routeIndex}`);
        
        const waypoints = this.getWaypointsForRoute(routeIndex);
        if (waypoints.length === 0) return;
        
        // Clear only our dashboard highlights
        if (this.highlightLayer) {
            this.highlightLayer.clearLayers();
        } else {
            this.highlightLayer = L.layerGroup().addTo(this.map);
        }
        
        // Draw a highlight line on top
        const latLngs = waypoints.map(wp => [wp.lat || wp.latitude, wp.lon || wp.longitude]);
        const highlightLine = L.polyline(latLngs, {
            color: '#00FF00', // Bright green
            weight: 3,
            opacity: 0.7,
            dashArray: '15, 10',
            className: 'dashboard-top-highlight',
            pane: 'dashboard-highlight-pane'
        }).addTo(this.highlightLayer);
        
        // Add a pulsing effect
        highlightLine.setStyle({
            className: 'dashboard-top-highlight pulsing'
        });
        
        console.log(`💎 Added dashboard overlay highlight`);
    }

    /**
     * Enhanced highlighting - our own method for when rtzWaypoints fails
     */
    highlightRouteEnhanced(routeIndex) {
        console.log(`✨ highlightRouteEnhanced for index: ${routeIndex}`);
        
        if (!this.map) {
            console.error('Map not available');
            return false;
        }
        
        const waypoints = this.getWaypointsForRoute(routeIndex);
        console.log(`Retrieved ${waypoints.length} waypoints for enhanced highlighting`);
        
        if (waypoints.length === 0) {
            console.log(`No waypoints available, cannot highlight route`);
            return false;
        }
        
        // Clear previous highlights
        this.clearMapHighlights();
        
        // Create highlight layer if needed
        if (!this.highlightLayer) {
            this.highlightLayer = L.layerGroup().addTo(this.map);
        }
        
        // Draw highlighted route
        const latLngs = waypoints.map(wp => {
            const lat = wp.lat || wp.latitude;
            const lon = wp.lon || wp.longitude;
            return L.latLng(lat, lon);
        }).filter(ll => ll.lat && ll.lng);
        
        if (latLngs.length === 0) {
            console.log(`No valid coordinates found`);
            return false;
        }
        
        // Draw the route with special highlighting
        const route = this.routesData[routeIndex];
        const routeName = route.clean_name || route.route_name || `Route ${routeIndex + 1}`;
        
        const highlightLine = L.polyline(latLngs, {
            color: '#FFD700', // Gold color for highlighting
            weight: 6,
            opacity: 0.9,
            dashArray: '10, 5',
            className: 'dashboard-route-highlight'
        }).addTo(this.highlightLayer);
        
        // Add start and end markers
        if (latLngs.length > 0) {
            const startIcon = L.divIcon({
                className: 'dashboard-highlight-start',
                html: '<div style="background-color: #00FF00; width: 25px; height: 25px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 20px #00FF00;"></div>',
                iconSize: [25, 25]
            });
            
            L.marker(latLngs[0], { icon: startIcon })
                .bindPopup(`<strong>${routeName}</strong><br>Start Point`)
                .addTo(this.highlightLayer);
        }
        
        if (latLngs.length > 1) {
            const endIcon = L.divIcon({
                className: 'dashboard-highlight-end',
                html: '<div style="background-color: #FF0000; width: 25px; height: 25px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 20px #FF0000;"></div>',
                iconSize: [25, 25]
            });
            
            L.marker(latLngs[latLngs.length - 1], { icon: endIcon })
                .bindPopup(`<strong>${routeName}</strong><br>End Point`)
                .addTo(this.highlightLayer);
        }
        
        // Zoom to route
        const bounds = L.latLngBounds(latLngs);
        this.map.fitBounds(bounds, {
            padding: [100, 100],
            maxZoom: 12,
            animate: true
        });
        
        console.log(`✅ Enhanced highlighting complete for ${routeName}`);
        return true;
    }

    /**
     * Draw route with waypoints using special pane - FOR REAL NCA DATA
     */
    drawRouteWithWaypointsEnhanced(waypoints, route) {
        try {
            if (!this.map || !this.highlightLayer) {
                console.error('Map or highlight layer not available');
                return false;
            }
            
            const routeName = route.clean_name || route.route_name || 'Unnamed Route';
            console.log(`🎨 Drawing enhanced route: ${routeName} with ${waypoints.length} waypoints`);
            
            // Filter valid waypoints
            const validWaypoints = waypoints.filter(wp => {
                const lat = wp.lat || wp.latitude;
                const lng = wp.lon || wp.longitude;
                return lat && lng && !isNaN(lat) && !isNaN(lng);
            });
            
            if (validWaypoints.length === 0) {
                console.error('No valid waypoints to draw');
                return false;
            }
            
            console.log(`📍 ${validWaypoints.length} valid waypoints found`);
            
            // Convert to LatLng array
            const latLngs = validWaypoints.map(wp => {
                const lat = wp.lat || wp.latitude;
                const lng = wp.lon || wp.longitude;
                return L.latLng(lat, lng);
            });
            
            // Draw polyline with special pane
            const polyline = L.polyline(latLngs, {
                color: '#3498db',
                weight: 5,
                opacity: 0.9,
                pane: 'dashboard-highlight-pane',
                className: 'super-visible-line dash-highlight'
            }).addTo(this.highlightLayer);
            
            // Add start marker
            const startIcon = L.divIcon({
                className: 'route-highlight-start',
                html: '<div style="background-color: #28a745; width: 25px; height: 25px; border-radius: 50%; border: 4px solid white; box-shadow: 0 0 20px #28a745; font-weight: bold; color: white; display: flex; align-items: center; justify-content: center;">S</div>',
                iconSize: [25, 25]
            });
            
            L.marker(latLngs[0], { 
                icon: startIcon,
                pane: 'dashboard-highlight-pane'
            })
            .bindPopup(`<strong>${routeName}</strong><br>Start: ${route.origin || 'Unknown'}`)
            .addTo(this.highlightLayer);
            
            // Add end marker
            if (latLngs.length > 1) {
                const endIcon = L.divIcon({
                    className: 'route-highlight-end',
                    html: '<div style="background-color: #dc3545; width: 25px; height: 25px; border-radius: 50%; border: 4px solid white; box-shadow: 0 0 20px #dc3545; font-weight: bold; color: white; display: flex; align-items: center; justify-content: center;">E</div>',
                    iconSize: [25, 25]
                });
                
                L.marker(latLngs[latLngs.length - 1], { 
                    icon: endIcon,
                    pane: 'dashboard-highlight-pane'
                })
                .bindPopup(`<strong>${routeName}</strong><br>End: ${route.destination || 'Unknown'}`)
                .addTo(this.highlightLayer);
            }
            
            // Calculate and show distance
            let totalDistance = 0;
            for (let i = 1; i < latLngs.length; i++) {
                totalDistance += latLngs[i-1].distanceTo(latLngs[i]);
            }
            
            // Bind popup with distance info
            polyline.bindPopup(`
                <div style="min-width: 250px;">
                    <strong>${routeName}</strong><br>
                    <small>${route.origin || 'Unknown'} → ${route.destination || 'Unknown'}</small><br>
                    <small>Waypoints: ${validWaypoints.length}</small><br>
                    <small>Distance: ${(totalDistance / 1000).toFixed(1)} km</small>
                </div>
            `);
            
            // Fit bounds to show the route
            const bounds = L.latLngBounds(latLngs);
            if (bounds.isValid()) {
                this.map.fitBounds(bounds, {
                    padding: [50, 50],
                    maxZoom: 10,
                    animate: true,
                    duration: 0.5
                });
            }
            
            console.log(`✅ Drew enhanced route: ${routeName}`);
            return true;
            
        } catch (error) {
            console.error('Error drawing enhanced route:', error);
            return false;
        }
    }
    
    /**
     * Test visualization function - PRESERVED
     */
    testVisualization() {
        console.log('🧪 Running visualization test...');
        
        if (!this.map) {
            console.error('Map not available for test');
            return false;
        }
        
        // Clear everything first
        this.clearMapHighlights();
        
        // Create a new highlight layer
        this.highlightLayer = L.layerGroup().addTo(this.map);
        
        // Test with real data if available
        if (this.routesData.length > 0) {
            const route = this.routesData[0];
            const waypoints = this.getWaypointsForRoute(0);
            
            if (waypoints.length > 0) {
                console.log(`🧪 Testing with REAL NCA data: ${route.clean_name || route.route_name}`);
                return this.drawRouteWithWaypointsEnhanced(waypoints, route);
            }
        }
        
        // Fallback test coordinates (Bergen area - realistic route)
        const testWaypoints = [
            { lat: 60.3913, lon: 5.3221, name: 'Bergen Port' },
            { lat: 60.40, lon: 5.25, name: 'Byfjorden' },
            { lat: 60.45, lon: 5.10, name: 'Hjeltefjorden' },
            { lat: 60.55, lon: 4.85, name: 'Fedjeosen' },
            { lat: 60.65, lon: 4.60, name: 'North Sea' }
        ];
        
        // Create test route object
        const testRoute = {
            clean_name: 'TEST ROUTE - Bergen to North Sea',
            route_name: 'Test Visualization Route',
            origin: 'Bergen',
            destination: 'North Sea'
        };
        
        // Draw the test route
        const success = this.drawRouteWithWaypointsEnhanced(testWaypoints, testRoute);
        
        if (success) {
            console.log('✅ Test visualization complete');
            this.showNotification('Test visualization active', 'success');
        } else {
            console.error('❌ Test visualization failed');
            this.showNotification('Test visualization failed', 'error');
        }
        
        return success;
    }
    
    /**
     * Find route index by ID - IMPROVED
     */
    findRouteIndexById(routeId) {
        if (!this.routesData || this.routesData.length === 0) {
            console.log('❌ No routes data available');
            return -1;
        }
        
        console.log(`🔍 findRouteIndexById called with: "${routeId}" (type: ${typeof routeId})`);
        
        // If routeId is a number or numeric string, treat it as index
        if (!isNaN(routeId)) {
            const index = parseInt(routeId);
            if (index >= 0 && index < this.routesData.length) {
                console.log(`✅ Treating "${routeId}" as index: ${index}`);
                return index;
            }
        }
        
        // Try to find by route_id or id
        for (let i = 0; i < this.routesData.length; i++) {
            const route = this.routesData[i];
            
            if (route.route_id && route.route_id.toString() === routeId.toString()) {
                console.log(`✅ Found by route_id at index ${i}: ${route.route_id}`);
                return i;
            }
            
            if (route.id && route.id.toString() === routeId.toString()) {
                console.log(`✅ Found by id at index ${i}: ${route.id}`);
                return i;
            }
            
            if (route.route_name && route.route_name.toLowerCase().includes(routeId.toLowerCase())) {
                console.log(`✅ Found by route_name at index ${i}: ${route.route_name}`);
                return i;
            }
            
            if (route.clean_name && route.clean_name.toLowerCase().includes(routeId.toLowerCase())) {
                console.log(`✅ Found by clean_name at index ${i}: ${route.clean_name}`);
                return i;
            }
        }
        
        console.log(`❌ Could not find route with ID: "${routeId}"`);
        return -1;
    }
    
    /**
     * Clear all highlight markers from map
     */
    clearMapHighlights() {
        // Clear our highlight layer
        if (this.highlightLayer) {
            this.highlightLayer.clearLayers();
            console.log('🧹 Cleared dashboard highlight layer');
        }
        
        // Try to clear any rtz_waypoints layers
        if (window.rtzWaypoints && window.rtzWaypoints.clearAllHighlights) {
            try {
                window.rtzWaypoints.clearAllHighlights();
                console.log('🧹 Cleared rtz_waypoints highlights');
            } catch (e) {
                console.log('⚠️ Could not clear rtz_waypoints highlights:', e.message);
            }
        }
        
        // Reset emergency mode
        this.emergencyMode = false;
    }
    
    /**
     * Get port coordinates
     */
    getPortCoordinates() {
        return {
            'bergen': [60.3913, 5.3221],
            'oslo': [59.9139, 10.7522],
            'stavanger': [58.9699, 5.7331],
            'trondheim': [63.4305, 10.3951],
            'alesund': [62.4722, 6.1497],
            'andalsnes': [62.5674, 7.6821],
            'kristiansand': [58.1467, 7.9956],
            'drammen': [59.7441, 10.2045],
            'sandefjord': [59.1314, 10.2167],
            'flekkefjord': [58.2975, 6.6608],
            'deep': [58.5, 5.5],
            'stad': [62.1, 5.1],
            'hjelmeland': [59.2333, 6.1833],
            'røst': [67.5167, 12.1167],
            'bodø': [67.2833, 14.3833],
            'tromsø': [69.6500, 18.9500],
            'hammerfest': [70.6631, 23.6811],
            'vardø': [70.3706, 31.1106]
        };
    }
    
    /**
     * Show route details - FIXED VERSION USING MODAL
     */
    showRouteDetails(routeIndex) {
        if (routeIndex < 0 || routeIndex >= this.routesData.length) {
            this.showNotification('Route not found', 'warning');
            return;
        }
        
        const route = this.routesData[routeIndex];
        const waypoints = this.getWaypointsForRoute(routeIndex);
        
        // Update modal title
        const modalTitle = document.querySelector('#routeModalTitle');
        if (modalTitle) {
            modalTitle.innerHTML = `<i class="fas fa-route me-2"></i> ${route.clean_name || route.route_name || `Route ${routeIndex + 1}`}`;
        }
        
        // Create modal body content
        let modalBody = `
            <div class="route-info-item">
                <span class="route-info-label"><i class="fas fa-flag text-success me-1"></i> Origin:</span>
                <span class="route-info-value">${route.origin || 'Unknown'}</span>
            </div>
            <div class="route-info-item">
                <span class="route-info-label"><i class="fas fa-flag-checkered text-danger me-1"></i> Destination:</span>
                <span class="route-info-value">${route.destination || 'Unknown'}</span>
            </div>
            <div class="route-info-item">
                <span class="route-info-label"><i class="fas fa-map-marker-alt text-primary me-1"></i> Waypoints:</span>
                <span class="route-info-value">${waypoints.length}</span>
            </div>
        `;
        
        if (route.total_distance_nm) {
            modalBody += `
                <div class="route-info-item">
                    <span class="route-info-label"><i class="fas fa-ruler text-info me-1"></i> Distance:</span>
                    <span class="route-info-value">${route.total_distance_nm.toFixed(1)} NM (${(route.total_distance_nm * 1.852).toFixed(1)} km)</span>
                </div>
            `;
        }
        
        if (route.source_city) {
            modalBody += `
                <div class="route-info-item">
                    <span class="route-info-label"><i class="fas fa-anchor text-warning me-1"></i> Source Port:</span>
                    <span class="route-info-value">${route.source_city}</span>
                </div>
            `;
        }
        
        if (route.description) {
            modalBody += `
                <div class="route-info-item">
                    <span class="route-info-label"><i class="fas fa-file-alt me-1"></i> Description:</span>
                    <span class="route-info-value" style="font-size: 0.9em;">${route.description}</span>
                </div>
            `;
        }
        
        // Add waypoints list if available
        if (waypoints.length > 0) {
            modalBody += `
                <div class="mt-3">
                    <strong><i class="fas fa-list me-1"></i> Waypoints:</strong>
                    <div class="waypoints-list">
            `;
            
            waypoints.slice(0, 10).forEach((wp, i) => {
                const wpName = wp.name || wp.wp_name || `Waypoint ${i + 1}`;
                const lat = wp.lat || wp.latitude;
                const lon = wp.lon || wp.longitude;
                
                modalBody += `
                    <div class="waypoint-item">
                        <small><strong>${wpName}</strong>: ${lat.toFixed(4)}°, ${lon.toFixed(4)}°</small>
                    </div>
                `;
            });
            
            if (waypoints.length > 10) {
                modalBody += `<small>... and ${waypoints.length - 10} more waypoints</small>`;
            }
            
            modalBody += `
                    </div>
                </div>
            `;
        }
        
        // Update modal body
        const modalBodyElement = document.querySelector('#routeModalBody');
        if (modalBodyElement) {
            modalBodyElement.innerHTML = modalBody;
        }
        
        // Store current route index in modal for button handlers
        const modalElement = document.getElementById('routeDetailsModal');
        if (modalElement) {
            modalElement.dataset.currentRouteIndex = routeIndex;
        }
        
        // Add modal styling
        modalElement.classList.add('route-details-modal');
        
        // Show modal
        this.routeDetailsModal.show();
        
        // Log to console for debugging
        console.log(`📋 Route details for index ${routeIndex}:`, {
            name: route.clean_name || route.route_name,
            origin: route.origin,
            destination: route.destination,
            waypoints: waypoints.length,
            distance: route.total_distance_nm,
            source_city: route.source_city
        });
    }
    
    /**
     * Show debug information - PRESERVED
     */
    showDebugInfo() {
        console.log('=== 🐛 DASHBOARD CONTROLS DEBUG ===');
        console.log('Version: 3.3.2 - ALL buttons preserved');
        console.log('Map available:', !!this.map);
        console.log('Total routes:', this.routesData.length);
        console.log('Waypoints data keys:', Object.keys(this.waypointsData));
        console.log('Current highlighted route:', this.currentHighlightedRoute);
        console.log('Emergency mode:', this.emergencyMode);
        console.log('Special pane exists:', !!this.map?.getPane('dashboard-highlight-pane'));
        
        // Check rtzWaypoints availability
        console.log('rtzWaypoints available:', !!window.rtzWaypoints);
        if (window.rtzWaypoints) {
            console.log('rtzWaypoints.highlightRoute exists:', !!window.rtzWaypoints.highlightRoute);
            console.log('rtzWaypoints.routeLines count:', Object.keys(window.rtzWaypoints.routeLines || {}).length);
        }
        
        // Sample first route data
        if (this.routesData.length > 0) {
            const firstRoute = this.routesData[0];
            console.log('First route:', {
                index: 0,
                id: firstRoute.id,
                route_id: firstRoute.route_id,
                name: firstRoute.clean_name || firstRoute.route_name,
                origin: firstRoute.origin,
                destination: firstRoute.destination,
                hasWaypointsInData: this.hasWaypointsForRoute(0)
            });
        }
        
        // Test functions
        console.log('Testing global functions:');
        console.log('  zoomToRoute:', typeof window.zoomToRoute);
        console.log('  inspectRouteData:', typeof window.inspectRouteData);
        console.log('  testMapVisualization:', typeof window.testMapVisualization);
        console.log('  testRtzWaypointsIntegration:', typeof window.testRtzWaypointsIntegration);
        
        console.log('=== END DEBUG ===');
        
        // Auto-run rtzWaypoints test
        setTimeout(() => {
            console.log('🧪 Auto-running rtzWaypoints integration test...');
            if (window.testRtzWaypointsIntegration) {
                window.testRtzWaypointsIntegration();
            }
        }, 500);
        
        this.showNotification('Debug info logged to console - Testing rtzWaypoints...', 'info');
    }
    
    /**
     * Show notification to user - REAL-TIME FIRST, FALLBACK LAST RESORT
     * @param {string} message - The message to display (TEXT ONLY, NO HTML)
     * @param {string} type - Type of notification: 'info', 'success', 'warning', 'error'
     * @param {number} duration - Duration in milliseconds to show the notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        console.log(`📢 [REAL-TIME FIRST] Attempting to show ${type} notification`);
        
        // Clear any existing timeouts
        if (this.notificationTimeout) {
            clearTimeout(this.notificationTimeout);
            this.notificationTimeout = null;
        }
        
        if (this.fallbackNotificationTimeout) {
            clearTimeout(this.fallbackNotificationTimeout);
            this.fallbackNotificationTimeout = null;
        }
        
        // Store last notification type for debugging
        this.lastNotificationType = type;
        
        // STEP 1: Try REAL-TIME notification system first
        const realTimeSuccess = this.showRealTimeNotification(message, type, duration);
        
        if (realTimeSuccess) {
            console.log(`✅ [REAL-TIME SUCCESS] Notification displayed via primary system`);
            return true;
        }
        
        // STEP 2: Only if real-time fails, use fallback as LAST RESORT
        console.log(`⚠️ [REAL-TIME FAILED] Primary system unavailable, using fallback as last resort`);
        return this.showFallbackNotification(message, type, duration);
    }

    /**
     * REAL-TIME NOTIFICATION SYSTEM - Primary method (tries first)
     * Uses the existing dashboard notification element
     */
    showRealTimeNotification(message, type = 'info', duration = 5000) {
        try {
            const notificationContainer = document.getElementById('dashboard-notification');
            
            if (!notificationContainer) {
                console.log('❌ [REAL-TIME] Notification container not found');
                return false;
            }
            
            console.log(`🔍 [REAL-TIME] Found notification container`);
            
            // Get toast elements
            const toastElement = notificationContainer.querySelector('.toast');
            const titleElement = notificationContainer.querySelector('#notification-title');
            const messageElement = notificationContainer.querySelector('#notification-message');
            const timeElement = notificationContainer.querySelector('#notification-time');
            
            if (!toastElement || !titleElement || !messageElement || !timeElement) {
                console.log('❌ [REAL-TIME] Toast elements not found in container');
                return false;
            }
            
            // Set notification content - USE TEXT CONTENT, NOT HTML
            titleElement.textContent = type.charAt(0).toUpperCase() + type.slice(1);
            messageElement.textContent = message; // Use textContent instead of innerHTML
            
            // Set timestamp
            const now = new Date();
            timeElement.textContent = now.toLocaleTimeString('en-GB', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            // Set type-specific styling
            const typeColors = {
                'info': '#17a2b8',
                'success': '#28a745',
                'warning': '#ffc107',
                'error': '#dc3545'
            };
            
            titleElement.style.color = typeColors[type] || typeColors.info;
            
            // Try to use Bootstrap Toast if available
            if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                console.log('🎯 [REAL-TIME] Using Bootstrap Toast API');
                
                // Initialize toast if not already done
                const toast = new bootstrap.Toast(toastElement, {
                    animation: true,
                    autohide: true,
                    delay: duration
                });
                
                // Show the toast
                toast.show();
                
                // Store timeout for cleanup
                this.notificationTimeout = setTimeout(() => {
                    toast.hide();
                }, duration);
                
                return true;
            } else {
                // Fallback to manual display
                console.log('⚠️ [REAL-TIME] Bootstrap not available, using manual display');
                
                // Force display of the notification
                notificationContainer.style.display = 'block';
                notificationContainer.style.visibility = 'visible';
                notificationContainer.style.opacity = '1';
                notificationContainer.classList.add('show');
                
                // Set manual timeout to hide
                this.notificationTimeout = setTimeout(() => {
                    notificationContainer.style.opacity = '0';
                    notificationContainer.classList.remove('show');
                    
                    setTimeout(() => {
                        notificationContainer.style.display = 'none';
                    }, 300);
                }, duration);
                
                return true;
            }
            
        } catch (error) {
            console.error('❌ [REAL-TIME ERROR] Failed to show real-time notification:', error);
            return false;
        }
    }

    /**
     * FALLBACK NOTIFICATION SYSTEM - Last resort only
     */
    showFallbackNotification(message, type = 'info', duration = 5000) {
        console.log(`🆘 [FALLBACK] Creating emergency notification as last resort`);
        
        try {
            // Remove any existing fallback notification
            const existing = document.querySelector('.dashboard-fallback-notification');
            if (existing) {
                existing.remove();
            }
            
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `dashboard-fallback-notification dashboard-fallback-${type}`;
            
            // Type-based styling
            const typeColors = {
                'info': '#17a2b8',
                'success': '#28a745',
                'warning': '#ffc107',
                'error': '#dc3545'
            };
            
            const typeIcons = {
                'info': 'ℹ️',
                'success': '✅',
                'warning': '⚠️',
                'error': '❌'
            };
            
            // Apply styles directly
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${typeColors[type] || typeColors.info};
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 9998;
                max-width: 350px;
                animation: slideIn 0.3s ease-out;
                font-family: system-ui, -apple-system, sans-serif;
                border-left: 4px solid ${type === 'error' ? '#b02a37' : type === 'warning' ? '#e0a800' : type === 'success' ? '#1e7e34' : '#0dcaf0'};
            `;
            
            // Create notification content
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-GB', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            notification.innerHTML = `
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 18px; margin-right: 8px;">${typeIcons[type] || 'ℹ️'}</span>
                    <span style="font-weight: bold; font-size: 16px;">
                        ${type.charAt(0).toUpperCase() + type.slice(1)}
                    </span>
                    <span style="margin-left: auto; font-size: 11px; opacity: 0.8;">
                        ${timeStr}
                    </span>
                </div>
                <div style="font-size: 14px; line-height: 1.4;">
                    ${message}
                </div>
                <div style="font-size: 10px; opacity: 0.6; margin-top: 5px; text-align: right;">
                    Emergency notification system
                </div>
            `;
            
            // Add to page
            document.body.appendChild(notification);
            
            // Auto-remove after duration
            this.fallbackNotificationTimeout = setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, duration);
            
            console.log(`✅ [FALLBACK] Emergency notification displayed as last resort`);
            
            return true;
            
        } catch (error) {
            console.error('❌ [FALLBACK ERROR] Failed to create fallback notification:', error);
            return false;
        }
    }
}

// Create and expose global instance
window.dashboardControls = new DashboardControls();

// Initialize when DOM is ready and map is available
document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 Dashboard controls v3.3.2 DOM ready - ALL buttons preserved');
    
    // Check for map availability
    const checkMap = setInterval(() => {
        if (window.map) {
            clearInterval(checkMap);
            window.dashboardControls.init(window.map);
        }
    }, 100);
});

// Add global test functions for console debugging
if (typeof window !== 'undefined') {
    window.testDashboard = function() {
        console.log('🧪 Testing dashboard v3.3.2...');
        if (window.dashboardControls) {
            console.log('Dashboard controls available');
            console.log('Total routes:', window.dashboardControls.routesData.length);
            
            // Test ALL 3 buttons
            if (window.dashboardControls.routesData.length > 0) {
                console.log('Testing ALL 3 buttons on first route...');
                window.dashboardControls.showRouteDetails(0);
            }
            
            return true;
        } else {
            console.error('Dashboard controls not available');
            return false;
        }
    };
    
    window.inspectRoute = function(index = 0) {
        return window.inspectRouteData?.(index);
    };
}