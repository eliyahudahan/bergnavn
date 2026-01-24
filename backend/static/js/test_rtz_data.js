
// Test RTZ data for map display
window.testRTZRoutes = [
    {
        name: 'Bergen to Oslo Commercial Route',
        clean_name: 'Bergen - Oslo Coastal Route',
        origin: 'Bergen',
        destination: 'Oslo',
        total_distance_nm: 210.5,
        waypoint_count: 24,
        source_city: 'bergen',
        data_source: 'test_data',
        waypoints: [
            { lat: 60.3913, lon: 5.3221, name: 'Bergen Harbor' },
            { lat: 60.3945, lon: 5.3182, name: 'Bergen West' },
            { lat: 60.3978, lon: 5.3105, name: 'Fjord Entrance' },
            { lat: 60.4050, lon: 5.3050, name: 'Coastal Waypoint' },
            { lat: 60.4200, lon: 5.3000, name: 'Hjeltefjorden' },
            { lat: 60.4500, lon: 5.2800, name: 'Sotra Passage' },
            { lat: 60.5000, lon: 5.2500, name: 'Fedje Area' }
        ]
    },
    {
        name: 'Stavanger Offshore Supply Route',
        clean_name: 'Stavanger - North Sea',
        origin: 'Stavanger',
        destination: 'North Sea Platform',
        total_distance_nm: 85.2,
        waypoint_count: 18,
        source_city: 'stavanger',
        data_source: 'test_data',
        waypoints: [
            { lat: 58.9699, lon: 5.7331, name: 'Stavanger Port' },
            { lat: 58.9750, lon: 5.7400, name: 'Hafrsfjord' },
            { lat: 59.0000, lon: 5.7500, name: 'Sola Approach' },
            { lat: 59.0500, lon: 5.8000, name: 'Offshore Exit' }
        ]
    },
    {
        name: 'Trondheim Coastal Passage',
        clean_name: 'Trondheim - Coastal',
        origin: 'Trondheim',
        destination: 'Coastal Waters',
        total_distance_nm: 45.8,
        waypoint_count: 12,
        source_city: 'trondheim',
        data_source: 'test_data',
        waypoints: [
            { lat: 63.4305, lon: 10.3951, name: 'Trondheim Harbor' },
            { lat: 63.4350, lon: 10.4000, name: 'Trondheimsfjord' },
            { lat: 63.4400, lon: 10.4100, name: 'Mid Fjord' }
        ]
    }
];

// Add to window for testing
window.getTestRTZRoutes = function() {
    return {
        success: true,
        routes: window.testRTZRoutes,
        count: window.testRTZRoutes.length,
        source: 'test_data'
    };
};

// Override fetch for testing
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        if (url.includes('/api/rtz/routes') || url.includes('/maritime/api/rtz/routes')) {
            console.log('🔧 Using test RTZ routes data');
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(window.getTestRTZRoutes()),
                status: 200
            });
        }
        return originalFetch.call(this, url, options);
    };
}
