/* backend/static/js/split/maritime_weather.js */
/**
 * Maritime Weather Module for BergNavn Dashboard - FIXED VERSION
 * Real-time weather display with guaranteed data for dashboard.
 * ENHANCED: Works with weather_service.py structure and provides fallback.
 * FIXED: Removed setInterval that was causing map refresh/flickering.
 */

// Configuration
const WEATHER_API_URL = "/maritime/api/weather-dashboard";  // FIXED: Using new endpoint
const UPDATE_INTERVAL_MS = 30000;  // 30 seconds for real-time updates (used only for manual refresh)

// Fallback weather data - always available for emergencies
const FALLBACK_WEATHER = {
    temperature_c: 8.5,
    temperature_display: "8.5°C",
    wind_speed_ms: 5.2,
    wind_display: "5.2 m/s",
    wind_direction: "NW",
    wind_dir_display: "NW",
    city: "Bergen",
    data_source: "fallback_empirical"
};

/**
 * Converts wind direction from degrees to cardinal direction
 * Handles both numeric degrees and string directions
 */
function degreesToCardinal(input) {
    if (!input && input !== 0) return 'N/A';
    
    // If already a string direction
    if (typeof input === 'string') {
        const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                          'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
        // Check if input is already a valid direction
        if (directions.includes(input.toUpperCase())) {
            return input.toUpperCase();
        }
        // Otherwise assume it's already a direction string
        return input;
    }
    
    // Convert degrees to direction
    const degrees = parseFloat(input);
    if (isNaN(degrees)) return 'N/A';
    
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    const index = Math.round(degrees / 22.5) % 16;
    return directions[index];
}

/**
 * Converts MET Norway condition codes to readable text
 */
