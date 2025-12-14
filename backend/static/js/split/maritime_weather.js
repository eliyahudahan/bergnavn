// backend/static/js/split/maritime_weather.js
/**
 * Fetches and displays weather data from the maritime API.
 * Updates every 60 seconds.
 */

// Configuration
const WEATHER_API_URL = "/maritime/api/weather";  // ✅ Corrected endpoint
const UPDATE_INTERVAL_MS = 60000; // 60 seconds
const WEATHER_BOX_ID = "weather-box";

/**
 * Converts wind direction from degrees to cardinal direction
 */
function degreesToCardinal(degrees) {
    if (degrees === null || degrees === undefined) return 'N/A';
    
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
        'fair': 'Fair',
        'partlycloudy': 'Partly Cloudy',
        'cloudy': 'Cloudy',
        'lightrain': 'Light Rain',
        'rain': 'Rain',
        'heavyrain': 'Heavy Rain',
        'lightsnow': 'Light Snow',
        'snow': 'Snow',
        'fog': 'Fog',
        'lightrainshowers': 'Light Rain Showers'
    };
    
    return conditionMap[symbolCode] || symbolCode;
}

/**
 * Fetches weather data from the backend API
 */
async function fetchWeatherData() {
    try {
        const response = await fetch(WEATHER_API_URL);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error("Weather fetch error:", error);
        return null;
    }
}

/**
 * Formats a timestamp into a readable time
 */
function formatTimestamp(isoString) {
    if (!isoString) return "Just now";
    
    try {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } catch (e) {
        return isoString.split('T')[1]?.substring(0, 5) || isoString;
    }
}

/**
 * Updates the weather display with new data
 */
function updateWeatherDisplay(weatherData) {
    const weatherBox = document.getElementById(WEATHER_BOX_ID);
    
    if (!weatherBox) {
        console.error("Weather box element not found");
        return;
    }
    
    // Check for error or missing data
    if (!weatherData || weatherData.status !== "success" || !weatherData.weather) {
        weatherBox.innerHTML = `
            <div class="weather-alert">
                <h4>🌤 Weather</h4>
                <p><em>Weather data is currently unavailable.</em></p>
                <p><small>Checking again shortly...</small></p>
            </div>
        `;
        return;
    }
    
    const w = weatherData.weather;
    
    // Format conditions text - use conditions_text if available, otherwise convert symbol
    const conditionsText = w.conditions_text || getConditionText(w.conditions);
    const windDirection = degreesToCardinal(w.wind_direction);
    const locationText = w.location ? `${w.location}, ${w.country || 'Norway'}` : 'Bergen, Norway';
    
    // Build the weather display HTML
    weatherBox.innerHTML = `
        <div class="weather-report">
            <div class="weather-location mb-2">
                <span class="city-indicator bergen-indicator"></span>
                <strong>${locationText}</strong> - Current Conditions
            </div>
            <h4>🌤 ${conditionsText}</h4>
            
            <div class="weather-metrics">
                ${w.temperature !== null ? `
                <div class="metric">
                    <span class="label">Temperature:</span>
                    <span class="value">${w.temperature.toFixed(1)}°C</span>
                </div>
                ` : ''}
                
                ${w.wind_speed !== null ? `
                <div class="metric">
                    <span class="label">Wind:</span>
                    <span class="value">${w.wind_speed.toFixed(1)} m/s ${windDirection}</span>
                </div>
                ` : ''}
                
                ${w.pressure !== null ? `
                <div class="metric">
                    <span class="label">Pressure:</span>
                    <span class="value">${w.pressure} hPa</span>
                </div>
                ` : ''}
                
                ${w.humidity !== null ? `
                <div class="metric">
                    <span class="label">Humidity:</span>
                    <span class="value">${w.humidity}%</span>
                </div>
                ` : ''}
            </div>
            
            <div class="weather-footer">
                <small>
                    <i class="bi bi-clock"></i> Updated: ${formatTimestamp(w.timestamp)} 
                    ${w.source ? `<br><i class="bi bi-database"></i> ${w.source}` : ''}
                </small>
            </div>
        </div>
    `;
    
    // Update dashboard stats
    updateDashboardStats(w);
}

/**
 * Updates dashboard statistics with weather data
 */
function updateDashboardStats(weatherData) {
    // Update temperature card
    const tempElement = document.getElementById('current-temp');
    if (tempElement && weatherData.temperature !== null) {
        tempElement.textContent = `${weatherData.temperature.toFixed(1)}°C`;
    }
    
    // Update wind speed card
    const windElement = document.getElementById('current-wind');
    if (windElement && weatherData.wind_speed !== null) {
        windElement.textContent = `${weatherData.wind_speed.toFixed(1)} m/s`;
    }
    
    // Update location texts
    const tempLocation = document.getElementById('temp-location');
    const windLocation = document.getElementById('wind-location');
    if (tempLocation && weatherData.location) {
        tempLocation.textContent = `Current • ${weatherData.location} Area`;
    }
    if (windLocation && weatherData.location) {
        windLocation.textContent = `Average • ${weatherData.location} Coastal`;
    }
    
    // Update weather timestamp
    const weatherTimestamp = document.getElementById('weather-timestamp');
    if (weatherTimestamp) {
        weatherTimestamp.textContent = formatTimestamp(weatherData.timestamp);
    }
    
    // Update weather source
    const weatherSource = document.getElementById('weather-source');
    if (weatherSource && weatherData.source) {
        weatherSource.textContent = weatherData.source;
    }
}

/**
 * Main function to load and display weather
 */
async function loadWeather() {
    try {
        console.log('🌤 Fetching weather data from:', WEATHER_API_URL);
        const data = await fetchWeatherData();
        updateWeatherDisplay(data);
    } catch (error) {
        console.error("Weather load error:", error);
        const box = document.getElementById(WEATHER_BOX_ID);
        if (box) {
            box.innerHTML = `
                <div class="weather-error">
                    <h4>⚠️ Weather</h4>
                    <p>Error loading weather data.</p>
                    <p><small>Check console for details</small></p>
                </div>
            `;
        }
    }
}

// Initialize weather display
document.addEventListener('DOMContentLoaded', () => {
    // Load immediately
    loadWeather();
    
    // Set up periodic refresh
    setInterval(loadWeather, UPDATE_INTERVAL_MS);
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { loadWeather, fetchWeatherData };
}