// static/js/dashboard.js

console.log("Dashboard JS loaded");

// -------- WEATHER --------
async function loadWeather() {
    try {
        const res = await fetch("/weather/api/maritime-weather");
        const data = await res.json();

        document.getElementById("weather-card").innerHTML = `
            <h3>Weather</h3>
            <p>Temp: ${data.data.temperature}°C</p>
            <p>Wind: ${data.data.wind_speed} m/s</p>
            <p>Humidity: ${data.data.humidity}%</p>
        `;
    } catch (err) {
        document.getElementById("weather-card").innerHTML = "Weather unavailable";
    }
}

// -------- LIVE SHIPS --------
async function loadShips() {
    try {
        const res = await fetch("/maritime/api/live-ships");
        const ships = await res.json();

        document.getElementById("ships-card").innerHTML =
            `<h3>Live Ships</h3><p>Ships loaded: ${ships.length}</p>`;
    } catch (err) {
        document.getElementById("ships-card").innerHTML = "Ships unavailable";
    }
}

// -------- OPTIMIZER --------
async function loadOptimizer() {
    try {
        const res = await fetch("/maritime/api/optimizer");
        const data = await res.json();
        document.getElementById("optimizer-card").innerHTML =
            `<h3>Fuel Optimization</h3><p>${data.message}</p>`;
    } catch (err) {
        document.getElementById("optimizer-card").innerHTML = "Optimizer unavailable";
    }
}

// -------- ALERTS --------
async function loadAlerts() {
    try {
        const res = await fetch("/maritime/api/alerts");
        const alerts = await res.json();
        document.getElementById("alerts-card").innerHTML =
            `<h3>Alerts</h3><p>Total alerts: ${alerts.length}</p>`;
    } catch (err) {
        document.getElementById("alerts-card").innerHTML = "Alerts unavailable";
    }
}

// -------- START --------
loadWeather();
loadShips();
loadOptimizer();
loadAlerts();

// Refresh every 30 sec
setInterval(() => {
    loadWeather();
    loadShips();
    loadOptimizer();
    loadAlerts();
}, 30000);
