/**
 * Maritime Weather Module for BergNavn Dashboard
 * Fetches and displays weather data from the maritime API.
 * FIXED: Adjusted to work with current dashboard structure
 */

// Configuration
const WEATHER_API_URL = "/maritime/api/weather";
const UPDATE_INTERVAL_MS = 60000; // 60 seconds

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
    // Check for error or missing data
    if (!weatherData || weatherData.status !== "success" || !weatherData.weather) {
        console.warn('No valid weather data received');
        updateWeatherStats(null);
        return;
    }
    
    const w = weatherData.weather;
    
    // Format conditions text
    const conditionsText = w.conditions_text || getConditionText(w.conditions);
    const windDirection = degreesToCardinal(w.wind_direction);
    
    // Update dashboard stats
    updateWeatherStats(w);
    
    // Also update the detailed weather box if it exists
    const weatherBox = document.getElementById('weather-box');
    if (weatherBox) {
        const locationText = w.location ? `${w.location}, ${w.country || 'Norway'}` : 'Bergen, Norway';
        
        weatherBox.innerHTML = `
            <div class="weather-report">
                <div class="weather-location mb-2">
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
    }
}

/**
 * Updates dashboard statistics with weather data
 */
function updateWeatherStats(weatherData) {
    if (!weatherData) {
        // Set default values when no data
        document.getElementById('weather-temp').textContent = '--°C';
        document.getElementById('wind-speed').textContent = '-- m/s';
        return;
    }
    
    // Update temperature
    const tempElement = document.getElementById('weather-temp');
    if (tempElement && weatherData.temperature !== null) {
        tempElement.textContent = `${Math.round(weatherData.temperature)}°C`;
    }
    
    // Update wind speed
    const windElement = document.getElementById('wind-speed');
    if (windElement && weatherData.wind_speed !== null) {
        windElement.textContent = `${Math.round(weatherData.wind_speed)} m/s`;
    }
    
    // Update weather condition
    const conditionElement = document.getElementById('weather-condition');
    if (conditionElement) {
        const conditionsText = weatherData.conditions_text || getConditionText(weatherData.conditions);
        conditionElement.textContent = conditionsText;
    }
    
    // Update weather location
    const locationElement = document.getElementById('weather-location');
    if (locationElement && weatherData.location) {
        locationElement.textContent = weatherData.location;
    }
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
        updateWeatherStats(null);
    }
}

// Initialize weather display
document.addEventListener('DOMContentLoaded', () => {
    // Load immediately
    loadWeather();
    
    // Set up periodic refresh
    setInterval(loadWeather, UPDATE_INTERVAL_MS);
});

// Export for global use
window.loadWeather = loadWeather;