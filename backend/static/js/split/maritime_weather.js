/* backend/static/js/split/maritime_weather.js */
/**
 * Maritime Weather Module for BergNavn Dashboard - UPDATED VERSION
 * Uses the new Weather Integration Service API instead of old endpoints
 * FIXED: No longer conflicts with new weather system
 * UPDATED: Uses /api/simple-weather endpoint for real MET Norway data
 */

// Configuration - Using NEW weather API endpoints
const WEATHER_API_ENDPOINTS = [
    "/api/simple-weather?lat=60.39&lon=5.32",    // Primary: New integration service
    "/api/weather-pro?lat=60.39&lon=5.32",       // Secondary: Blueprint endpoint
    "/maritime/api/weather-dashboard"            // Fallback: Legacy endpoint
];

// Fallback weather data - always available for emergencies
const FALLBACK_WEATHER = {
    temperature_c: 8.5,
    temperature_display: "8.5°C",
    wind_speed_ms: 5.2,
    wind_display: "5.2 m/s",
    wind_direction: "NW",
    wind_dir_display: "NW",
    city: "Bergen",
    condition: "Fallback Data",
    data_source: "fallback_empirical",
    display: {
        temperature: "8°C",
        wind: "5 m/s",
        location: "Bergen",
        condition: "Fallback Data",
        source_badge: "📊 Fallback",
        icon: "cloud"
    }
};

/**
 * Converts wind direction from degrees to cardinal direction
 */
