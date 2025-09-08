// =======================================
// BergNavn Maritime - Dashboard JS
// Author: BergNavn Maritime Team
// Credits: MET Norway API (https://api.met.no)
// =======================================

// ==================== SETTINGS ====================
const APP_CONFIG = {
    USER_AGENT: 'BergNavnMaritime/1.0 (framgangsrik747@gmail.com)',
    CACHE_TIME: 5 * 60 * 1000, // 5 minutes
    TIMEOUT: 10000 // 10 seconds
};

// ==================== MARITIME ROUTES ====================
const MARITIME_ROUTES = [
    {
        id: 1,
        name: "Bergen → Trondheim",
        time: 12,
        distance: 200,
        ports: [
            { name: "Bergen", required: true },
            { name: "Trondheim", required: true }
        ],
        coords: [
            { lat: 60.39, lon: 5.32 },
            { lat: 63.43, lon: 10.39 }
        ]
    },
    {
        id: 2,
        name: "Stavanger → Bergen",
        time: 6,
        distance: 120,
        ports: [
            { name: "Stavanger", required: true },
            { name: "Bergen", required: true }
        ],
        coords: [
            { lat: 58.97, lon: 5.73 },
            { lat: 60.39, lon: 5.32 }
        ]
    }
];

// ==================== WEATHER SERVICE ====================
class WeatherService {
    constructor() {
        this.cache = new Map();
        this.isOnline = false;
    }

