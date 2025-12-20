// static/js/split/hazard_data.js
/**
 * Hazard Data Module for BergNavn Maritime Dashboard
 * Loads and displays BarentsWatch hazard data on the map
 */

let hazardMarkers = [];
let hazardLayer = null;

/**
 * Load hazard data from BarentsWatch API
 */
async function loadHazardData() {
    try {
        const response = await fetch('/maritime/api/barentswatch/hazards');
        const data = await response.json();
        
        if (data.status === 'success') {
            hazardData = data.hazards;
            updateHazardUI(data.hazards, data.counts);
            
            // If hazards are visible, show them on map
            if (window.hazardsVisible && typeof window.showHazardsOnMap === 'function') {
                window.showHazardsOnMap(data.hazards);
            }
            
            console.log(`Loaded ${data.counts.aquaculture} aquaculture, ${data.counts.cables} cables, ${data.counts.installations} installations`);
        }
    } catch (error) {
        console.error('Failed to load hazard data:', error);
        document.getElementById('hazard-source-status').innerHTML = 
            '<i class="bi bi-exclamation-circle me-1"></i>Hazard data: Connection failed';
    }
}

/**
 * Update the UI with hazard statistics
 */
function updateHazardUI(hazards, counts) {
    // Update hazard summary
    const totalHazards = counts.aquaculture + counts.cables + counts.installations;
    document.getElementById('hazard-summary').textContent = totalHazards;
    
    // Update hazard types text
    const hazardTypes = [];
    if (counts.aquaculture > 0) hazardTypes.push(`${counts.aquaculture} aquaculture`);
    if (counts.cables > 0) hazardTypes.push(`${counts.cables} cables`);
    if (counts.installations > 0) hazardTypes.push(`${counts.installations} installations`);
    document.getElementById('hazard-types').textContent = hazardTypes.join(', ') || 'No hazards';
    
    // Update hazard badges
    const hazardBadge = document.getElementById('hazard-badge');
    const mapHazardBadge = document.getElementById('map-hazard-badge');
    
    if (totalHazards > 0) {
        hazardBadge.style.display = 'inline-block';
        mapHazardBadge.style.display = 'inline-block';
        document.getElementById('hazard-count').textContent = totalHazards;
        document.getElementById('map-hazard-count').textContent = totalHazards;
        
        document.getElementById('hazard-source-status').innerHTML = 
            `<i class="bi bi-check-circle me-1 text-success"></i>Hazard data: ${totalHazards} hazards loaded`;
    } else {
        hazardBadge.style.display = 'none';
        mapHazardBadge.style.display = 'none';
        document.getElementById('hazard-source-status').innerHTML = 
            '<i class="bi bi-info-circle me-1"></i>Hazard data: No hazards in area';
    }
}

/**
 * Show hazards on the map
 */
window.showHazardsOnMap = function(hazards) {
    if (!window.map) {
        console.error('Map not initialized');
        return;
    }
    
    // Clear existing hazard markers
    window.hideHazardsFromMap();
    
    hazardLayer = L.layerGroup();
    
    // Add aquaculture markers
    if (hazards.aquaculture && Array.isArray(hazards.aquaculture)) {
        hazards.aquaculture.forEach(facility => {
            const lat = facility.latitude || facility.lat;
            const lon = facility.longitude || facility.lon;
            
            if (lat && lon) {
                const marker = L.marker([lat, lon], {
                    icon: L.divIcon({
                        className: 'hazard-marker aquaculture-marker',
                        html: '<i class="bi bi-droplet-fill"></i>',
                        iconSize: [20, 20]
                    })
                }).bindPopup(`
                    <strong>${facility.name || 'Aquaculture Facility'}</strong><br>
                    Type: Aquaculture<br>
                    Owner: ${facility.owner || 'Unknown'}<br>
                    Size: ${facility.size_hectares || 'N/A'} hectares
                `);
                hazardLayer.addLayer(marker);
            }
        });
    }
    
    // Add cable markers
    if (hazards.cables && Array.isArray(hazards.cables)) {
        hazards.cables.forEach(cable => {
            const lat = cable.latitude || cable.lat;
            const lon = cable.longitude || cable.lon;
            
            if (lat && lon) {
                const marker = L.marker([lat, lon], {
                    icon: L.divIcon({
                        className: 'hazard-marker cable-marker',
                        html: '<i class="bi bi-lightning-charge-fill"></i>',
                        iconSize: [20, 20]
                    })
                }).bindPopup(`
                    <strong>${cable.name || 'Subsea Cable'}</strong><br>
                    Type: Subsea Cable<br>
                    Voltage: ${cable.voltage || 'Unknown'}<br>
                    Owner: ${cable.owner || 'Unknown'}
                `);
                hazardLayer.addLayer(marker);
            }
        });
    }
    
    // Add installation markers
    if (hazards.installations && Array.isArray(hazards.installations)) {
        hazards.installations.forEach(installation => {
            const lat = installation.latitude || installation.lat;
            const lon = installation.longitude || installation.lon;
            
            if (lat && lon) {
                const marker = L.marker([lat, lon], {
                    icon: L.divIcon({
                        className: 'hazard-marker installation-marker',
                        html: '<i class="bi bi-tower"></i>',
                        iconSize: [20, 20]
                    })
                }).bindPopup(`
                    <strong>${installation.name || 'Offshore Installation'}</strong><br>
                    Type: ${installation.type || 'Platform'}<br>
                    Height: ${installation.height_m || 'N/A'}m<br>
                    Owner: ${installation.owner || 'Unknown'}
                `);
                hazardLayer.addLayer(marker);
            }
        });
    }
    
    // Add hazard layer to map
    hazardLayer.addTo(window.map);
    
    // Add to layer control if it exists
    if (window.layerControl) {
        window.layerControl.addOverlay(hazardLayer, 'Hazards');
    }
};

/**
 * Hide hazards from the map
 */
window.hideHazardsFromMap = function() {
    if (hazardLayer) {
        if (window.map && window.map.hasLayer(hazardLayer)) {
            window.map.removeLayer(hazardLayer);
        }
        if (window.layerControl) {
            window.layerControl.removeLayer(hazardLayer);
        }
        hazardLayer = null;
    }
};

/**
 * Toggle map layers (for use by toggleDataView)
 */
window.toggleMapLayers = function() {
    if (!window.map) return;
    
    // Example: Cycle through different base layers
    const baseLayers = window.map._layers;
    // Implementation depends on your map setup
    console.log('Toggle map layers called');
};