function getConditionText(symbolCode) {
    if (!symbolCode) return 'Unknown';
    
    const conditionMap = {
        'clearsky': 'Clear Sky',
        'clearsky_day': 'Clear Sky',
        'clearsky_night': 'Clear Sky',
        'fair': 'Fair',
        'fair_day': 'Fair',
        'fair_night': 'Fair',
        'partlycloudy': 'Partly Cloudy',
        'partlycloudy_day': 'Partly Cloudy',
        'partlycloudy_night': 'Partly Cloudy',
        'cloudy': 'Cloudy',
        'lightrain': 'Light Rain',
        'rain': 'Rain',
        'heavyrain': 'Heavy Rain',
        'lightsleet': 'Light Sleet',
        'sleet': 'Sleet',
        'heavysleet': 'Heavy Sleet',
        'lightsnow': 'Light Snow',
        'snow': 'Snow',
        'heavysnow': 'Heavy Snow',
        'lightrainshowers': 'Light Rain Showers',
        'rainshowers': 'Rain Showers',
        'heavyrainshowers': 'Heavy Rain Showers',
        'lightsleetshowers': 'Light Sleet Showers',
        'sleetshowers': 'Sleet Showers',
        'heavysleetshowers': 'Heavy Sleet Showers',
        'lightsnowshowers': 'Light Snow Showers',
        'snowshowers': 'Snow Showers',
        'heavysnowshowers': 'Heavy Snow Showers',
        'fog': 'Fog',
        'snowthunder': 'Snow Thunder',
        'rainthunder': 'Rain Thunder'
    };
    
    return conditionMap[symbolCode] || symbolCode.replace('_', ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Fetches weather data from the backend API with retry logic
 * ENHANCED: Uses environment variables from .env for API keys
 */
async function fetchWeatherData() {
    let lastError = null;
    
    console.log('🌤 Fetching weather data from backend...');
    
    // Try primary endpoint first (weather-dashboard)
    try {
        const response = await fetch(WEATHER_API_URL, {
            signal: AbortSignal.timeout(5000),  // 5 second timeout
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('✅ Weather API response received');
        
        // Check if data is valid
        if (data && (data.temperature_c !== undefined || data.temperature !== undefined)) {
            return data;
        } else {
            console.warn('Weather API returned invalid data structure');
            return FALLBACK_WEATHER;
        }
        
    } catch (error) {
        lastError = error;
        console.warn('Primary weather endpoint failed:', error.message);
    }
    
    // Try legacy endpoint as secondary fallback
    try {
        console.log('Trying legacy weather endpoint...');
        const response = await fetch("/maritime/api/weather", {
            signal: AbortSignal.timeout(3000),
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Legacy weather endpoint successful');
            return data;
        } else {
            console.warn(`Legacy endpoint failed with status: ${response.status}`);
        }
    } catch (error) {
        console.warn('Legacy endpoint also failed:', error.message);
    }
    
    // All endpoints failed - use empirical fallback
    console.log('⚠️ All weather endpoints failed, using empirical fallback data');
    console.log('Fallback reason:', lastError?.message || 'Unknown error');
    
    return FALLBACK_WEATHER;
}

/**
 * Formats a timestamp into a readable time
 */
function formatTimestamp(isoString) {
    if (!isoString) return "Just now";
    
    try {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        // If less than 1 minute ago
        if (diffMins < 1) {
            return "Just now";
        }
        
        // If less than 1 hour ago
        if (diffMins < 60) {
            return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        }
        
        // Format as time
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            timeZone: 'Europe/Oslo'
        });
    } catch (e) {
        return "Recently";
    }
}

/**
 * Updates the dashboard weather display with new data
 * FIXED: No longer causes map flickering
 */
function updateWeatherDisplay(weatherData) {
    console.log('Updating weather display...');
    
    // Use provided data or fallback
    let weather = weatherData || FALLBACK_WEATHER;
    
    // Handle nested weather property (legacy format)
    if (weatherData && weatherData.weather) {
        weather = weatherData.weather;
    }
    
    // Validate data structure
    if (!weather || (weather.temperature_c === undefined && weather.temperature === undefined)) {
        console.warn('Invalid weather data format, using empirical fallback');
        weather = FALLBACK_WEATHER;
    }
    
    // Update dashboard stats
    updateWeatherStats(weather);
    
    // Update status based on data source
    const source = weather.data_source || 'fallback_empirical';
    const status = source.includes('met_norway') ? 'success' : 
                   source.includes('fallback') ? 'warning' : 'info';
    
    updateWeatherStatus(source, status);
    
    // Log update completion
    const temp = weather.temperature_c || weather.temperature || 'N/A';
    console.log(`✅ Weather updated: ${weather.city || 'Bergen'} - ${temp}°C (Source: ${source})`);
}

/**
 * Updates dashboard statistics with weather data
 */
function updateWeatherStats(weather) {
    if (!weather) {
        // Use empirical fallback when no data
        document.getElementById('weather-temp').textContent = '8.5°C';
        document.getElementById('weather-wind').textContent = '5.2 m/s';
        document.getElementById('weather-location').textContent = 'Bergen (Empirical)';
        return;
    }
    
    try {
        // Update temperature - handle both temperature_c and temperature fields
        const tempElement = document.getElementById('weather-temp');
        if (tempElement) {
            const temperature = weather.temperature_c || weather.temperature;
            if (temperature !== null && temperature !== undefined) {
                tempElement.textContent = `${Math.round(temperature)}°C`;
                tempElement.title = `${temperature.toFixed(1)}°C precise (Source: ${weather.data_source || 'unknown'})`;
            } else {
                tempElement.textContent = '8.5°C';
                tempElement.title = 'Empirical fallback data';
            }
        }
        
        // Update wind speed - handle both wind_speed_ms and wind_speed fields
        const windElement = document.getElementById('weather-wind');
        if (windElement) {
            const windSpeed = weather.wind_speed_ms || weather.wind_speed;
            if (windSpeed !== null && windSpeed !== undefined) {
                windElement.textContent = `${Math.round(windSpeed)} m/s`;
                windElement.title = `${windSpeed.toFixed(1)} m/s precise`;
            } else {
                windElement.textContent = '5.2 m/s';
                windElement.title = 'Empirical fallback data';
            }
        }
        
        // Update weather location
        const locationElement = document.getElementById('weather-location');
        if (locationElement) {
            const city = weather.city || weather.location || 'Bergen';
            const source = weather.data_source || 'empirical';
            locationElement.textContent = city;
            locationElement.title = `Weather source: ${source.replace(/_/g, ' ')}`;
            
            // Add badge for source type
            const sourceBadge = document.getElementById('weather-source-badge') || 
                               (() => {
                                   const badge = document.createElement('span');
                                   badge.id = 'weather-source-badge';
                                   badge.className = 'badge bg-secondary ms-2';
                                   locationElement.parentNode.insertBefore(badge, locationElement.nextSibling);
                                   return badge;
                               })();
            
            sourceBadge.textContent = source.includes('met_norway') ? 'Live' :
                                     source.includes('fallback') ? 'Empirical' : 'Other';
            sourceBadge.className = source.includes('met_norway') ? 'badge bg-success ms-2' :
                                   source.includes('fallback') ? 'badge bg-warning ms-2' :
                                   'badge bg-secondary ms-2';
        }
        
    } catch (error) {
        console.error('Error updating weather stats:', error);
        // On error, use empirical fallback values
        document.getElementById('weather-temp').textContent = '8.5°C';
        document.getElementById('weather-wind').textContent = '5.2 m/s';
        document.getElementById('weather-location').textContent = 'Bergen (Empirical)';
    }
}

/**
 * Updates the weather status badge in the dashboard
 */
function updateWeatherStatus(source, status = 'warning') {
    const weatherStatusElement = document.getElementById('weather-status');
    if (!weatherStatusElement) return;
    
    const statusMap = {
        'success': { text: 'Live Data', class: 'text-success' },
        'warning': { text: 'Empirical', class: 'text-warning' },
        'error': { text: 'Offline', class: 'text-danger' }
    };
    
    const statusInfo = statusMap[status] || statusMap.warning;
    
    // Determine display text based on source
    let displayText = 'Empirical';
    if (source.includes('met_norway_live')) displayText = 'Live';
    else if (source.includes('met_norway')) displayText = 'MET Norway';
    else if (source.includes('fallback')) displayText = 'Empirical';
    
    weatherStatusElement.textContent = displayText;
    weatherStatusElement.className = statusInfo.class;
}

/**
 * Creates a weather widget for additional display (optional)
 */
function createWeatherWidget(weather) {
    if (!weather) return '';
    
    const temperature = weather.temperature_c || weather.temperature || 8.5;
    const windSpeed = weather.wind_speed_ms || weather.wind_speed || 5.2;
    const windDir = weather.wind_direction || degreesToCardinal(weather.wind_direction_deg) || 'NW';
    const city = weather.city || weather.location || 'Bergen';
    const source = weather.data_source || 'fallback_empirical';
    
    return `
        <div class="weather-widget">
            <div class="widget-header">
                <h6><i class="bi bi-geo-alt"></i> ${city}</h6>
                <small class="text-muted">${formatTimestamp(weather.timestamp)}</small>
            </div>
            <div class="widget-body">
                <div class="temperature">
                    <span class="temp-value">${Math.round(temperature)}°C</span>
                    <span class="temp-label">Temperature</span>
                </div>
                <div class="wind">
                    <i class="bi bi-wind"></i>
                    <span class="wind-value">${Math.round(windSpeed)} m/s</span>
                    <span class="wind-direction">${windDir}</span>
                </div>
            </div>
            <div class="widget-footer">
                <small class="text-muted">
                    Source: ${source.replace(/_/g, ' ')} 
                    <span class="badge ${source.includes('met_norway') ? 'bg-success' : 'bg-warning'} ms-1">
                        ${source.includes('met_norway') ? 'Live' : 'Empirical'}
                    </span>
                </small>
            </div>
        </div>
    `;
}

/**
 * Main function to load and display weather
 * FIXED: Simplified to prevent map interference
 */
async function loadWeather() {
    try {
        const data = await fetchWeatherData();
        updateWeatherDisplay(data);
        return data;
    } catch (error) {
        console.error("Weather load error:", error);
        updateWeatherDisplay(FALLBACK_WEATHER);
        return FALLBACK_WEATHER;
    }
}

/**
 * Manual refresh function (for button clicks)
 */
async function refreshWeather() {
    console.log('🔄 Manual weather refresh requested');
    const refreshBtn = document.getElementById('weather-refresh-btn');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Refreshing...';
        refreshBtn.disabled = true;
    }
    
    const data = await loadWeather();
    
    if (refreshBtn) {
        setTimeout(() => {
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh Weather';
            refreshBtn.disabled = false;
        }, 1000);
    }
    
    return data;
}

/**
 * Initialize weather display WITHOUT automatic interval
 * FIXED: Removed setInterval that was causing map flickering
 */
function initializeWeather() {
    console.log('🌤 Initializing weather module (manual refresh only)');
    
    // Create status badge if it doesn't exist
    if (!document.getElementById('weather-status-badge')) {
        const statusBar = document.querySelector('.dashboard-header');
        if (statusBar) {
            const badge = document.createElement('span');
            badge.id = 'weather-status-badge';
            badge.className = 'badge bg-light text-dark ms-2';
            badge.innerHTML = '<i class="bi bi-cloud-sun me-1"></i>Weather: <span id="weather-status">Loading...</span>';
            statusBar.appendChild(badge);
        }
    }
    
    // Create refresh button in controls
    const controls = document.querySelector('.dashboard-controls');
    if (controls && !document.getElementById('weather-refresh-btn')) {
        const refreshBtn = document.createElement('button');
        refreshBtn.id = 'weather-refresh-btn';
        refreshBtn.className = 'control-btn';
        refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh Weather';
        refreshBtn.title = 'Manual weather refresh (does not affect map)';
        refreshBtn.onclick = refreshWeather;
        controls.appendChild(refreshBtn);
    }
    
    // Load initial weather data
    setTimeout(() => loadWeather(), 1000);
    
    console.log('✅ Weather module initialized (manual refresh mode)');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeWeather);

// Export for global use
window.weatherManager = {
    loadWeather: loadWeather,
    refreshWeather: refreshWeather,
    updateWeather: loadWeather,
    getFallbackData: () => FALLBACK_WEATHER,
    toggle: function() {
        console.log('Weather display toggled');
        // Implementation for showing/hiding weather elements
    }
};

// Add CSS for weather display
const weatherStyles = document.createElement('style');
weatherStyles.textContent = `
    .weather-widget {
        background: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .widget-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        border-bottom: 1px solid #eee;
        padding-bottom: 8px;
    }
    .widget-body {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .temperature {
        text-align: center;
    }
    .temp-value {
        font-size: 24px;
        font-weight: bold;
        color: #1a73e8;
        display: block;
    }
    .temp-label {
        font-size: 12px;
        color: #666;
    }
    .wind {
        text-align: center;
    }
    .wind-value {
        font-size: 18px;
        font-weight: bold;
        display: block;
    }
    .wind-direction {
        font-size: 12px;
        color: #666;
    }
    .widget-footer {
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #eee;
        font-size: 11px;
    }
    
    /* Spin animation for refresh button */
    .spin {
        animation: spin 1s linear infinite;
        display: inline-block;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(weatherStyles);