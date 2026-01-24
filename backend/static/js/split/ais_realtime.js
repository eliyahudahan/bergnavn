/* backend/static/js/split/ais_realtime.js */
/**
 * Real-time AIS Data Module for BergNavn Maritime Dashboard - FIXED VERSION
 * Fetches and displays real vessel data from BarentsWatch API
 * FIXED: Optimized update intervals to prevent map flickering/refreshing
 */

window.aisManager = {
    realtimeVessels: [],
    aisMarkers: null,
    updateInterval: null,
    isUpdating: false, // FIXED: Add update lock to prevent concurrent updates
    
    /**
     * Initialize AIS real-time monitoring
     */
    init: function() {
        console.log('🚢 AIS Manager initialized (Optimized Version)');
        
        // Create marker layer for vessels
        this.aisMarkers = L.layerGroup();
        
        // Add to layer control if available
        if (window.layerControl && window.map) {
            window.layerControl.addOverlay(this.aisMarkers, 'Vessels (Real-time)');
        }
        
        // Initialize with optimized settings
        this.optimizeMapPerformance();
        
        return this;
    },
    
    /**
     * Optimize map performance settings
     * FIXED: Prevents unnecessary map refreshes
     */
    optimizeMapPerformance: function() {
        if (!window.map) return;
        
        // Disable some Leaflet animations that might cause flickering
        try {
            // Reduce animation intensity
            if (map.options.zoomAnimation) {
                map.options.zoomAnimation = false;
            }
            
            // Limit marker clustering animations
            if (map._layers) {
                Object.values(map._layers).forEach(layer => {
                    if (layer._animation && typeof layer._animation === 'function') {
                        // Disable animation on path updates
                        layer.options.smoothFactor = 1.0; // Less smoothing
                    }
                });
            }
        } catch (e) {
            console.log('Map optimization applied:', e.message);
        }
    },
    
    /**
     * Start real-time AIS updates with optimized intervals
     * FIXED: Longer interval and better state management
     */
    startRealTimeUpdates: function() {
        console.log('Starting AIS real-time updates (Optimized)');
        
        // Initial load with delay to let map settle
        setTimeout(() => {
            this.fetchRealTimeVessels();
        }, 2000);
        
        // FIXED: Set up optimized periodic updates (every 2 minutes instead of 1)
        // Prevents constant map refreshing
        this.updateInterval = setInterval(() => {
            // Only update if map is visible and user is active
            if (this.shouldUpdate()) {
                this.fetchRealTimeVessels();
            } else {
                console.log('🕒 Skipping AIS update (inactive tab/map)');
            }
        }, 120000); // 120000ms = 2 minutes (was 60000ms)
        
        return this;
    },
    
    /**
     * Check if we should update based on user activity
     * FIXED: Prevents updates when not needed
     */
    shouldUpdate: function() {
        // Don't update if already updating
        if (this.isUpdating) return false;
        
        // Don't update if tab is not visible
        if (document.hidden) return false;
        
        // Don't update if map is not visible
        const mapElement = document.getElementById('maritime-map');
        if (!mapElement || mapElement.offsetParent === null) return false;
        
        // Don't update if AIS layer is not visible
        if (window.map && this.aisMarkers && !window.map.hasLayer(this.aisMarkers)) {
            return false;
        }
        
        return true;
    },
    
    /**
     * Fetch real-time vessel data from backend API
     * FIXED: Added timeout and better error handling
     */
    fetchRealTimeVessels: async function() {
        // Prevent concurrent updates
        if (this.isUpdating) {
            console.log('⚠️ AIS update already in progress, skipping...');
            return;
        }
        
        this.isUpdating = true;
        console.log('📡 Fetching real-time AIS data...');
        
        try {
            // Add timeout to prevent hanging requests
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch('/maritime/api/ais/realtime', {
                signal: controller.signal,
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });
            
            clearTimeout(timeoutId);
            const data = await response.json();
            
            if (data.status === 'success' && data.vessels) {
                // FIXED: Use requestAnimationFrame for smoother updates
                requestAnimationFrame(() => {
                    this.realtimeVessels = data.vessels;
                    this.updateVesselDisplay();
                    
                    // Update UI counters with minimal DOM operations
                    this.updateUICounters(data.vessels);
                    
                    console.log(`✅ Loaded ${data.vessels.length} real-time vessels`);
                });
            } else {
                console.warn('AIS API returned unexpected format:', data);
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn('AIS request timed out');
            } else {
                console.error('Failed to fetch AIS data:', error);
            }
            
            // Update status with fallback
            document.getElementById('ais-status').textContent = 'Offline';
            document.getElementById('ais-status').className = 'text-danger';
        } finally {
            this.isUpdating = false;
            this.lastUpdateTime = new Date();
        }
    },
    
    /**
     * Update UI counters efficiently
     * FIXED: Minimizes DOM operations
     */
    updateUICounters: function(vessels) {
        const vesselCount = vessels.length;
        
        // Update count elements in one batch
        const countElement = document.getElementById('vessel-count');
        const activeElement = document.getElementById('active-vessels');
        
        if (countElement && countElement.textContent !== vesselCount.toString()) {
            countElement.textContent = vesselCount;
        }
        
        if (activeElement && activeElement.textContent !== vesselCount.toString()) {
            activeElement.textContent = vesselCount;
        }
        
        // Update vessel type summary (only if changed)
        const vesselTypes = this.countVesselTypes(vessels);
        const typeSummary = this.formatVesselTypes(vesselTypes);
        const typeElement = document.getElementById('vessel-type');
        
        if (typeElement && typeElement.textContent !== typeSummary) {
            typeElement.textContent = typeSummary;
        }
        
        // Update AIS status
        document.getElementById('ais-status').textContent = 'Live';
        document.getElementById('ais-status').className = 'text-success';
    },
    
    /**
     * Count vessel types for display
     */
    countVesselTypes: function(vessels) {
        const types = {};
        
        vessels.forEach(vessel => {
            const type = vessel.ship_type || vessel.type || 'Unknown';
            types[type] = (types[type] || 0) + 1;
        });
        
        return types;
    },
    
    /**
     * Format vessel types for display
     */
    formatVesselTypes: function(types) {
        const mainTypes = ['Cargo', 'Tanker', 'Passenger', 'Fishing', 'Tug'];
        const result = [];
        
        mainTypes.forEach(type => {
            if (types[type]) {
                result.push(`${types[type]} ${type}`);
            }
        });
        
        // Add "Other" if there are remaining types
        const otherCount = Object.values(types).reduce((a, b) => a + b, 0) -
                         result.reduce((sum, item) => sum + parseInt(item), 0);
        
        if (otherCount > 0) {
            result.push(`${otherCount} Other`);
        }
        
        return result.length > 0 ? result.join(', ') : 'No vessels';
    },
    
    /**
     * Update vessel display on map and UI
     * FIXED: Optimized to prevent map flickering
     */
    updateVesselDisplay: function() {
        if (!window.map || !this.aisMarkers) {
            console.warn('Map or AIS markers not initialized');
            return;
        }
        
        // FIXED: Use debounced update to prevent rapid re-renders
        if (this._updateTimeout) {
            clearTimeout(this._updateTimeout);
        }
        
        this._updateTimeout = setTimeout(() => {
            // Clear existing markers
            this.aisMarkers.clearLayers();
            
            // Add new markers for each vessel
            this.realtimeVessels.forEach(vessel => {
                const lat = vessel.latitude || vessel.lat;
                const lon = vessel.longitude || vessel.lon;
                
                if (lat && lon) {
                    // Create custom vessel icon based on type
                    const icon = this.createVesselIcon(vessel);
                    
                    // Create marker with popup
                    const marker = L.marker([lat, lon], { 
                        icon: icon,
                        // FIXED: Disable animation for markers
                        animate: false
                    }).bindPopup(this.createVesselPopup(vessel));
                    
                    this.aisMarkers.addLayer(marker);
                }
            });
            
            console.log(`🔄 Updated ${this.realtimeVessels.length} vessel markers`);
        }, 100); // 100ms debounce
    },
    
    /**
     * Create custom Leaflet icon for vessel
     */
    createVesselIcon: function(vessel) {
        const vesselType = vessel.ship_type || vessel.type || 'Unknown';
        let iconClass = 'bi-question-circle'; // Default icon
        
        // Map vessel types to icons
        const iconMap = {
            'Cargo': 'bi-box',
            'Tanker': 'bi-droplet',
            'Passenger': 'bi-people',
            'Fishing': 'bi-fish',
            'Tug': 'bi-truck',
            'Pilot': 'bi-compass',
            'Search and Rescue': 'bi-life-preserver',
            'Military': 'bi-shield'
        };
        
        // Find matching icon
        for (const [type, icon] of Object.entries(iconMap)) {
            if (vesselType.toLowerCase().includes(type.toLowerCase())) {
                iconClass = icon;
                break;
            }
        }
        
        return L.divIcon({
            className: 'vessel-marker',
            html: `<i class="bi ${iconClass}"></i>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
    },
    
    /**
     * Create HTML popup for vessel
     */
    createVesselPopup: function(vessel) {
        return `
            <div class="vessel-popup">
                <strong>${vessel.name || 'Unknown Vessel'}</strong><br>
                <small class="text-muted">MMSI: ${vessel.mmsi || 'N/A'}</small><br>
                Type: ${vessel.ship_type || vessel.type || 'Unknown'}<br>
                Speed: ${vessel.speed || 0} knots<br>
                Course: ${vessel.course || 0}°<br>
                <small>Updated: ${new Date().toLocaleTimeString()}</small>
            </div>
        `;
    },
    
    /**
     * Show/hide real-time vessels on map
     */
    showRealtimeVessels: function() {
        if (!window.map || !this.aisMarkers) {
            console.error('Map or AIS markers not available');
            return;
        }
        
        if (window.map.hasLayer(this.aisMarkers)) {
            window.map.removeLayer(this.aisMarkers);
            console.log('Real-time vessels hidden');
            
            // FIXED: Stop updates when layer is hidden
            this.stopRealTimeUpdates();
        } else {
            window.map.addLayer(this.aisMarkers);
            console.log('Real-time vessels shown');
            
            // Restart updates when layer is shown
            this.startRealTimeUpdates();
            
            // If no vessels loaded yet, fetch them
            if (this.realtimeVessels.length === 0) {
                this.fetchRealTimeVessels();
            }
        }
    },
    
    /**
     * Toggle AIS layer visibility without affecting updates
     * FIXED: Separate visibility from update logic
     */
    toggleAISVisibility: function() {
        if (!window.map || !this.aisMarkers) return;
        
        const isVisible = window.map.hasLayer(this.aisMarkers);
        
        if (isVisible) {
            window.map.removeLayer(this.aisMarkers);
        } else {
            window.map.addLayer(this.aisMarkers);
        }
        
        return !isVisible;
    },
    
    /**
     * Stop real-time updates
     */
    stopRealTimeUpdates: function() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
            console.log('AIS real-time updates stopped');
        }
        
        // Clear any pending timeouts
        if (this._updateTimeout) {
            clearTimeout(this._updateTimeout);
            this._updateTimeout = null;
        }
    },
    
    /**
     * Clean up resources
     */
    destroy: function() {
        this.stopRealTimeUpdates();
        
        if (this.aisMarkers) {
            this.aisMarkers.clearLayers();
            if (window.map && window.map.hasLayer(this.aisMarkers)) {
                window.map.removeLayer(this.aisMarkers);
            }
        }
        
        console.log('AIS Manager cleaned up');
    }
};

// Auto-initialize when DOM is ready with optimization
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for map to fully initialize
    setTimeout(() => {
        if (typeof L !== 'undefined' && window.map) {
            window.aisManager.init();
            
            // FIXED: Don't auto-start updates, let user control
            // window.aisManager.startRealTimeUpdates(); // Commented out
            
            console.log('✅ AIS Manager ready (manual start required)');
        }
    }, 1000);
});