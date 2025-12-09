// static/js/dashboard.js
// Dashboard glue logic: updates widgets, uses endpoints defined in maritime_routes.py

console.log("Dashboard JS loaded");

async function loadWeatherCard() {
    try {
        const res = await fetch("/weather/api/maritime-weather");
        const payload = await res.json();
        const container = document.getElementById("weather-data") || document.getElementById("weather-card");
        if (!container) return;

        if (payload && payload.status === 'success') {
            const d = payload.data;
            container.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">${d.location || 'Location'}</h6>
                        <div class="h3">${Math.round(d.temperature || 0)}°C</div>
                        <div class="small text-muted">Wind: ${d.wind_speed || 0} m/s</div>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `<div class="alert alert-warning">Weather fallback used</div>`;
        }
    } catch (err) {
        const container = document.getElementById("weather-data") || document.getElementById("weather-card");
        if (container) container.innerHTML = "Weather unavailable";
        console.error("loadWeatherCard error:", err);
    }
}

async function loadShipsCard() {
    try {
        const res = await fetch("/maritime/api/live-ships");
        const payload = await res.json();
        const container = document.getElementById("ships-card") || document.getElementById("ships-card-container");
        if (!container) return;

        if (payload && payload.status === 'success') {
            const count = payload.count || (payload.vessels && payload.vessels.length) || 0;
            container.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">Live Ships</h6>
                        <p class="h4 mb-0">${count}</p>
                        <small class="text-muted">Updated: ${new Date().toLocaleTimeString()}</small>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `<div class="alert alert-secondary">Ships unavailable</div>`;
        }
    } catch (err) {
        console.error("loadShipsCard error:", err);
        const container = document.getElementById("ships-card") || document.getElementById("ships-card-container");
        if (container) container.innerHTML = "Ships unavailable";
    }
}

async function loadOptimizerCard() {
    try {
        const res = await fetch("/maritime/api/optimizer");
        const payload = await res.json();
        const container = document.getElementById("optimizer-card") || document.getElementById("fuel-card-container");
        if (!container) return;

        if (payload && payload.status === 'success' || payload.recommended_speed) {
            const msg = payload.message || `Recommended speed ${payload.recommended_speed || 'N/A'} kn`;
            container.innerHTML = `<div class="card h-100"><div class="card-body"><h6>Fuel Optimizer</h6><p>${msg}</p></div></div>`;
        } else {
            container.innerHTML = `<div class="alert alert-secondary">Optimizer unavailable</div>`;
        }
    } catch (err) {
        console.error("loadOptimizerCard error:", err);
    }
}

async function loadAlertsCard() {
    try {
        const res = await fetch("/maritime/api/alerts");
        const payload = await res.json();
        const container = document.getElementById("alerts-card") || document.getElementById("alerts-card-container");
        if (!container) return;

        if (payload && payload.status === 'success' && payload.alerts) {
            container.innerHTML = `<div class="card h-100"><div class="card-body"><h6>Alerts</h6><p>Total: ${payload.alerts.length}</p></div></div>`;
        } else {
            container.innerHTML = `<div class="alert alert-secondary">No alerts</div>`;
        }
    } catch (err) {
        console.error("loadAlertsCard error:", err);
    }
}

function startDashboardRefresh() {
    loadWeatherCard();
    loadShipsCard();
    loadOptimizerCard();
    loadAlertsCard();

    setInterval(() => {
        loadWeatherCard();
        loadShipsCard();
        loadOptimizerCard();
        loadAlertsCard();
    }, 30000);
}

document.addEventListener("DOMContentLoaded", startDashboardRefresh);
