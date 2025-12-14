// backend/static/js/split/maritime_map.js
/**
 * Maritime Map Module for BergNavn Dashboard
 * Handles Leaflet map initialization and AIS vessel display
 */

// Global map variables
let map = null;
let vesselMarkers = [];

/**
 * Initialize the maritime map
 */
function initMap() {
    console.log('🗺️ Initializing maritime map...');
    
    // Initialize map if not already initialized
    if (!map) {
        map = L.map('maritime-map').setView([60.392, 5.324], 8);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(map);
        
        // Add Norwegian waters layer
        L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
            attribution: '© OpenSeaMap',
            opacity: 0.6,
            maxZoom: 18,
        }).addTo(map);
        
        console.log('✅ Map initialized');
    }
    
    return map;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString) {
    if (!isoString) return "Just now";
    
    try {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } catch (e) {
        return isoString.split('T')[1]?.substring(0, 5) || isoString;
    }
}

/**
 * Load AIS data and display vessels on map
 */
async function loadAIS() {
    try {
        console.log('🚢 Fetching AIS data...');
        const response = await fetch('/maritime/api/ais-data');
        const data = await response.json();
        
        console.log(`✅ Loaded ${data.vessels.length} vessels from ${data.source}`);
        
        // Initialize map if not already done
        if (!map) {
            initMap();
        }
        
        // Clear existing vessel markers
        if (vesselMarkers && vesselMarkers.length > 0) {
            vesselMarkers.forEach(marker => map.removeLayer(marker));
            vesselMarkers = [];
        }
        
        // Add vessel markers
        data.vessels.forEach(vessel => {
            // Determine vessel type icon color
            const vesselType = vessel.type?.toLowerCase() || 'unknown';
            let iconColor = '#3498db'; // Default blue
            
            if (vesselType.includes('cargo') || vesselType.includes('container')) {
                iconColor = '#2ecc71'; // Green
            } else if (vesselType.includes('passenger') || vesselType.includes('ferry')) {
                iconColor = '#e74c3c'; // Red
            } else if (vesselType.includes('tanker')) {
                iconColor = '#f39c12'; // Orange
            }
            
            // Create custom vessel icon
            const vesselIcon = L.divIcon({
                className: 'vessel-marker',
                html: `
                    <div class="vessel-icon" style="transform: rotate(${vessel.course || 0}deg);">
                        <i class="bi bi-ship" style="color: ${iconColor}; font-size: 20px;"></i>
                    </div>
                `,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
            
            // Create marker
            const marker = L.marker([vessel.lat, vessel.lon], {
                icon: vesselIcon
            }).bindPopup(`
                <div class="vessel-popup">
                    <strong>${vessel.name}</strong><br>
                    MMSI: ${vessel.mmsi || 'N/A'}<br>
                    Type: ${vessel.type || 'Unknown'}<br>
                    Speed: ${vessel.speed || 0} knots<br>
                    Course: ${vessel.course || 0}°<br>
                    Destination: ${vessel.destination || 'Unknown'}<br>
                    Status: ${vessel.status || 'Unknown'}<br>
                    <small>Updated: ${formatTimestamp(vessel.timestamp)}</small>
                </div>
            `);
            
            marker.addTo(map);
            vesselMarkers.push(marker);
        });
        
        // Update vessel count
        const vesselCount = document.getElementById('vessel-count-number');
        if (vesselCount) {
            vesselCount.textContent = data.vessels.length;
        }
        
        // Update active vessels in stats
        const activeVessels = document.getElementById('active-vessels');
        if (activeVessels) {
            activeVessels.textContent = data.vessels.length;
        }
        
        // Update AIS timestamp
        const aisTimestamp = document.getElementById('ais-timestamp');
        if (aisTimestamp) {
            aisTimestamp.textContent = formatTimestamp(data.timestamp);
        }
        
        // Update map center display
        const mapCenter = document.getElementById('map-center');
        if (mapCenter && map.getCenter()) {
            const center = map.getCenter();
            mapCenter.textContent = `${center.lat.toFixed(2)}°N, ${center.lng.toFixed(2)}°E`;
        }
        
        // Fit map bounds to show all vessels
        if (vesselMarkers.length > 0) {
            const vesselGroup = new L.featureGroup(vesselMarkers);
            map.fitBounds(vesselGroup.getBounds().pad(0.1));
        }
        
    } catch (error) {
        console.error('AIS load error:', error);
        
        // Show fallback message
        const vesselCount = document.getElementById('vessel-count-number');
        if (vesselCount) {
            vesselCount.textContent = 'Error';
        }
        
        const activeVessels = document.getElementById('active-vessels');
        if (activeVessels) {
            activeVessels.textContent = 'Error';
        }
        
        const aisTimestamp = document.getElementById('ais-timestamp');
        if (aisTimestamp) {
            aisTimestamp.textContent = 'Error';
        }
    }
}

/**
 * Initialize map and load data when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🗺️ Maritime map module loaded');
    
    // Initialize map immediately
    initMap();
    
    // Load AIS data after a short delay
    setTimeout(loadAIS, 1000);
    
    // Set up periodic refresh (every 30 seconds)
    setInterval(loadAIS, 30000);
});

// Export functions for global use
window.loadAIS = loadAIS;
window.initMap = initMap;