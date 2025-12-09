// static/js/maritime.js
// Core maritime real-time map + data fetch logic.
// English comments only.

let map;
let aisLayer;
let weatherLayer;

// Initialize the map element with id "maritime-map" or "map"
function initMap() {
    const mapId = document.getElementById('maritime-map') ? 'maritime-map' : 'map';
    map = L.map(mapId, {
        zoomControl: true,
        scrollWheelZoom: true
    }).setView([63.4305, 10.3951], 7);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    aisLayer = L.layerGroup().addTo(map);
    weatherLayer = L.layerGroup().addTo(map);

    // Initial load
    fetchAIS();
    fetchWeather();

    // Auto-refresh
    setInterval(fetchAIS, 30000);       // AIS every 30s
    setInterval(fetchWeather, 300000);  // Weather every 5min
}

async function fetchAIS() {
    try {
        const res = await fetch("/maritime/api/live-ships");
        const payload = await res.json();
        if (!payload || payload.status !== 'success') {
            console.warn("AIS payload not success", payload);
            return;
        }
        const data = payload.vessels || [];

        aisLayer.clearLayers();

        data.forEach(v => {
            const lat = parseFloat(v.lat || v.latitude || v.lat_dd);
            const lon = parseFloat(v.lon || v.longitude || v.lon_dd);
            if (!lat || !lon) return;

            const marker = L.circleMarker([lat, lon], {
                radius: 6,
                color: "#0077ff",
                fillColor: "#66aaff",
                fillOpacity: 0.8
            });

            const popup = `<b>${v.name || "Unknown Vessel"}</b><br/>MMSI: ${v.mmsi || 'N/A'}<br/>SOG: ${v.sog || v.speed || 'N/A'} kn`;
            marker.bindPopup(popup);
            marker.addTo(aisLayer);
        });
    } catch (err) {
        console.error("AIS fetch error:", err);
    }
}

async function fetchWeather() {
    try {
        const res = await fetch("/weather/api/maritime-weather");
        const payload = await res.json();
        // payload may be {status:'success', data: {...}} or fallback
        let data = null;
        if (payload && payload.status === 'success') data = [payload.data];
        else if (Array.isArray(payload)) data = payload;
        else data = [];

        weatherLayer.clearLayers();

        data.forEach(point => {
            const lat = parseFloat(point.lat || point.latitude || point.lat_dd);
            const lon = parseFloat(point.lon || point.longitude || point.lon_dd);
            if (!lat || !lon) return;

            const icon = L.divIcon({
                className: "weather-marker",
                html: `<div style="font-size:12px;text-align:center;">${point.source || 'WX'}<br/>${Math.round(point.temperature||0)}°C</div>`
            });

            L.marker([lat, lon], { icon }).addTo(weatherLayer);
        });
    } catch (err) {
        console.error("Weather fetch error:", err);
    }
}

// Expose functions globally
window.initMap = initMap;
window.fetchAIS = fetchAIS;
window.fetchWeather = fetchWeather;
