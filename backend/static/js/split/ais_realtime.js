// backend/static/js/split/ais_realtime.js
/**
 * Real-time AIS Data Module for BergNavn Maritime Dashboard
 * Fetches and displays real vessel data from BarentsWatch API
 */

window.aisManager = {
    realtimeVessels: [],
    aisMarkers: null,
    updateInterval: null,
    
    /**
     * Initialize AIS real-time monitoring
     */
    init: function() {
        console.log('AIS Manager initialized');
        
        // Create marker layer for vessels
        this.aisMarkers = L.layerGroup();
        
        // Add to layer control if available
        if (window.layerControl && window.map) {
            window.layerControl.addOverlay(this.aisMarkers, 'Vessels (Real-time)');
        }
        
        return this;
    },
    
    /**
     * Start real-time AIS updates
     */
    startRealTimeUpdates: function() {
        console.log('Starting AIS real-time updates');
        
        // Initial load
        this.fetchRealTimeVessels();
        
        // Set up periodic updates (every 60 seconds)
        this.updateInterval = setInterval(() => {
            this.fetchRealTimeVessels();
        }, 60000);
        
        return this;
    },
    
    /**
     * Fetch real-time vessel data from backend API
     */
    fetchRealTimeVessels: async function() {
        try {
            console.log('Fetching real-time AIS data...');
            
            const response = await fetch('/maritime/api/ais/realtime');
            const data = await response.json();
            
            if (data.status === 'success' && data.vessels) {
                this.realtimeVessels = data.vessels;
                this.updateVesselDisplay();
                
                // Update UI counters
                document.getElementById('vessel-count').textContent = data.vessels.length;
                document.getElementById('active-vessels').textContent = data.vessels.length;
                
                // Update vessel type summary
                const vesselTypes = this.countVesselTypes(data.vessels);
                document.getElementById('vessel-type').textContent = 
                    this.formatVesselTypes(vesselTypes);
                
                // Update AIS status
                document.getElementById('ais-status').textContent = 'Live';
                document.getElementById('ais-status').className = 'text-success';
                
                console.log(`Loaded ${data.vessels.length} real-time vessels`);
            }
        } catch (error) {
            console.error('Failed to fetch AIS data:', error);
            document.getElementById('ais-status').textContent = 'Offline';
            document.getElementById('ais-status').className = 'text-danger';
        }
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
     */
    updateVesselDisplay: function() {
        if (!window.map || !this.aisMarkers) {
            console.warn('Map or AIS markers not initialized');
            return;
        }
        
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
                const marker = L.marker([lat, lon], { icon: icon })
                    .bindPopup(this.createVesselPopup(vessel));
                
                this.aisMarkers.addLayer(marker);
            }
        });
        
        // Update vessel count badge
        document.getElementById('vessel-count').textContent = this.realtimeVessels.length;
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
        } else {
            window.map.addLayer(this.aisMarkers);
            console.log('Real-time vessels shown');
            
            // If no vessels loaded yet, fetch them
            if (this.realtimeVessels.length === 0) {
                this.fetchRealTimeVessels();
            }
        }
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
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof L !== 'undefined' && window.map) {
        window.aisManager.init();
    }
});