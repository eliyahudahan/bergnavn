// ======================================================
//   Maritime Dashboard - Clean + MET-Based Map Logic
//   No email exposed, no external secrets.
//   Fully backend-driven.
// ======================================================

let map;
let aisLayer;
let weatherLayer;

// Initialize the map
function initMap() {
    map = L.map("map", {
        zoomControl: true,
        scrollWheelZoom: true
    }).setView([63.4305, 10.3951], 8); // Trondheim default

    // Base map from OpenStreetMap
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    // Layers
    aisLayer = L.layerGroup().addTo(map);
    weatherLayer = L.layerGroup().addTo(map);

    // Load initial data
    fetchAIS();
    fetchWeather();

    // Auto-refresh AIS every 30 sec
    setInterval(fetchAIS, 30000);
    // Auto-refresh weather every 5 min
    setInterval(fetchWeather, 300000);
}

// ======================================================
//                 AIS LIVE DATA
// ======================================================

async function fetchAIS() {
    try {
        const response = await fetch("/api/ais/live");
        const data = await response.json();

        aisLayer.clearLayers();

        data.forEach(vessel => {
            if (!vessel.lat || !vessel.lon) return;

            const marker = L.circleMarker([vessel.lat, vessel.lon], {
                radius: 6,
                color: "#0077ff",
                fillColor: "#66aaff",
                fillOpacity: 0.7
            });

            marker.bindPopup(`
                <b>${vessel.name || "Unknown Vessel"}</b><br>
                MMSI: ${vessel.mmsi}<br>
                Speed: ${vessel.speed} kn<br>
                Course: ${vessel.course}°
            `);

            marker.addTo(aisLayer);
        });

    } catch (err) {
        console.error("AIS fetch error:", err);
    }
}

// ======================================================
//                 MET WEATHER (Wind, Waves)
// ======================================================

async function fetchWeather() {
    try {
        const response = await fetch("/api/weather/current");
        const wx = await response.json();

        weatherLayer.clearLayers();

        wx.forEach(point => {
            if (!point.lat || !point.lon) return;

            const icon = L.divIcon({
                className: "weather-marker",
                html: `
                    <div style="font-size: 14px; text-align:center;">
                        🌬️${point.wind_speed} m/s<br>
                        ↗ ${point.wind_dir}°
                    </div>
                `
            });

            L.marker([point.lat, point.lon], { icon }).addTo(weatherLayer);
        });

    } catch (err) {
        console.error("Weather fetch error:", err);
    }
}

// ======================================================
//         Optional: Toggle Layers (Dashboard UI)
// ======================================================

function toggleLayer(layerName, state) {
    if (layerName === "ais") {
        state ? map.addLayer(aisLayer) : map.removeLayer(aisLayer);
    } else if (layerName === "weather") {
        state ? map.addLayer(weatherLayer) : map.removeLayer(weatherLayer);
    }
}

// Export
window.initMap = initMap;
window.toggleLayer = toggleLayer;
