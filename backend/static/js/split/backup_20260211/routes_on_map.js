// Auto-generated route data for map
var routeData = [
];

// Add routes to map
function addRoutesToMap() {
    if (typeof window.map === 'undefined') {
        console.log('Map not ready yet');
        setTimeout(addRoutesToMap, 1000);
        return;
    }
    
    console.log('Adding', routeData.length, 'routes to map');
    
    routeData.forEach(function(route) {
        if (route.coordinates && route.coordinates.length >= 2) {
            // Create polyline
            var polyline = L.polyline(route.coordinates, {
                color: '#3498db',
                weight: 3,
                opacity: 0.7
            }).addTo(window.map);
            
            // Add popup
            polyline.bindPopup(`
                <strong>${route.name}</strong><br>
                ${route.origin} → ${route.destination}<br>
                Distance: ${route.distance} nm
            `);
        }
    });
}

// Run when map is ready
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(addRoutesToMap, 2000);
});
