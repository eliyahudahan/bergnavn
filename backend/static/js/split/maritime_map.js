/**
 * Maritime Map Module for BergNavn Dashboard
 * Handles Leaflet map initialization and AIS vessel display
 * FIXED: Adjusted to work with current dashboard structure
 */

// Global map variables
let map = null;
let vesselMarkers = [];

/**
 * Initialize the maritime map
 */
function initMap() {
    console.log('🗺️ Initializing maritime map...');
    
    const mapElement = document.getElementById('maritime-map');
    if (!mapElement) {
        console.error('Map container not found');
        return null;
    }
    
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
        
        console.log(`✅ Loaded ${data.vessels ? data.vessels.length : 0} vessels`);
        
        // Initialize map if not already done
        if (!map) {
            initMap();
        }
        
        // Clear existing vessel markers
        if (vesselMarkers && vesselMarkers.length > 0) {
            vesselMarkers.forEach(marker => {
                if (marker && map) map.removeLayer(marker);
            });
            vesselMarkers = [];
        }
        
        // Check if we have vessel data
        if (!data.vessels || data.vessels.length === 0) {
            console.log('No vessels found in Norwegian waters');
            
            // Update UI with zero count
            updateVesselCountUI(0);
            return;
        }
        
        // Add vessel markers
        data.vessels.forEach(vessel => {
            if (!vessel.lat || !vessel.lon) return;
            
            // Determine vessel type icon color
            const vesselType = (vessel.type || '').toLowerCase();
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
                    <strong>${vessel.name || 'Unknown'}</strong><br>
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
        
        // Update vessel count in UI
        updateVesselCountUI(data.vessels.length);
        
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
        
        // Fit map bounds to show all vessels if we have markers
        if (vesselMarkers.length > 0) {
            const vesselGroup = L.featureGroup(vesselMarkers);
            map.fitBounds(vesselGroup.getBounds().pad(0.1));
        }
        
    } catch (error) {
        console.error('AIS load error:', error);
        
        // Show fallback message
        updateVesselCountUI('Error');
    }
}

/**
 * Update vessel count in all UI elements
 */
function updateVesselCountUI(count) {
    // Update all possible vessel count elements
    const countElements = [
        'vessel-count',
        'vessel-count-number',
        'active-vessels',
        'live-vessel-count'
    ];
    
    countElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = count;
        }
    });
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

// ============================================================================
// RTZ Routes Integration
// ============================================================================

/**
 * Initialize RTZ routes when map is fully loaded
 */
function initializeRTZRoutes() {
    // Wait a moment for map to be ready, then initialize RTZ
    setTimeout(() => {
        if (typeof map !== 'undefined' && map && typeof initRTZRoutes === 'function') {
            const rtzManager = initRTZRoutes(map);
            if (rtzManager) {
                console.log('RTZ routes integration complete');
                
                // Optional: Auto-show panel on first load
                // setTimeout(() => rtzManager.togglePanel(), 3000);
            }
        } else {
            console.warn('RTZ routes not initialized - map or initRTZRoutes not available');
        }
    }, 2000);
}

// Initialize RTZ routes when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait for map to be initialized, then set up RTZ routes
    setTimeout(initializeRTZRoutes, 1500);
});