/**
 * Maritime Weather Module for BergNavn Dashboard - FIXED VERSION
 * Real-time weather display with guaranteed data for dashboard.
 * ENHANCED: Works with weather_service.py structure and provides fallback.
 */

// Configuration
const WEATHER_API_URL = "/maritime/api/weather-dashboard";  // FIXED: Using new endpoint
const UPDATE_INTERVAL_MS = 30000;  // 30 seconds for real-time updates
const FALLBACK_WEATHER = {
    temperature_c: 8.5,
    temperature_display: "8.5°C",
    wind_speed_ms: 5.2,
    wind_display: "5.2 m/s",
    wind_direction: "NW",
    wind_dir_display: "NW",
    city: "Bergen",
    data_source: "fallback"
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
 */
async function fetchWeatherData() {
    let lastError = null;
    
    // Try primary endpoint first
    try {
        const response = await fetch(WEATHER_API_URL, {
            signal: AbortSignal.timeout(5000)  // 5 second timeout
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Weather API response:', data);
        return data;
    } catch (error) {
        lastError = error;
        console.warn('Primary weather endpoint failed, trying legacy endpoint...');
    }
    
    // Try legacy endpoint as fallback
    try {
        const response = await fetch("/maritime/api/weather", {
            signal: AbortSignal.timeout(3000)
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Legacy weather endpoint successful');
            return data;
        }
    } catch (error) {
        console.warn('Legacy endpoint also failed');
    }
    
    // All endpoints failed
    console.error('All weather endpoints failed:', lastError);
    return null;
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
 */
function updateWeatherDisplay(weatherData) {
    console.log('Updating weather display with:', weatherData);
    
    // Check for error or missing data
    if (!weatherData) {
        console.warn('No weather data received, using fallback');
        updateWeatherStats(FALLBACK_WEATHER);
        updateWeatherStatus('No data - Using fallback', 'warning');
        return;
    }
    
    // Handle different data structures
    let weather = weatherData;
    
    // If data has nested weather property (legacy format)
    if (weatherData.weather) {
        weather = weatherData.weather;
    }
    
    // If still no valid data, use fallback
    if (!weather || (!weather.temperature_c && !weather.temperature)) {
        console.warn('Invalid weather data format, using fallback');
        updateWeatherStats(FALLBACK_WEATHER);
        updateWeatherStatus('Invalid data - Using fallback', 'warning');
        return;
    }
    
    // Update dashboard stats
    updateWeatherStats(weather);
    
    // Update weather status badge
    updateWeatherStatus(weather.data_source || 'Unknown source', 
                       weather.data_source === 'met_norway_live' ? 'success' : 'warning');
    
    // Log success
    console.log(`✅ Weather updated: ${weather.city || 'Unknown'} - ${weather.temperature_c || weather.temperature}°C`);
}

/**
 * Updates dashboard statistics with weather data
 */
function updateWeatherStats(weather) {
    if (!weather) {
        // Set default values when no data
        document.getElementById('weather-temp').textContent = '--°C';
        document.getElementById('wind-speed').textContent = '-- m/s';
        document.getElementById('wind-direction').textContent = '--°';
        document.getElementById('weather-location').textContent = 'Bergen';
        return;
    }
    
    try {
        // Update temperature - handle both temperature_c and temperature fields
        const tempElement = document.getElementById('weather-temp');
        if (tempElement) {
            const temperature = weather.temperature_c || weather.temperature;
            if (temperature !== null && temperature !== undefined) {
                tempElement.textContent = `${Math.round(temperature)}°C`;
                tempElement.title = `${temperature.toFixed(1)}°C precise`;
            } else {
                tempElement.textContent = '--°C';
            }
        }
        
        // Update wind speed - handle both wind_speed_ms and wind_speed fields
        const windSpeedElement = document.getElementById('wind-speed');
        if (windSpeedElement) {
            const windSpeed = weather.wind_speed_ms || weather.wind_speed;
            if (windSpeed !== null && windSpeed !== undefined) {
                windSpeedElement.textContent = `${Math.round(windSpeed)} m/s`;
                windSpeedElement.title = `${windSpeed.toFixed(1)} m/s precise`;
            } else {
                windSpeedElement.textContent = '-- m/s';
            }
        }
        
        // Update wind direction
        const windDirElement = document.getElementById('wind-direction');
        if (windDirElement) {
            const windDir = weather.wind_direction || weather.wind_dir_display || 
                           (weather.wind_direction_deg ? degreesToCardinal(weather.wind_direction_deg) : null);
            
            if (windDir) {
                windDirElement.textContent = windDir;
                if (weather.wind_direction_deg) {
                    windDirElement.title = `${weather.wind_direction_deg}°`;
                }
            } else {
                windDirElement.textContent = '--°';
            }
        }
        
        // Update weather location
        const locationElement = document.getElementById('weather-location');
        if (locationElement) {
            locationElement.textContent = weather.city || weather.location || 'Bergen';
            if (weather.region) {
                locationElement.title = weather.region;
            }
        }
        
        // Update data source indicator (optional)
        const sourceElement = document.getElementById('weather-source');
        if (sourceElement) {
            const source = weather.data_source || 'Unknown';
            const sourceText = source.replace('_', ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
            sourceElement.textContent = sourceText;
            sourceElement.className = weather.data_source === 'met_norway_live' ? 'badge bg-success' : 'badge bg-warning';
        }
        
        // Update timestamp if available
        const timestampElement = document.getElementById('weather-timestamp');
        if (timestampElement && weather.timestamp) {
            timestampElement.textContent = formatTimestamp(weather.timestamp);
        }
        
    } catch (error) {
        console.error('Error updating weather stats:', error);
        // On error, set to fallback values
        document.getElementById('weather-temp').textContent = '--°C';
        document.getElementById('wind-speed').textContent = '-- m/s';
        document.getElementById('wind-direction').textContent = '--°';
    }
}

/**
 * Updates the weather status badge in the dashboard
 */
function updateWeatherStatus(source, status = 'success') {
    const weatherStatusElement = document.getElementById('weather-status');
    if (!weatherStatusElement) return;
    
    const statusMap = {
        'success': { text: 'Connected', class: 'text-success' },
        'warning': { text: 'Fallback', class: 'text-warning' },
        'error': { text: 'Offline', class: 'text-danger' }
    };
    
    const statusInfo = statusMap[status] || statusMap.warning;
    
    weatherStatusElement.textContent = source.includes('fallback') ? 'Fallback Data' : 'Connected';
    weatherStatusElement.className = source.includes('fallback') ? 'text-warning' : 'text-success';
    
    // Also update the badge in the status bar
    const statusBadge = document.getElementById('weather-status-badge');
    if (statusBadge) {
        const span = statusBadge.querySelector('span');
        if (span) {
            span.textContent = source.includes('fallback') ? 'Fallback' : 'Connected';
            span.className = source.includes('fallback') ? 'text-warning' : 'text-success';
        }
    }
}

/**
 * Creates a weather widget for additional display (optional)
 */
function createWeatherWidget(weather) {
    if (!weather) return '';
    
    const temperature = weather.temperature_c || weather.temperature;
    const windSpeed = weather.wind_speed_ms || weather.wind_speed;
    const windDir = weather.wind_direction || degreesToCardinal(weather.wind_direction_deg);
    const city = weather.city || weather.location || 'Bergen';
    const source = weather.data_source || 'unknown';
    
    return `
        <div class="weather-widget">
            <div class="widget-header">
                <h6><i class="bi bi-geo-alt"></i> ${city}</h6>
                <small class="text-muted">${formatTimestamp(weather.timestamp)}</small>
            </div>
            <div class="widget-body">
                <div class="temperature">
                    <span class="temp-value">${temperature ? Math.round(temperature) : '--'}°C</span>
                    <span class="temp-label">Temperature</span>
                </div>
                <div class="wind">
                    <i class="bi bi-wind"></i>
                    <span class="wind-value">${windSpeed ? Math.round(windSpeed) : '--'} m/s</span>
                    <span class="wind-direction">${windDir || '--'}</span>
                </div>
            </div>
            <div class="widget-footer">
                <small class="text-muted">
                    Source: ${source.replace('_', ' ')}
                </small>
            </div>
        </div>
    `;
}

/**
 * Main function to load and display weather
 */
async function loadWeather() {
    try {
        console.log('🌤 Fetching weather data...');
        const data = await fetchWeatherData();
        updateWeatherDisplay(data);
    } catch (error) {
        console.error("Weather load error:", error);
        updateWeatherStats(FALLBACK_WEATHER);
        updateWeatherStatus('API Error - Using fallback', 'error');
    }
}

/**
 * Initialize weather display and set up periodic updates
 */
function initializeWeather() {
    console.log('🌤 Initializing weather module...');
    
    // Create status badge if it doesn't exist
    if (!document.getElementById('weather-status-badge')) {
        const statusBar = document.querySelector('.alert-secondary');
        if (statusBar) {
            const badge = document.createElement('span');
            badge.id = 'weather-status-badge';
            badge.className = 'badge bg-light text-dark ms-2';
            badge.innerHTML = '<i class="bi bi-cloud-sun me-1"></i>Weather: <span id="weather-status">Loading...</span>';
            statusBar.querySelector('span').appendChild(badge);
        }
    }
    
    // Load immediately
    loadWeather();
    
    // Set up periodic refresh
    setInterval(loadWeather, UPDATE_INTERVAL_MS);
    
    // Add CSS for weather widget
    const style = document.createElement('style');
    style.textContent = `
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
    `;
    document.head.appendChild(style);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeWeather);

// Export for global use
window.weatherManager = {
    loadWeather: loadWeather,
    updateWeather: loadWeather,
    toggle: function() {
        console.log('Weather display toggled');
        // Implementation for showing/hiding weather elements
    }
};