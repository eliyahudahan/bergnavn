/**
 * TURBINE PROXIMITY ALERTS - REAL-TIME INTEGRATION
 * =================================================
 * Adds wind turbine proximity alerts to existing simulation
 * WITHOUT modifying working files.
 * 
 * Priority: Real-time API → Empirical fallback
 * Max search time: 5 seconds
 */

window.turbineAlerts = {
    // Configuration
    searchTimeout: 5000, // 5 seconds max
    checkInterval: 30000, // Check every 30 seconds
    activeAlerts: [],
    
    // Norwegian wind turbine data
    turbines: [],
    dataSource: 'unknown',
    searchResults: [],
    lastUpdate: null,
    
    /**
     * Initialize turbine alerts
     * Called from realtime_simulation.html
     */
    init: function() {
        console.log('🌀 Turbine Alerts: Initializing...');
        
        // Load turbine data
        this.loadTurbineData();
        
        // Start periodic checks
        setInterval(() => {
            this.checkProximity();
        }, this.checkInterval);
        
        return this;
    },
    
    /**
     * Load turbine data from backend API
     * Performs REAL search with timeout
     */
    loadTurbineData: async function() {
        try {
            console.log('🌀 Turbine Alerts: Searching for real-time data...');
            
            // Show search status in UI
            this.updateSearchStatus('searching', 'Checking Norwegian wind turbine APIs...');
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.searchTimeout);
            
            const response = await fetch('/api/turbines/search', {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const data = await response.json();
                
                this.turbines = data.turbines || [];
                this.dataSource = data.data_source || 'unknown';
                this.searchResults = data.search_results || [];
                this.lastUpdate = new Date();
                
                console.log(`🌀 Turbine Alerts: ${data.data_source.toUpperCase()}`);
                console.log(`   Turbines loaded: ${this.turbines.length}`);
                console.log(`   Search time: ${data.total_search_time_seconds}s`);
                
                // Update UI with search results
                this.updateSearchStatus('complete', data);
                
                // Initial proximity check
                this.checkProximity();
                
            } else {
                console.warn('Turbine API error, using fallback');
                this.useEmpiricalFallback();
            }
            
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('🌀 Turbine Alerts: Search timeout (5s) - using empirical data');
            } else {
                console.warn('🌀 Turbine Alerts: Search failed:', error.message);
            }
            this.useEmpiricalFallback();
        }
    },
    
    /**
     * Use empirical data as fallback
     */
    useEmpiricalFallback: function() {
        console.log('🌀 Turbine Alerts: Switching to empirical data');
        
        this.turbines = [
            {
                id: "utsira_nord",
                name: "Utsira Nord",
                latitude: 59.5,
                longitude: 4.0,
                buffer_meters: 1000,
                capacity_mw: 1500,
                status: "planned",
                data_source: "empirical_fallback",
                operator: "Equinor"
            },
            {
                id: "sorlige_nordsjo_ii",
                name: "Sørlige Nordsjø II",
                latitude: 57.5,
                longitude: 6.8,
                buffer_meters: 1500,
                capacity_mw: 3000,
                status: "planning",
                data_source: "empirical_fallback",
                operator: "Statkraft"
            },
            {
                id: "bergen_coastal_test",
                name: "Bergen Coastal Test",
                latitude: 60.8,
                longitude: 4.8,
                buffer_meters: 800,
                capacity_mw: 200,
                status: "operational",
                data_source: "empirical_fallback",
                operator: "University of Bergen"
            }
        ];
        
        this.dataSource = 'empirical_fallback';
        this.lastUpdate = new Date();
        this.updateSearchStatus('empirical', 'Using empirical wind farm data');
        
        // Initial proximity check
        this.checkProximity();
    },
    
    /**
     * Check proximity of current vessel to all turbines
     */
    checkProximity: function() {
        if (!this.turbines.length) {
            console.log('🌀 No turbines loaded for proximity check');
            return;
        }
        
        // Try to get vessel from singleVesselSim
        let vessel = null;
        if (window.singleVesselSim && window.singleVesselSim.currentVessel) {
            vessel = window.singleVesselSim.currentVessel;
        } else {
            // Use default position if no vessel
            vessel = { lat: 60.3940, lon: 5.3200, name: "Default Vessel" };
            console.log('🌀 Using default position for proximity check');
        }
        
        const warnings = [];
        
        this.turbines.forEach(turbine => {
            try {
                const distance = this.calculateDistance(
                    vessel.lat, vessel.lon,
                    turbine.latitude, turbine.longitude
                );
                
                const distanceMeters = distance * 1000; // Convert km to meters
                
                if (distanceMeters < turbine.buffer_meters) {
                    const warningLevel = distanceMeters < turbine.buffer_meters * 0.3 
                        ? 'CRITICAL' 
                        : 'WARNING';
                    
                    warnings.push({
                        turbine: turbine.name,
                        distance: Math.round(distanceMeters),
                        buffer: turbine.buffer_meters,
                        level: warningLevel,
                        data_source: turbine.data_source,
                        operator: turbine.operator || 'Unknown'
                    });
                }
            } catch (error) {
                console.warn('Error calculating distance to turbine:', error);
            }
        });
        
        this.activeAlerts = warnings;
        this.updateAlertsUI();
        
        // Log if warnings found
        if (warnings.length > 0) {
            console.log(`🚨 Turbine Alerts: ${warnings.length} proximity warning(s)`);
        } else {
            console.log('🌀 Turbine Alerts: No proximity warnings');
        }
    },
    
    /**
     * Calculate distance between two points (km)
     */
    calculateDistance: function(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                 Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                 Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    },
    
    /**
     * Update search status in UI
     */
    updateSearchStatus: function(status, data) {
        const panel = this.getOrCreateTurbinePanel();
        if (!panel) return;
        
        let statusHtml = '';
        const statusElement = panel.querySelector('.turbine-status');
        if (!statusElement) return;
        
        if (status === 'searching') {
            statusHtml = `
                <div class="alert alert-warning mb-2 p-2">
                    <small>
                        <i class="fas fa-search me-1"></i>
                        <strong>Searching Norwegian Wind Turbine APIs...</strong><br>
                        ${data}
                    </small>
                </div>
            `;
        }
        else if (status === 'complete') {
            const sourceText = data.data_source === 'realtime_api' 
                ? '<span class="text-success">Real-time API data</span>' 
                : '<span class="text-info">Empirical data</span>';
            
            const timeStr = this.lastUpdate ? this.lastUpdate.toLocaleTimeString() : 'Now';
            
            statusHtml = `
                <div class="alert alert-success mb-2 p-2">
                    <small>
                        <i class="fas fa-check-circle me-1"></i>
                        <strong>Wind Turbine Data Loaded</strong><br>
                        Source: ${sourceText} | Turbines: ${data.turbines.length}<br>
                        Search time: ${data.total_search_time_seconds}s | Updated: ${timeStr}
                    </small>
                </div>
            `;
        }
        else if (status === 'empirical') {
            statusHtml = `
                <div class="alert alert-info mb-2 p-2">
                    <small>
                        <i class="fas fa-database me-1"></i>
                        <strong>Using Empirical Wind Farm Data</strong><br>
                        ${data}<br>
                        ${this.turbines.length} Norwegian wind farms loaded
                    </small>
                </div>
            `;
        }
        
        statusElement.innerHTML = statusHtml;
    },
    
    /**
     * Update alerts UI
     */
    updateAlertsUI: function() {
        const panel = this.getOrCreateTurbinePanel();
        if (!panel) return;
        
        const alertsContainer = panel.querySelector('.turbine-alerts');
        if (!alertsContainer) return;
        
        if (this.activeAlerts.length === 0) {
            alertsContainer.innerHTML = `
                <div class="alert alert-success p-2">
                    <small>
                        <i class="fas fa-check-circle me-1"></i>
                        <strong>All Clear</strong><br>
                        No turbine proximity warnings. Maintain safe distance.
                    </small>
                </div>
            `;
        } else {
            let alertsHtml = `
                <div class="alert alert-danger p-2 mb-2">
                    <small>
                        <i class="fas fa-exclamation-triangle me-1"></i>
                        <strong>${this.activeAlerts.length} TURBINE PROXIMITY WARNING(S)</strong><br>
                        Vessel is too close to wind turbine safety zones.
                    </small>
                </div>
            `;
            
            this.activeAlerts.forEach(alert => {
                const alertClass = alert.level === 'CRITICAL' 
                    ? 'alert-danger' 
                    : 'alert-warning';
                
                const icon = alert.level === 'CRITICAL' 
                    ? 'fa-exclamation-circle' 
                    : 'fa-exclamation-triangle';
                
                alertsHtml += `
                    <div class="alert ${alertClass} p-2 mb-1">
                        <small>
                            <i class="fas ${icon} me-1"></i>
                            <strong>${alert.turbine}</strong> (${alert.operator})<br>
                            Distance: <strong>${alert.distance}m</strong> / Buffer: ${alert.buffer}m<br>
                            Level: <span class="badge bg-${alert.level === 'CRITICAL' ? 'danger' : 'warning'}">${alert.level}</span> | 
                            Source: ${alert.data_source.replace('_', ' ')}
                        </small>
                    </div>
                `;
            });
            
            alertsContainer.innerHTML = alertsHtml;
        }
    },
    
    /**
     * Get or create turbine panel in UI
     */
    getOrCreateTurbinePanel: function() {
        let panel = document.getElementById('turbine-alerts-panel');
        
        if (!panel) {
            // Find right column (where vessel info is)
            const rightColumn = document.querySelector('.col-lg-4');
            if (!rightColumn) {
                console.warn('🌀 Could not find right column for turbine panel');
                return null;
            }
            
            // Create panel HTML
            panel = document.createElement('div');
            panel.id = 'turbine-alerts-panel';
            panel.className = 'card mt-3';
            panel.style.cssText = 'border-left: 4px solid #ffc107;';
            panel.innerHTML = `
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0">
                        <i class="fas fa-wind me-2"></i>
                        Norwegian Wind Turbine Alerts
                        <span class="badge bg-dark float-end">NEW</span>
                    </h6>
                </div>
                <div class="card-body">
                    <div class="turbine-status mb-3">
                        <div class="alert alert-info p-2">
                            <small>
                                <i class="fas fa-sync-alt fa-spin me-1"></i>
                                Initializing turbine alert system...
                            </small>
                        </div>
                    </div>
                    <div class="turbine-alerts">
                        <div class="alert alert-secondary p-2">
                            <small>
                                <i class="fas fa-info-circle me-1"></i>
                                Loading turbine proximity data...
                            </small>
                        </div>
                    </div>
                    <div class="mt-2 text-center">
                        <button class="btn btn-sm btn-outline-warning" onclick="window.turbineAlerts.checkProximity()">
                            <i class="fas fa-redo me-1"></i> Check Now
                        </button>
                        <small class="text-muted d-block mt-1">
                            Real-time API search + Empirical fallback
                        </small>
                    </div>
                </div>
            `;
            
            // Insert after the first card (vessel info)
            const vesselCard = rightColumn.querySelector('.card');
            if (vesselCard) {
                vesselCard.parentNode.insertBefore(panel, vesselCard.nextSibling);
            } else {
                rightColumn.insertBefore(panel, rightColumn.firstChild);
            }
            
            console.log('🌀 Created turbine alerts panel in UI');
        }
        
        return panel;
    },
    
    /**
     * Get current alert count
     */
    getAlertCount: function() {
        return this.activeAlerts.length;
    },
    
    /**
     * Get data source info
     */
    getDataSource: function() {
        return this.dataSource;
    },
    
    /**
     * Manually trigger proximity check
     */
    manualCheck: function() {
        console.log('🌀 Manual turbine proximity check triggered');
        this.checkProximity();
    }
};

// Auto-initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        console.log('🌀 Starting turbine alerts system...');
        if (!window.turbineAlerts) {
            window.turbineAlerts = turbineAlerts;
        }
        window.turbineAlerts.init();
    }, 1500);
});

// Export for global use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = turbineAlerts;
}
