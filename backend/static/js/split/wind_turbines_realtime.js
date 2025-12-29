// backend/static/js/split/wind_turbines_realtime.js
/**
 * Norwegian Wind Turbines Layer
 * Displays offshore wind farms with safety zones
 */

window.windTurbineManager = {
    turbines: [],
    turbineLayer: null,
    safetyZoneLayer: null,
    
    // Norwegian offshore wind farms (sample data - later from Kystdatahuset)
    norwegianWindFarms: [
        {
            name: "Utsira Nord",
            lat: 59.5,
            lon: 4.0,
            buffer_m: 1000,
            capacity: "1.5 GW",
            status: "Planned",
            turbines: 50
        },
        {
            name: "Sørlige Nordsjø II",
            lat: 57.5, 
            lon: 6.8,
            buffer_m: 1500,
            capacity: "3.0 GW",
            status: "Planning",
            turbines: 100
        },
        {
            name: "Bergen Coastal Test",
            lat: 60.8,
            lon: 4.8,
            buffer_m: 800,
            capacity: "0.2 GW",
            status: "Operational",
            turbines: 5
        }
    ],
    
    init: function() {
        console.log('Wind Turbine Manager initialized');
        
        // Create layers
        this.turbineLayer = L.layerGroup();
        this.safetyZoneLayer = L.layerGroup();
        
        // Add to layer control if available
        if (window.layerControl && window.map) {
            window.layerControl.addOverlay(this.turbineLayer, 'Wind Turbines');
            window.layerControl.addOverlay(this.safetyZoneLayer, 'Safety Zones (500m)');
        }
        
        this.loadTurbines();
        return this;
    },
    
    loadTurbines: function() {
        console.log('Loading wind turbine data...');
        
        // For now use sample data, later fetch from Kystdatahuset API
        this.turbines = this.norwegianWindFarms;
        
        this.displayTurbines();
        this.updateTurbineCount();
        
        return this;
    },
    
    displayTurbines: function() {
        if (!window.map || !this.turbineLayer) return;
        
        // Clear existing
        this.turbineLayer.clearLayers();
        this.safetyZoneLayer.clearLayers();
        
        this.turbines.forEach(turbine => {
            // Create turbine marker
            const marker = L.marker([turbine.lat, turbine.lon], {
                icon: L.divIcon({
                    className: 'turbine-marker',
                    html: '<i class="bi bi-fan"></i>',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                })
            }).bindPopup(`
                <div class="turbine-popup">
                    <strong>${turbine.name}</strong><br>
                    Status: <span class="badge ${turbine.status === 'Operational' ? 'bg-success' : 'bg-warning'}">${turbine.status}</span><br>
                    Capacity: ${turbine.capacity}<br>
                    Turbines: ${turbine.turbines}<br>
                    Safety Zone: ${turbine.buffer_m}m radius<br>
                    <small class="text-muted">Norwegian waters</small>
                </div>
            `);
            
            this.turbineLayer.addLayer(marker);
            
            // Create safety zone circle
            const safetyZone = L.circle([turbine.lat, turbine.lon], {
                radius: turbine.buffer_m,
                color: '#ff6b6b',
                fillColor: '#ff6b6b',
                fillOpacity: 0.1,
                weight: 2,
                dashArray: '5, 5'
            }).bindPopup(`<strong>${turbine.name} Safety Zone</strong><br>${turbine.buffer_m}m radius - Keep clear`);
            
            this.safetyZoneLayer.addLayer(safetyZone);
        });
    },
    
    updateTurbineCount: function() {
        const count = this.turbines.length;
        const activeTurbines = this.turbines.filter(t => t.status === 'Operational').length;
        
        // Update UI counter
        document.getElementById('turbine-count').textContent = count;
        
        // Update tooltip if exists
        const turbineBadge = document.querySelector('.badge-warning');
        if (turbineBadge && turbineBadge.querySelector('#turbine-count')) {
            turbineBadge.title = `${count} wind farms (${activeTurbines} operational)`;
        }
    },
    
    showTurbines: function(showZones = true) {
        if (!window.map) return;
        
        if (window.map.hasLayer(this.turbineLayer)) {
            window.map.removeLayer(this.turbineLayer);
            if (showZones) window.map.removeLayer(this.safetyZoneLayer);
            console.log('Wind turbines hidden');
        } else {
            window.map.addLayer(this.turbineLayer);
            if (showZones) window.map.addLayer(this.safetyZoneLayer);
            console.log('Wind turbines shown');
        }
    },
    
    checkVesselProximity: function(vesselLat, vesselLon) {
        // Check if vessel is too close to any turbine
        const warnings = [];
        
        this.turbines.forEach(turbine => {
            if (!vesselLat || !vesselLon) return;
            
            const distance = this.calculateDistance(
                vesselLat, vesselLon, 
                turbine.lat, turbine.lon
            );
            
            if (distance * 1000 < turbine.buffer_m) { // Convert to meters
                warnings.push({
                    turbine: turbine.name,
                    distance: Math.round(distance * 1000),
                    buffer: turbine.buffer_m,
                    severity: distance * 1000 < turbine.buffer_m * 0.5 ? 'HIGH' : 'MEDIUM'
                });
            }
        });
        
        return warnings;
    },
    
    calculateDistance: function(lat1, lon1, lat2, lon2) {
        // Haversine formula in kilometers
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                 Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                 Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
};