    async getWeatherData(lat, lon) {
        const cacheKey = `${lat},${lon}`;
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < APP_CONFIG.CACHE_TIME) {
                return cached.data;
            }
        }

        try {
            const data = await this.fetchMetNorwayData(lat, lon);
            this.cache.set(cacheKey, { data, timestamp: Date.now() });
            this.isOnline = true;
            return data;
        } catch (err) {
            console.warn('MET Norway API failed, using mock data', err);
            this.isOnline = false;
            return this.generateMockData(lat, lon);
        }
    }

    async fetchMetNorwayData(lat, lon) {
        const url = `https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=${lat}&lon=${lon}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), APP_CONFIG.TIMEOUT);

        const response = await fetch(url, {
            headers: { 'User-Agent': APP_CONFIG.USER_AGENT },
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const apiData = await response.json();
        return this.parseWeatherData(apiData);
    }

    parseWeatherData(apiData) {
        const current = apiData.properties?.timeseries?.[0];
        if (!current) throw new Error('Invalid API data structure');

        const details = current.data.instant.details;
        return {
            temperature: details.air_temperature,
            windSpeed: details.wind_speed,
            windDirection: details.wind_from_direction,
            humidity: details.relative_humidity,
            pressure: details.air_pressure_at_sea_level,
            condition: current.data.next_1_hours?.summary.symbol_code || 'clearsky',
            updatedAt: new Date().toISOString(),
            isLive: true,
            source: 'MET Norway API'
        };
    }

    generateMockData(lat, lon) {
        const temp = 10 + (lat - 58) * 2 + (Math.random() * 6 - 3);
        const wind = 5 + Math.random() * 8;
        const conditions = ['clearsky', 'fair', 'partlycloudy', 'cloudy', 'lightrain'];
        return {
            temperature: Math.round(temp*10)/10,
            windSpeed: Math.round(wind*10)/10,
            windDirection: Math.floor(Math.random()*360),
            humidity: Math.floor(60 + Math.random()*30),
            pressure: 1010 + Math.floor(Math.random()*20),
            condition: conditions[Math.floor(Math.random()*conditions.length)],
            updatedAt: new Date().toISOString(),
            isLive: false,
            source: 'Mock Data (Offline)'
        };
    }
}

// ==================== PORT STATUS API ====================
async function checkPortStatus(portName) {
    // Placeholder for external API; currently returns open for demonstration
    // In future, can call actual API to check if port is closed
    return { name: portName, open: true };
}

// ==================== STATUS MANAGEMENT ====================
function updateStatus(isOnline, message) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    const apiMode = document.getElementById('api-mode');
    dot.className = 'status-dot ' + (isOnline ? 'status-online' : 'status-offline');
    text.textContent = message;
    apiMode.textContent = isOnline ? 'Live' : 'Offline';
    apiMode.style.color = isOnline ? '#28a745' : '#dc3545';
}

function updateLastUpdateTime() {
    document.getElementById('last-update').textContent =
        'Updated: ' + new Date().toLocaleTimeString('he-IL');
}

// ==================== RENDERING ====================
async function renderRoutes() {
    const container = document.getElementById('routes-container');
    let html = '<div class="routes-grid">';

    for (let route of MARITIME_ROUTES) {
        html += `
            <div class="route-card">
                <h3>${route.name}</h3>
                <p>⏱️ ${route.time} hours | 📏 ${route.distance} nautical miles</p>
                <p>🛟 Ports: ${route.ports.map(p => p.name).join(" → ")}</p>
                <button class="btn" onclick="checkRouteWeather(${route.id})">🌤️ Check Weather</button>
                <div id="weather-${route.id}"></div>
            </div>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

// ==================== WEATHER CHECK ====================
async function checkRouteWeather(routeId) {
    const route = MARITIME_ROUTES.find(r => r.id === routeId);
    if (!route) return;

    const weatherDiv = document.getElementById(`weather-${route.id}`);
    weatherDiv.innerHTML = '<div class="loader"></div><p>Connecting...</p>';

    try {
        // Check port status for optional skipping logic
        for (let port of route.ports) {
            const status = await checkPortStatus(port.name);
            port.open = status.open;
        }

        const ws = new WeatherService();
        const weatherData = await ws.getWeatherData(route.coords[0].lat, route.coords[0].lon);

        displayWeatherResult(routeId, weatherData);
        updateStatus(weatherData.isLive, weatherData.isLive ? 'Connected to MET Norway' : 'Offline / Mock');
        updateLastUpdateTime();

    } catch (err) {
        weatherDiv.innerHTML = `<div class="alert alert-danger">❌ Error: ${err.message}</div>`;
        updateStatus(false, 'Connection Error');
    }
}

function displayWeatherResult(routeId, weatherData) {
    const weatherDiv = document.getElementById(`weather-${routeId}`);
    const translations = {
        clearsky: "Clear ☀️",
        fair: "Fair 🌤️",
        partlycloudy: "Partly Cloudy ⛅",
        cloudy: "Cloudy ☁️",
        lightrain: "Light Rain 🌦️",
        rain: "Rain 🌧️",
        heavyrain: "Heavy Rain ⛈️",
        lightsnow: "Light Snow 🌨️",
        snow: "Snow ❄️"
    };
    const conditionText = translations[weatherData.condition] || weatherData.condition;

    const html = `
        <div class="weather-details">
            <div style="color: ${weatherData.isLive ? '#28a745' : '#ffc107'}; font-weight: bold;">
                ${weatherData.isLive ? '✅ Live Data' : '⚠️ Mock Data'}
            </div>
            <div class="weather-row"><span>🌡️ Temp:</span><span>${weatherData.temperature}°C</span></div>
            <div class="weather-row"><span>💨 Wind:</span><span>${weatherData.windSpeed} m/s</span></div>
            <div class="weather-row"><span>🧭 Wind Dir:</span><span>${weatherData.windDirection}°</span></div>
            <div class="weather-row"><span>💧 Humidity:</span><span>${weatherData.humidity}%</span></div>
            <div class="weather-row"><span>📊 Pressure:</span><span>${weatherData.pressure} hPa</span></div>
            <div class="weather-row"><span>☁️ Condition:</span><span>${conditionText}</span></div>
            <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                Source: ${weatherData.source}
            </div>
        </div>
    `;
    weatherDiv.innerHTML = html;
}

// ==================== INITIALIZE ====================
async function initializeApp() {
    const ws = new WeatherService();
    const testData = await ws.getWeatherData(60.39, 5.32);
    updateStatus(testData.isLive, testData.isLive ? 'Connected to MET Norway' : 'Offline');
    updateLastUpdateTime();
    renderRoutes();
}

// ==================== START ====================
document.addEventListener('DOMContentLoaded', initializeApp);