function degreesToCardinal(input) {
    if (!input && input !== 0) return 'N/A';
    
    // If already a string direction
    if (typeof input === 'string') {
        const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                          'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
        if (directions.includes(input.toUpperCase())) {
            return input.toUpperCase();
        }
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
 * Gets weather icon class based on condition or icon name
 */
function getWeatherIconClass(iconName) {
    const iconMap = {
        'sun': 'bi bi-sun-fill weather-icon weather-icon-sun',
        'cloud': 'bi bi-cloud-fill weather-icon weather-icon-cloud',
        'cloud-sun': 'bi bi-cloud-sun-fill weather-icon weather-icon-cloud',
        'cloud-rain': 'bi bi-cloud-rain-fill weather-icon weather-icon-rain',
        'cloud-snow': 'bi bi-cloud-snow-fill weather-icon weather-icon-snow',
        'snow': 'bi bi-snow weather-icon weather-icon-snow',
        'cloud-fog': 'bi bi-cloud-fog-fill weather-icon weather-icon-fog',
        'cloud-lightning': 'bi bi-cloud-lightning-fill weather-icon weather-icon-cloud'
    };
    
    return iconMap[iconName] || 'bi bi-cloud-fill weather-icon weather-icon-cloud';
}

/**
 * Gets source badge based on data source
 */
function getSourceBadge(source) {
    const badges = {
        'met_norway': '🇳🇴 MET Norway',
        'met_norway_live': '🇳🇴 MET Norway',
        'barentswatch': '🌊 BarentsWatch',
        'openweather': '🌍 OpenWeatherMap',
        'empirical': '📊 Empirical',
        'fallback_empirical': '📊 Empirical',
        'emergency': '🚨 Emergency',
        'fallback': '📊 Fallback'
    };
    return badges.get(source, '📊 Weather');
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
        
        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        
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
 * Fetches weather data using the NEW API endpoints
 * Tries endpoints in order until one works
 */
async function fetchWeatherData() {
    console.log('🌤️ Fetching weather data from new API system...');
    
    // Try each endpoint in order
    for (const endpoint of WEATHER_API_ENDPOINTS) {
        try {
            console.log(`🔍 Trying endpoint: ${endpoint}`);
            
            const response = await fetch(endpoint, {
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
            console.log(`✅ Got response from ${endpoint}`);
            
            // Process the response based on endpoint structure
            if (endpoint.includes('/api/simple-weather') || endpoint.includes('/api/weather-pro')) {
                // New API format: {status: "success", data: {...}}
                if (data.status === 'success' && data.data) {
                    console.log(`✅ Using weather from: ${data.data.data_source || 'unknown'}`);
                    return data.data;
                }
            } else if (endpoint.includes('/maritime/api/weather-dashboard')) {
                // Legacy format: direct weather object
                return data;
            }
            
        } catch (error) {
            console.warn(`⚠️ Endpoint ${endpoint} failed:`, error.message);
            continue; // Try next endpoint
        }
    }
    
    // All endpoints failed - use empirical fallback
    console.log('⚠️ All weather endpoints failed, using empirical fallback data');
    return FALLBACK_WEATHER;
}

/**
 * Updates the dashboard weather display with new data
 * FIXED: Properly handles both new and old data formats
 */
function updateWeatherDisplay(weatherData) {
    console.log('📊 Updating weather display...');
    
    let weather = weatherData || FALLBACK_WEATHER;
    
    // Ensure display object exists (for new API format)
    if (weather && !weather.display) {
        weather.display = {
            temperature: `${Math.round(weather.temperature_c || 0)}°C`,
            wind: `${Math.round(weather.wind_speed_ms || 0)} m/s`,
            location: weather.location || weather.city || 'Bergen',
            condition: weather.condition || 'Unknown',
            source_badge: getSourceBadge(weather.data_source),
            icon: weather.icon || 'cloud'
        };
    }
    
    // Update dashboard stats
    updateWeatherStats(weather);
    
    // Update status badge
    updateWeatherStatus(weather.data_source);
    
    console.log(`✅ Weather updated: ${weather.display?.temperature}, ${weather.display?.wind}`);
}

/**
 * Updates dashboard statistics with weather data
 * UPDATED: Uses display object from new API
 */
function updateWeatherStats(weather) {
    if (!weather) {
        updateWithFallback();
        return;
    }
    
    try {
        // Update temperature
        const tempElement = document.getElementById('weather-temp');
        if (tempElement) {
            if (weather.display && weather.display.temperature) {
                tempElement.textContent = weather.display.temperature;
                tempElement.title = `${weather.temperature_c?.toFixed(1) || '8.5'}°C precise`;
            } else {
                tempElement.textContent = `${Math.round(weather.temperature_c || 8.5)}°C`;
            }
        }
        
        // Update wind speed
        const windElement = document.getElementById('weather-wind');
        if (windElement) {
            if (weather.display && weather.display.wind) {
                windElement.textContent = weather.display.wind;
                windElement.title = `${weather.wind_speed_ms?.toFixed(1) || '5.2'} m/s precise`;
            } else {
                windElement.textContent = `${Math.round(weather.wind_speed_ms || 5.2)} m/s`;
            }
        }
        
        // Update location
        const locationElement = document.getElementById('weather-location');
        if (locationElement) {
            if (weather.display && weather.display.location) {
                locationElement.textContent = weather.display.location;
            } else {
                locationElement.textContent = weather.location || weather.city || 'Bergen';
            }
        }
        
        // Update condition
        const conditionElement = document.getElementById('weather-condition');
        if (conditionElement) {
            if (weather.display && weather.display.condition) {
                conditionElement.textContent = weather.display.condition;
            } else if (weather.condition) {
                conditionElement.textContent = weather.condition;
            }
        }
        
        // Update timestamp
        const updatedElement = document.getElementById('weather-updated');
        if (updatedElement) {
            updatedElement.textContent = `Updated: ${formatTimestamp(weather.timestamp)}`;
        }
        
        // Update weather icon
        const weatherIcon = document.getElementById('weather-main-icon');
        if (weatherIcon) {
            if (weather.display && weather.display.icon) {
                weatherIcon.className = getWeatherIconClass(weather.display.icon);
            } else {
                weatherIcon.className = 'bi bi-cloud-fill weather-icon weather-icon-cloud';
            }
        }
        
        // Update source indicator
        const sourceIndicator = document.getElementById('weather-source-indicator');
        if (sourceIndicator) {
            if (weather.display && weather.display.source_badge) {
                sourceIndicator.textContent = weather.display.source_badge;
            } else {
                sourceIndicator.textContent = getSourceBadge(weather.data_source);
            }
            
            // Update badge class
            sourceIndicator.className = 'weather-source-badge';
            const source = weather.data_source || 'empirical';
            if (source.includes('met_norway')) {
                sourceIndicator.classList.add('weather-source-met_norway');
            } else if (source.includes('empirical') || source.includes('fallback')) {
                sourceIndicator.classList.add('weather-source-empirical');
            }
        }
        
    } catch (error) {
        console.error('Error updating weather stats:', error);
        updateWithFallback();
    }
}

/**
 * Updates with fallback data
 */
function updateWithFallback() {
    console.log('⚠️ Using fallback weather data');
    
    const tempElement = document.getElementById('weather-temp');
    const windElement = document.getElementById('weather-wind');
    const locationElement = document.getElementById('weather-location');
    const conditionElement = document.getElementById('weather-condition');
    const updatedElement = document.getElementById('weather-updated');
    const weatherIcon = document.getElementById('weather-main-icon');
    const sourceIndicator = document.getElementById('weather-source-indicator');
    
    if (tempElement) tempElement.textContent = '8°C';
    if (windElement) windElement.textContent = '5 m/s';
    if (locationElement) locationElement.textContent = 'Bergen';
    if (conditionElement) conditionElement.textContent = 'Fallback Data';
    if (updatedElement) updatedElement.textContent = 'Updated: Fallback';
    if (weatherIcon) weatherIcon.className = 'bi bi-cloud-fill weather-icon weather-icon-cloud';
    if (sourceIndicator) {
        sourceIndicator.textContent = '📊 Fallback';
        sourceIndicator.className = 'weather-source-badge weather-source-empirical';
    }
}

/**
 * Updates the weather status badge in the dashboard header
 */
function updateWeatherStatus(source) {
    const weatherStatusBadge = document.getElementById('weather-status-badge');
    const weatherStatusText = document.getElementById('weather-status-text');
    
    if (!weatherStatusBadge || !weatherStatusText) return;
    
    if (source === 'met_norway' || source === 'met_norway_live') {
        weatherStatusBadge.className = 'badge bg-success me-2';
        weatherStatusText.textContent = 'Live MET Norway';
    } else if (source === 'empirical' || source === 'fallback_empirical') {
        weatherStatusBadge.className = 'badge bg-warning me-2';
        weatherStatusText.textContent = 'Empirical Data';
    } else if (source === 'emergency_fallback' || source === 'emergency') {
        weatherStatusBadge.className = 'badge bg-danger me-2';
        weatherStatusText.textContent = 'Emergency Mode';
    } else {
        weatherStatusBadge.className = 'badge bg-info me-2';
        weatherStatusText.textContent = 'Weather Data';
    }
}

/**
 * Main function to load and display weather
 * UPDATED: Uses new API system
 */
async function loadWeather() {
    try {
        console.log('🌤️ Loading weather from new API system...');
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
        const originalHtml = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Refreshing...';
        refreshBtn.disabled = true;
        
        const data = await loadWeather();
        
        setTimeout(() => {
            refreshBtn.innerHTML = originalHtml;
            refreshBtn.disabled = false;
        }, 1000);
        
        return data;
    }
    
    return await loadWeather();
}

/**
 * Initialize weather display - SIMPLIFIED VERSION
 * Only loads once and doesn't interfere with other systems
 */
function initializeWeather() {
    console.log('🌤️ Initializing weather module (simplified, no auto-refresh)');
    
    // Load initial weather data after a short delay
    setTimeout(() => {
        loadWeather();
    }, 1500); // Give other systems time to initialize
    
    console.log('✅ Weather module initialized');
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWeather);
} else {
    initializeWeather();
}

// Export for global use - SIMPLIFIED to avoid conflicts
window.maritimeWeather = {
    loadWeather: loadWeather,
    refreshWeather: refreshWeather,
    getFallbackData: () => FALLBACK_WEATHER
};

// Add CSS for weather display if not already present
if (!document.getElementById('weather-module-styles')) {
    const weatherStyles = document.createElement('style');
    weatherStyles.id = 'weather-module-styles';
    weatherStyles.textContent = `
        /* Weather icon styling */
        .weather-icon {
            font-size: 1.2rem;
            margin-right: 8px;
            vertical-align: middle;
        }
        
        .weather-icon-sun {
            color: #ffc107;
        }
        
        .weather-icon-cloud {
            color: #6c757d;
        }
        
        .weather-icon-rain {
            color: #17a2b8;
        }
        
        .weather-icon-snow {
            color: #6f42c1;
        }
        
        .weather-icon-fog {
            color: #adb5bd;
        }
        
        /* Weather source badge updates */
        .weather-source-met_norway {
            background-color: #28a745;
            color: white;
        }
        
        .weather-source-barentswatch {
            background-color: #17a2b8;
            color: white;
        }
        
        .weather-source-openweather {
            background-color: #fd7e14;
            color: white;
        }
        
        .weather-source-empirical {
            background-color: #ffc107;
            color: #212529;
        }
        
        .weather-source-emergency {
            background-color: #dc3545;
            color: white;
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
}