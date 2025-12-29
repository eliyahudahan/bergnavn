// backend/static/js/split/tanker_monitoring.js
/**
 * Tanker Traffic Monitoring Layer
 * Identifies and monitors tanker vessels in real-time
 */

window.tankerMonitor = {
    tankers: [],
    tankerLayer: null,
    dangerZoneLayer: null,
    updateInterval: null,
    
    init: function() {
        console.log('Tanker Monitor initialized');
        
        this.tankerLayer = L.layerGroup();
        this.dangerZoneLayer = L.layerGroup();
        
        if (window.layerControl && window.map) {
            window.layerControl.addOverlay(this.tankerLayer, 'Tankers');
            window.layerControl.addOverlay(this.dangerZoneLayer, 'Tanker Danger Zones');
        }
        
        return this;
    },
    
    startMonitoring: function() {
        console.log('Starting tanker monitoring...');
        
        // Initial scan
        this.scanForTankers();
        
        // Set up periodic scanning
        this.updateInterval = setInterval(() => {
            this.scanForTankers();
        }, 30000); // Every 30 seconds
        
        return this;
    },
    
    scanForTankers: function() {
        // Get current vessels from AIS manager
        const allVessels = window.aisManager?.realtimeVessels || [];
        
        // Filter for tankers
        this.tankers = allVessels.filter(vessel => {
            const type = vessel.ship_type || vessel.type || '';
            return type.toLowerCase().includes('tanker') || 
                   type.toLowerCase().includes('chemical') ||
                   type.toLowerCase().includes('oil') ||
                   vessel.name?.toLowerCase().includes('tanker');
        });
        
        console.log(`Found ${this.tankers.length} tankers`);
        this.displayTankers();
        this.updateTankerCount();
        
        return this.tankers;
    },
    
    displayTankers: function() {
        if (!window.map || !this.tankerLayer) return;
        
        // Clear existing
        this.tankerLayer.clearLayers();
        this.dangerZoneLayer.clearLayers();
        
        this.tankers.forEach(tanker => {
            const lat = tanker.latitude || tanker.lat;
            const lon = tanker.longitude || tanker.lon;
            
            if (!lat || !lon) return;
            
            // Create tanker marker
            const marker = L.marker([lat, lon], {
                icon: L.divIcon({
                    className: 'tanker-marker',
                    html: '<i class="bi bi-droplet-fill"></i>',
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                }),
                zIndexOffset: 1000 // Make tankers appear above other vessels
            }).bindPopup(`
                <div class="tanker-popup">
                    <strong class="text-danger">${tanker.name || 'Tanker'}</strong><br>
                    Type: ${tanker.ship_type || tanker.type || 'Tanker'}<br>
                    MMSI: ${tanker.mmsi || 'N/A'}<br>
                    Speed: ${tanker.speed || 0} knots<br>
                    Course: ${tanker.course || 0}°<br>
                    <small class="text-danger">⚠️ Hazardous Cargo - Keep 500m distance</small>
                </div>
            `);
            
            this.tankerLayer.addLayer(marker);
            
            // Create danger zone (500m radius)
            const dangerZone = L.circle([lat, lon], {
                radius: 500, // 500 meters safety zone
                color: '#dc3545',
                fillColor: '#dc3545',
                fillOpacity: 0.15,
                weight: 3,
                dashArray: '10, 10'
            }).bindPopup(`<strong>Tanker Safety Zone</strong><br>500m radius - Hazardous cargo`);
            
            this.dangerZoneLayer.addLayer(dangerZone);
        });
    },
    
    updateTankerCount: function() {
        const count = this.tankers.length;
        
        // Update UI if element exists
        const tankerCounter = document.getElementById('tanker-count');
        if (tankerCounter) {
            tankerCounter.textContent = count;
        } else {
            // Create counter in dashboard if not exists
            const statsRow = document.querySelector('.row.mb-4');
            if (statsRow && count > 0) {
                this.createTankerStatsCard(count);
            }
        }
    },
    
    createTankerStatsCard: function(count) {
        const statsRow = document.querySelector('.row.mb-4');
        if (!statsRow) return;
        
        const html = `
            <div class="col-md-3 mb-3">
                <div class="stats-card tanker-stat">
                    <h6><i class="bi bi-droplet me-2"></i>Tankers</h6>
                    <h3 id="tanker-count">${count}</h3>
                    <small class="text-muted">Hazardous cargo vessels</small>
                </div>
            </div>
        `;
        
        // Insert before RTZ routes card
        const rtzCard = document.querySelector('.rtz-stat').closest('.col-md-3');
        if (rtzCard) {
            rtzCard.insertAdjacentHTML('beforebegin', html);
        }
    },
    
    showTankers: function(showZones = true) {
        if (!window.map) return;
        
        if (window.map.hasLayer(this.tankerLayer)) {
            window.map.removeLayer(this.tankerLayer);
            if (showZones) window.map.removeLayer(this.dangerZoneLayer);
            console.log('Tankers hidden');
        } else {
            window.map.addLayer(this.tankerLayer);
            if (showZones) window.map.addLayer(this.dangerZoneLayer);
            console.log('Tankers shown');
            
            // If no tankers loaded, scan now
            if (this.tankers.length === 0) {
                this.scanForTankers();
            }
        }
    },
    
    checkCollisionRisk: function(vesselLat, vesselLon, vesselType) {
        // Check if vessel is too close to any tanker
        const risks = [];
        
        this.tankers.forEach(tanker => {
            const tLat = tanker.latitude || tanker.lat;
            const tLon = tanker.longitude || tanker.lon;
            
            if (!vesselLat || !vesselLon || !tLat || !tLon) return;
            
            const distance = this.calculateDistance(vesselLat, vesselLon, tLat, tLon);
            
            // 500m danger zone for all vessels
            // 1000m extra caution for other tankers
            const dangerRadius = vesselType?.toLowerCase().includes('tanker') ? 1000 : 500;
            
            if (distance * 1000 < dangerRadius) {
                risks.push({
                    tanker: tanker.name || 'Unknown Tanker',
                    distance: Math.round(distance * 1000),
                    dangerRadius: dangerRadius,
                    severity: distance * 1000 < dangerRadius * 0.3 ? 'CRITICAL' : 'WARNING'
                });
            }
        });
        
        return risks;
    },
    
    calculateDistance: function(lat1, lon1, lat2, lon2) {
        // Same as turbine distance calculator
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                 Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                 Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    },
    
    stopMonitoring: function() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
            console.log('Tanker monitoring stopped');
        }
    }
};