// backend/static/js/split/ais_realtime.js
/**
 * Real-time AIS Data Module for BergNavn Maritime Dashboard - SECURE VERSION
 * Uses environment variables securely via Flask backend
 * Priority: Bergen real-time → Commercial vessels → Empirical fallback (ONE vessel only)
 */

window.aisManager = {
    realtimeVessels: [],
    aisMarkers: null,
    updateInterval: null,
    isUpdating: false,
    lastUpdateTime: null,
    updateLock: false, // Prevents concurrent API calls
    
    /**
     * Initialize AIS real-time monitoring - SECURE VERSION
     */
    init: function() {
        console.log('🚢 AIS Manager initialized (Secure Bergen Priority)');
        
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
     */
    optimizeMapPerformance: function() {
        if (!window.map) return;
        
        // Disable unnecessary animations
        try {
            window.map.options.zoomAnimation = false;
            window.map.options.fadeAnimation = false;
            window.map.options.markerZoomAnimation = false;
        } catch (e) {
            console.log('Map optimization applied');
        }
    },
    
    /**
     * Start real-time AIS updates with Bergen priority
     */
    startRealTimeUpdates: function() {
        console.log('🚢 Starting AIS updates (Bergen Priority System)');
        
        // Initial load
        this.fetchRealTimeVessels();
        
        // Set up periodic updates (every 2 minutes)
        this.updateInterval = setInterval(() => {
            if (this.shouldUpdate()) {
                this.fetchRealTimeVessels();
            }
        }, 120000);
        
        return this;
    },
    
    /**
     * Check if we should update
     */
    shouldUpdate: function() {
        if (this.isUpdating) return false;
        if (document.hidden) return false;
        if (!window.map || !window.map.hasLayer(this.aisMarkers)) return false;
        
        return true;
    },
    
    /**
     * Fetch real-time vessel data with Bergen priority
     * SECURE: All credentials handled by Flask backend
     */
    fetchRealTimeVessels: async function() {
        // Prevent concurrent updates
        if (this.updateLock) {
            console.log('⚠️ AIS update locked, skipping...');
            return;
        }
        
        this.updateLock = true;
        this.isUpdating = true;
        
        console.log('📡 Fetching AIS data (Bergen Priority System)...');
        
        try {
            // Use AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000);
            
            // Call our secure backend API
            const response = await fetch('/maritime/api/ais/realtime', {
                signal: controller.signal,
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success' && data.vessels) {
                // Apply Bergen priority filter
                const filteredVessels = this.applyBergenPriority(data.vessels);
                
                requestAnimationFrame(() => {
                    this.realtimeVessels = filteredVessels;
                    this.updateVesselDisplay();
                    this.updateUICounters(filteredVessels);
                    
                    console.log(`✅ AIS: ${filteredVessels.length} vessels (Bergen priority applied)`);
                    console.log(`📊 Source: ${data.source || 'unknown'}`);
                    
                    // Update API status
                    this.updateAPIStatus(data.source || 'unknown', true);
                });
            } else {
                console.warn('AIS API returned unexpected format');
                this.fallbackToEmpirical();
            }
            
        } catch (error) {
            console.error('AIS fetch failed:', error.name, error.message);
            this.fallbackToEmpirical();
        } finally {
            this.updateLock = false;
            this.isUpdating = false;
            this.lastUpdateTime = new Date();
        }
    },
    
    /**
     * Apply Bergen priority filter to vessels
     * Priority: Bergen → Commercial → Others → Empirical fallback
     */
    applyBergenPriority: function(vessels) {
        if (!vessels || vessels.length === 0) {
            return this.createEmpiricalFallback();
        }
        
        const bergenArea = {
            latMin: 60.38, latMax: 60.40,
            lonMin: 5.30, lonMax: 5.34
        };
        
        // Categorize vessels
        const categories = {
            bergen: [],    // Vessels in Bergen area
            commercial: [], // Commercial vessels elsewhere
            other: []      // All other vessels
        };
        
        vessels.forEach(vessel => {
            const lat = vessel.latitude || vessel.lat;
            const lon = vessel.longitude || vessel.lon;
            
            if (!lat || !lon) return;
            
            // Check if vessel is in Bergen area
            const isInBergen = (
                lat >= bergenArea.latMin && lat <= bergenArea.latMax &&
                lon >= bergenArea.lonMin && lon <= bergenArea.lonMax
            );
            
            // Check if vessel is commercial (Cargo, Tanker, etc.)
            const vesselType = vessel.ship_type || vessel.type || '';
            const isCommercial = [
                'Cargo', 'Tanker', 'Container', 'Bulk Carrier',
                'Chemical Tanker', 'Oil Tanker', 'Gas Carrier'
            ].some(type => vesselType.includes(type));
            
            // Categorize
            if (isInBergen) {
                categories.bergen.push(vessel);
            } else if (isCommercial) {
                categories.commercial.push(vessel);
            } else {
                categories.other.push(vessel);
            }
        });
        
        // Build priority list (max 10 vessels total)
        const priorityVessels = [];
        
        // 1. Bergen vessels (up to 3)
        priorityVessels.push(...categories.bergen.slice(0, 3));
        
        // 2. Commercial vessels (up to 4)
        if (priorityVessels.length < 7) {
            priorityVessels.push(...categories.commercial.slice(0, 7 - priorityVessels.length));
        }
        
        // 3. Other vessels (fill up to 10)
        if (priorityVessels.length < 10) {
            priorityVessels.push(...categories.other.slice(0, 10 - priorityVessels.length));
        }
        
        // If we have no vessels at all, use empirical fallback
        if (priorityVessels.length === 0) {
            return this.createEmpiricalFallback();
        }
        
        return priorityVessels;
    },
    
    /**
     * Create empirical fallback - ONE vessel in Bergen
     * This is the last resort fallback
     */
    // שורה 145 בקובץ ais_realtime.js
// במקום זה:
createEmpiricalFallback: function() {
    console.log('🔄 Using empirical fallback (Bergen simulation)');
    
    const fallbackVessel = {
        mmsi: '259123000',
        name: 'MS BERGEN FJORD',
        ship_type: 'Passenger',
        type: 'Passenger Ship',
        latitude: 60.3929,  // Bergen Port - IN THE WATER!
        longitude: 5.3242,  // Bergen Port - IN THE WATER!
        speed: 12.5,
        course: 45,
        heading: 50,
        status: 'Under way using engine',
        destination: 'BERGEN',
        eta: new Date().toISOString(),
        draught: 6.5,
        length: 120,
        width: 18,
        timestamp: new Date().toISOString(),
        is_empirical: true
    };
    
    return [fallbackVessel];
},

createEmpiricalFallback: function() {
    console.log('🔄 Using empirical fallback (Realistic Bergen simulation)');
    
    // REALISTIC POSITIONS IN THE WATER - NOT ON LAND!
    const realisticVessels = [
        {
            mmsi: '259123000',
            name: 'MS BERGEN FJORD',
            ship_type: 'Passenger',
            type: 'Passenger Ship',
            latitude: 60.3991,  // Bergen Port - IN THE FJORD!
            longitude: 5.3167,  // Bergen Port - IN THE FJORD!
            speed: 12.5,
            course: 280,
            heading: 275,
            status: 'Under way using engine',
            destination: 'BERGEN',
            eta: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
            draught: 6.5,
            length: 120,
            width: 18,
            timestamp: new Date().toISOString(),
            is_empirical: true
        },
        {
            mmsi: '258123456',
            name: 'F/V SØRØY',
            ship_type: 'Fishing',
            type: 'Fishing Vessel',
            latitude: 60.405,  // OUTSIDE Bergen - IN THE WATER
            longitude: 5.285,  // OUTSIDE Bergen - IN THE WATER
            speed: 8.2,
            course: 190,
            heading: 195,
            status: 'Under way fishing',
            destination: 'FISKE',
            eta: new Date(Date.now() + 7200000).toISOString(), // 2 hours from now
            draught: 4.2,
            length: 45,
            width: 10,
            timestamp: new Date().toISOString(),
            is_empirical: true
        }
    ];
    
    return realisticVessels;
},
    
    /**
     * Fallback to empirical data when all else fails
     */
    fallbackToEmpirical: function() {
        console.log('⚠️ Falling back to empirical data');
        
        const empiricalVessels = this.createEmpiricalFallback();
        
        requestAnimationFrame(() => {
            this.realtimeVessels = empiricalVessels;
            this.updateVesselDisplay();
            this.updateUICounters(empiricalVessels);
            this.updateAPIStatus('empirical', false);
        });
    },
    
    /**
     * Update API status display
     */
    updateAPIStatus: function(source, isLive) {
        const statusElement = document.getElementById('ais-api-status');
        const qualityElement = document.getElementById('ais-data-quality');
        
        if (!statusElement || !qualityElement) return;
        
        const sourceMap = {
            'kystverket': { text: 'Kystverket Live', class: 'success' },
            'barentswatch': { text: 'BarentsWatch Live', class: 'success' },
            'kystdatahuset': { text: 'Kystdatahuset', class: 'info' },
            'empirical': { text: 'Empirical Fallback', class: 'warning' },
            'unknown': { text: 'Unknown Source', class: 'warning' }
        };
        
        const sourceInfo = sourceMap[source] || sourceMap['unknown'];
        
        // Update status badge
        statusElement.textContent = sourceInfo.text;
        statusElement.className = `badge bg-${isLive ? sourceInfo.class : 'warning'}`;
        
        // Update data quality indicator
        qualityElement.innerHTML = `
            <i class="fas fa-ship me-1"></i>
            AIS: ${isLive ? 'Live' : 'Fallback'} (${source})
        `;
        qualityElement.className = `data-quality-indicator ${
            isLive ? 'data-quality-high' : 'data-quality-low'
        }`;
    },
    
    /**
     * Update UI counters efficiently
     */
    updateUICounters: function(vessels) {
        if (!vessels || vessels.length === 0) return;
        
        const vesselCount = vessels.length;
        
        // Update count elements
        ['vessel-count', 'active-vessels'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = vesselCount;
        });
        
        // Update vessel type
        const typeElement = document.getElementById('vessel-type');
        if (typeElement) {
            const types = this.countVesselTypes(vessels);
            typeElement.textContent = this.formatVesselTypes(types);
        }
        
        // Update freshness timestamp
        const freshnessElement = document.getElementById('vessels-updated');
        if (freshnessElement) {
            const now = new Date();
            freshnessElement.textContent = `Updated: ${now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
        }
    },
    
    /**
     * Count vessel types
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
        const entries = Object.entries(types);
        if (entries.length === 0) return 'No vessels';
        
        return entries.map(([type, count]) => `${count} ${type}`).join(', ');
    },
    
    /**
     * Update vessel display on map
     */
    updateVesselDisplay: function() {
        if (!window.map || !this.aisMarkers) return;
        
        // Clear existing markers
        this.aisMarkers.clearLayers();
        
        // Add new markers for each vessel
        this.realtimeVessels.forEach(vessel => {
            const lat = vessel.latitude || vessel.lat;
            const lon = vessel.longitude || vessel.lon;
            
            if (lat && lon) {
                const icon = this.createVesselIcon(vessel);
                const marker = L.marker([lat, lon], { 
                    icon: icon,
                    zIndexOffset: vessel.is_empirical ? -1000 : 1000 // Empirical vessels behind real ones
                }).bindPopup(this.createVesselPopup(vessel));
                
                this.aisMarkers.addLayer(marker);
            }
        });
        
        // Ensure layer is on map if we have vessels
        if (this.realtimeVessels.length > 0 && !window.map.hasLayer(this.aisMarkers)) {
            window.map.addLayer(this.aisMarkers);
        }
    },
    
    /**
     * Create custom vessel icon
     */
    createVesselIcon: function(vessel) {
        const vesselType = vessel.ship_type || vessel.type || 'Unknown';
        const isEmpirical = vessel.is_empirical || false;
        
        // Different icons for different types
        let iconClass = 'fas fa-ship'; // Default
        
        if (vesselType.includes('Cargo') || vesselType.includes('Container')) {
            iconClass = 'fas fa-box';
        } else if (vesselType.includes('Tanker')) {
            iconClass = 'fas fa-gas-pump';
        } else if (vesselType.includes('Passenger')) {
            iconClass = 'fas fa-users';
        } else if (vesselType.includes('Fishing')) {
            iconClass = 'fas fa-fish';
        } else if (vesselType.includes('Tug')) {
            iconClass = 'fas fa-anchor';
        }
        
        // Empirical vessels have different styling
        const color = isEmpirical ? '#6c757d' : '#007bff';
        const size = isEmpirical ? '18px' : '22px';
        
        return L.divIcon({
            className: `vessel-marker ${isEmpirical ? 'empirical' : 'live'}`,
            html: `<i class="${iconClass}" style="color: ${color}; font-size: ${size};"></i>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
    },
    
    /**
     * Create vessel popup
     */
    createVesselPopup: function(vessel) {
        const isEmpirical = vessel.is_empirical || false;
        const source = isEmpirical ? 'Empirical Simulation' : 'Real-time AIS';
        
        return `
            <div class="vessel-popup ${isEmpirical ? 'empirical' : ''}">
                <strong>${vessel.name || 'Unknown Vessel'}</strong>
                ${isEmpirical ? '<span class="badge bg-warning ms-1">SIM</span>' : ''}
                <br>
                <small class="text-muted">MMSI: ${vessel.mmsi || 'N/A'}</small><br>
                Type: ${vessel.ship_type || vessel.type || 'Unknown'}<br>
                Position: ${(vessel.latitude || vessel.lat).toFixed(4)}°, ${(vessel.longitude || vessel.lon).toFixed(4)}°<br>
                Speed: ${vessel.speed || 0} knots<br>
                Course: ${vessel.course || 0}°<br>
                ${vessel.destination ? `Destination: ${vessel.destination}<br>` : ''}
                <small>Source: ${source}</small><br>
                <small>Updated: ${new Date().toLocaleTimeString()}</small>
            </div>
        `;
    },
    
    /**
     * Toggle AIS visibility
     */
    toggleAISVisibility: function() {
        if (!window.map || !this.aisMarkers) return false;
        
        const isVisible = window.map.hasLayer(this.aisMarkers);
        
        if (isVisible) {
            window.map.removeLayer(this.aisMarkers);
            this.stopRealTimeUpdates();
            console.log('AIS layer hidden');
        } else {
            window.map.addLayer(this.aisMarkers);
            this.startRealTimeUpdates();
            console.log('AIS layer shown');
        }
        
        return !isVisible;
    },
    
    /**
     * Stop updates
     */
    stopRealTimeUpdates: function() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    },
    
    /**
     * Clean up
     */
    destroy: function() {
        this.stopRealTimeUpdates();
        if (this.aisMarkers) {
            this.aisMarkers.clearLayers();
        }
    }
};

// Auto-initialize
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        if (window.map) {
            window.aisManager.init();
            console.log('✅ AIS Manager ready (Bergen Priority System)');
        }
    }, 1500);
});