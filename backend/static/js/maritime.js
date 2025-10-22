// backend/static/js/maritime.js - BergNavn Maritime Real-time Dashboard
// Enhanced with MET Norway integration, analytics, and interactive features

console.log('🚢 BergNavn Maritime Dashboard JavaScript loaded');

class MaritimeWeatherService {
    constructor() {
        this.USER_AGENT = 'BergNavnMaritime/3.0 (framgangsrik747@gmail.com)';
        this.CACHE_DURATION = 10 * 60 * 1000; // 10 minutes cache
        this.cache = new Map();
        this.isOnline = true;
        this.currentSource = 'Backend API';
    }

    /**
     * Fetch weather data with multiple fallback sources
     * Primary: MET Norway endpoint → Direct MET Norway → OpenWeather → Mock data
     * @param {number} latitude - Geographic latitude
     * @param {number} longitude - Geographic longitude  
     * @param {string} locationName - Human-readable location name
     * @returns {Promise<Object>} Weather data object
     */
    async getMaritimeWeather(latitude, longitude, locationName) {
        const cacheKey = `${latitude},${longitude}`;
        
        // Check cache first for performance optimization
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.CACHE_DURATION) {
                console.log('📦 Using cached weather data');
                return cached.data;
            }
        }

        try {
            // PRIMARY: New MET Norway endpoint
            let weatherData = await this.fetchFromMETNorwayEndpoint(latitude, longitude, locationName);
            this.currentSource = 'MET Norway';
            
            // FALLBACK 1: Direct MET Norway API
            if (!weatherData || weatherData.status === 'error') {
                weatherData = await this.fetchDirectMETNorway(latitude, longitude);
                this.currentSource = 'MET Norway Direct';
            }
            
            // FALLBACK 2: Legacy OpenWeather
            if (!weatherData) {
                weatherData = await this.fetchLegacyOpenWeather(latitude, longitude, locationName);
                this.currentSource = 'OpenWeather (Legacy)';
            }
            
            const enrichedData = {
                ...weatherData,
                location: locationName,
                timestamp: new Date().toISOString(),
                source: this.currentSource
            };
            
            // Update cache with fresh data
            this.cache.set(cacheKey, {
                data: enrichedData,
                timestamp: Date.now()
            });
            
            this.isOnline = true;
            return enrichedData;
            
        } catch (error) {
            console.warn(`All weather APIs failed for ${locationName}:`, error);
            this.isOnline = false;
            this.currentSource = 'Mock Data';
            return this.getMockWeatherData(latitude, longitude, locationName);
        }
    }

    /**
     * Fetch from our enhanced MET Norway endpoint (primary data source)
     * @param {number} lat - Latitude coordinate
     * @param {number} lon - Longitude coordinate
     * @param {string} locationName - Location name for context
     * @returns {Promise<Object>} Parsed weather data
     */
    async fetchFromMETNorwayEndpoint(lat, lon, locationName) {
        const url = `/weather/api/maritime-weather?lat=${lat}&lon=${lon}&location=${encodeURIComponent(locationName)}`;
        
        try {
            console.log('🌤️ Fetching from MET Norway endpoint...');
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });

            if (!response.ok) {
                throw new Error(`MET Norway endpoint error: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ MET Norway endpoint response:', data);
            
            if (data.status === 'success') {
                return this.parseMETNorwayEndpointResponse(data.data);
            } else if (data.status === 'fallback') {
                console.log('🔄 MET Norway endpoint using fallback data');
                return null; // Trigger next fallback
            } else {
                throw new Error(data.message || 'MET Norway endpoint returned error');
            }
        } catch (error) {
            console.warn('MET Norway endpoint failed:', error);
            return null;
        }
    }

    /**
     * Parse our enhanced MET Norway endpoint response
     * @param {Object} weatherData - Weather data from endpoint
     * @returns {Object} Structured weather information
     */
    parseMETNorwayEndpointResponse(weatherData) {
        return {
            temperature: weatherData.temperature,
            windSpeed: weatherData.wind_speed,
            windDirection: weatherData.wind_direction || 0,
            windGust: weatherData.wind_gust || weatherData.wind_speed * 1.3,
            pressure: weatherData.pressure,
            humidity: weatherData.humidity,
            cloudCover: 50, // Default value
            condition: { 
                text: weatherData.condition, 
                icon: weatherData.icon || '🌊'
            },
            dataQuality: weatherData.data_quality || 'high'
        };
    }

    /**
     * Direct MET Norway API call (fallback source)
     * @param {number} lat - Latitude coordinate
     * @param {number} lon - Longitude coordinate
     * @returns {Promise<Object>} Parsed weather data
     */
    async fetchDirectMETNorway(lat, lon) {
        const url = `https://api.met.no/weatherapi/locationforecast/2.0/complete?lat=${lat}&lon=${lon}`;
        
        try {
            console.log('🔄 Trying direct MET Norway API...');
            const response = await fetch(url, {
                headers: {
                    'User-Agent': this.USER_AGENT,
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Direct MET Norway API error: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ Direct MET Norway API success');
            return this.parseMETNorwayResponse(data);
        } catch (error) {
            console.warn('Direct MET Norway API failed:', error);
            return null;
        }
    }

    /**
     * Legacy OpenWeather fallback
     * @param {number} lat - Latitude coordinate
     * @param {number} lon - Longitude coordinate
     * @param {string} locationName - Location name for context
     * @returns {Promise<Object>} Parsed weather data
     */
    async fetchLegacyOpenWeather(lat, lon, locationName) {
        const url = `/maritime/api/weather?lat=${lat}&lon=${lon}&location=${encodeURIComponent(locationName)}`;
        
        try {
            console.log('🔄 Trying legacy OpenWeather endpoint...');
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Legacy API error: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.status === 'success') {
                console.log('✅ Legacy OpenWeather endpoint success');
                return this.parseBackendWeatherResponse(data.data);
            } else {
                throw new Error(data.message || 'Legacy API returned error');
            }
        } catch (error) {
            console.warn('Legacy OpenWeather endpoint failed:', error);
            return null;
        }
    }

    /**
     * Parse direct MET Norway API response
     * @param {Object} apiData - Raw API response from MET Norway
     * @returns {Object} Structured weather information
     */
    parseMETNorwayResponse(apiData) {
        try {
            const current = apiData.properties.timeseries[0];
            const details = current.data.instant.details;
            
            return {
                temperature: details.air_temperature,
                windSpeed: details.wind_speed,
                windDirection: details.wind_from_direction,
                windGust: details.wind_speed_of_gust,
                pressure: details.air_pressure_at_sea_level,
                humidity: details.relative_humidity,
                cloudCover: details.cloud_area_fraction,
                condition: this.mapMETNorwayCondition(current.data.next_1_hours?.summary.symbol_code)
            };
        } catch (error) {
            console.error('Error parsing MET Norway response:', error);
            throw error;
        }
    }

    /**
     * Parse legacy OpenWeather response
     * @param {Object} weatherData - Weather data from backend API
     * @returns {Object} Structured weather information
     */
    parseBackendWeatherResponse(weatherData) {
        return {
            temperature: weatherData.temperature,
            windSpeed: weatherData.wind_speed,
            windDirection: weatherData.wind_direction || 0,
            windGust: weatherData.wind_gust || weatherData.wind_speed * 1.3,
            pressure: weatherData.pressure,
            humidity: weatherData.humidity,
            cloudCover: 50,
            condition: { 
                text: weatherData.condition, 
                icon: weatherData.icon 
            }
        };
    }

    /**
     * Map MET Norway condition codes to readable format with icons
     * @param {string} conditionCode - MET Norway condition code
     * @returns {Object} Mapped condition with text and icon
     */
    mapMETNorwayCondition(conditionCode) {
        const conditions = {
            'clearsky': { text: 'Clear Sky', icon: '☀️' },
            'fair': { text: 'Fair', icon: '🌤️' },
            'partlycloudy': { text: 'Partly Cloudy', icon: '⛅' },
            'cloudy': { text: 'Cloudy', icon: '☁️' },
            'lightrain': { text: 'Light Rain', icon: '🌦️' },
            'rain': { text: 'Rain', icon: '🌧️' },
            'heavyrain': { text: 'Heavy Rain', icon: '⛈️' },
            'lightsnow': { text: 'Light Snow', icon: '🌨️' },
            'snow': { text: 'Snow', icon: '❄️' },
            'fog': { text: 'Fog', icon: '🌫️' }
        };
        
        return conditions[conditionCode] || { text: 'Maritime Conditions', icon: '🌊' };
    }

    /**
     * Generate mock data for offline fallback mode
     * @param {number} lat - Latitude for realistic data generation
     * @param {number} lon - Longitude for realistic data generation  
     * @param {string} locationName - Location name for context
     * @returns {Object} Mock weather data
     */
    getMockWeatherData(lat, lon, locationName) {
        const baseTemp = 8 + (lat - 58) * 0.5; // Temperature varies with latitude
        const baseWind = 3 + Math.random() * 12; // Realistic wind speeds
        
        return {
            temperature: Math.round((baseTemp + (Math.random() * 6 - 3)) * 10) / 10,
            windSpeed: Math.round(baseWind * 10) / 10,
            windDirection: Math.floor(Math.random() * 360),
            windGust: Math.round((baseWind * 1.3) * 10) / 10,
            pressure: 1000 + Math.floor(Math.random() * 30),
            humidity: 65 + Math.floor(Math.random() * 25),
            cloudCover: Math.floor(Math.random() * 100),
            condition: { text: 'Fair', icon: '🌤️' },
            location: locationName,
            timestamp: new Date().toISOString(),
            source: 'Mock Data (Offline)'
        };
    }
}

/**
 * Maritime Data Science Integration
 * Handles AIS data, analytics, and optimization insights
 */
class MaritimeDataScience {
    constructor() {
        this.analyticsData = null;
        this.optimizationData = null;
    }

    /**
     * Load AIS data and analytics from backend APIs
     * Includes fleet performance and optimization recommendations
     */
    async loadAISData() {
        try {
            console.log('🚢 Loading AIS data and analytics...');
            
            // Load analytics data
            await this.loadAnalytics();
            
            // Load optimization recommendations
            await this.loadOptimization();
            
            // Update dashboard with analytics insights
            this.updateDashboardMetrics();
            
        } catch (error) {
            console.warn('AIS data loading failed:', error);
            this.displayMockAnalytics();
        }
    }

    /**
     * Load fleet analytics from ML API
     */
    async loadAnalytics() {
        try {
            const response = await fetch('/api/ml/maritime-analytics');
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    this.analyticsData = data;
                    console.log('📊 Analytics data loaded:', data);
                }
            }
        } catch (error) {
            console.warn('Analytics loading failed:', error);
        }
    }

    /**
     * Load fuel optimization recommendations
     */
    async loadOptimization() {
        try {
            const response = await fetch('/api/ml/fuel-optimization');
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    this.optimizationData = data;
                    console.log('⚡ Optimization data loaded:', data);
                }
            }
        } catch (error) {
            console.warn('Optimization loading failed:', error);
        }
    }

    /**
     * Update dashboard with analytics insights
     */
    updateDashboardMetrics() {
        // Update fuel savings display if analytics data is available
        if (this.analyticsData && this.analyticsData.fleet_metrics) {
            const fuelSaving = this.analyticsData.fleet_metrics.potential_fuel_savings_percent;
            if (fuelSaving) {
                const fuelElements = document.querySelectorAll('[id*="fuel"], [class*="fuel"]');
                fuelElements.forEach(element => {
                    if (element.textContent.includes('15%+') || element.textContent.includes('15%')) {
                        element.textContent = element.textContent.replace('15%+', `${fuelSaving}%+`);
                    }
                });
            }
        }
    }

    /**
     * Display mock analytics when real data is unavailable
     */
    displayMockAnalytics() {
        console.log('🔧 Using mock analytics data');
        this.analyticsData = {
            fleet_metrics: {
                potential_fuel_savings_percent: 15,
                total_ships: 12,
                average_fuel_efficiency: 78
            }
        };
        this.updateDashboardMetrics();
    }
}

/**
 * Maritime Route Manager
 * Handles route data, ETA calculations, and geographic operations
 */
class MaritimeRouteManager {
    constructor() {
        this.routePoints = [
            { name: 'Kristiansand', lat: 58.1467, lon: 8.0980, type: 'port' },
            { name: 'Oksøy Lighthouse', lat: 58.0667, lon: 8.0500, type: 'navigation' },
            { name: 'Oslo Fjord', lat: 59.9115, lon: 10.7570, type: 'port' }
        ];
    }

    /**
     * Get important weather points along the maritime route
     * @returns {Array} Filtered route points for weather monitoring
     */
    getWeatherPoints() {
        return this.routePoints.filter(point => 
            point.type === 'port' || point.name.includes('Lighthouse')
        );
    }

    /**
     * Get all route points for map visualization
     * @returns {Array} All route points with coordinates
     */
    getAllRoutePoints() {
        return this.routePoints;
    }
}

/**
 * Main Maritime Dashboard Controller
 * Orchestrates weather data, route management, analytics, and UI updates
 */
class MaritimeDashboard {
    constructor() {
        this.weatherService = new MaritimeWeatherService();
        this.dataScience = new MaritimeDataScience();
        this.routeManager = new MaritimeRouteManager();
        this.updateInterval = null;
    }

    /**
     * Initialize the maritime dashboard components
     * Sets up data loading, event listeners, and auto-refresh
     */
    async initialize() {
        console.log('🚢 BergNavn Maritime Dashboard Initializing...');
        
        try {
            // Load initial data
            await this.loadWeatherData();
            await this.dataScience.loadAISData();
            
            // Initialize map visualization
            this.initializeMap();
            
            // Set up auto-refresh and event handlers
            this.setupAutoRefresh();
            this.setupEventListeners();
            
            // Update status display
            this.updateStatusDisplay();
            
            console.log('✅ Maritime Dashboard initialized successfully');
            
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
            this.displayError('Dashboard initialization failed. Some features may be unavailable.');
        }
    }

    /**
     * Load and display weather data for all route points
     */
    async loadWeatherData() {
        const weatherPoints = this.routeManager.getWeatherPoints();
        const weatherContainer = document.getElementById('weather-data');
        
        if (!weatherContainer) {
            console.error('❌ Weather container element not found');
            return;
        }

        // Show loading state during data fetch
        weatherContainer.innerHTML = `
            <div class="col-12 text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading maritime weather data...</span>
                </div>
                <p class="mt-2">Loading real-time MET Norway data...</p>
                <small class="text-muted">Connecting to official Norwegian meteorological service</small>
            </div>
        `;

        try {
            // Fetch weather data for all route points concurrently
            const weatherPromises = weatherPoints.map(point =>
                this.weatherService.getMaritimeWeather(point.lat, point.lon, point.name)
            );
            
            const weatherResults = await Promise.all(weatherPromises);
            this.displayWeatherData(weatherResults);
            await this.updateRouteETA();
            
        } catch (error) {
            console.error('❌ Failed to load weather data:', error);
            this.displayError('Failed to load weather data from MET Norway. Using fallback data.');
        }
    }

    /**
     * Display weather data in the dashboard UI
     * @param {Array} weatherData - Array of weather data objects
     */
    displayWeatherData(weatherData) {
        const weatherContainer = document.getElementById('weather-data');
        
        const weatherHTML = weatherData.map(weather => `
            <div class="col-md-4 mb-3">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body text-center">
                        <h6 class="card-title text-primary">${weather.location}</h6>
                        <div class="weather-icon display-4 mb-2">${weather.condition.icon}</div>
                        <div class="temperature h4 mb-1">${Math.round(weather.temperature)}°C</div>
                        <div class="condition-text small text-muted mb-3">${weather.condition.text}</div>
                        <div class="weather-details">
                            <div class="row small text-muted">
                                <div class="col-6">
                                    💨 ${Math.round(weather.windSpeed)} m/s
                                </div>
                                <div class="col-6">
                                    💧 ${weather.humidity}%
                                </div>
                                <div class="col-6">
                                    📊 ${weather.pressure} hPa
                                </div>
                                <div class="col-6">
                                    🎯 ${weather.source}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        weatherContainer.innerHTML = weatherHTML;
    }

    /**
     * Initialize the maritime map visualization
     * Currently shows route information, can be enhanced with interactive maps
     */
    initializeMap() {
        const mapContainer = document.getElementById('maritime-map');
        if (!mapContainer) return;

        const routePoints = this.routeManager.getAllRoutePoints();
        const shipCount = this.dataScience.analyticsData?.fleet_metrics?.total_ships || 12;
        
        mapContainer.innerHTML = `
            <div style="height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px;">
                <div class="text-center p-4">
                    <h4>🗺️ Live Maritime Map</h4>
                    <p class="mb-3">Kristiansand ↔ Oslo Route</p>
                    
                    <div class="mb-3">
                        <div style="display: inline-block; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px; backdrop-filter: blur(10px);">
                            <strong>Route Visualization</strong><br>
                            <small>Interactive map integration ready</small>
                        </div>
                    </div>
                    
                    <div class="row mt-3">
                        <div class="col-6">
                            <small>🚢 ${shipCount} Vessels Tracked</small>
                        </div>
                        <div class="col-6">
                            <small>📡 AIS Connected</small>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <small class="text-light">
                            Route Points: ${routePoints.map(p => p.name).join(' → ')}
                        </small>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Update route ETA display from backend API
     * Uses enhanced ETA endpoint with weather adjustments
     */
    async updateRouteETA() {
        try {
            // Try enhanced ETA endpoint first
            const response = await fetch('/maritime/api/route/eta-enhanced');
            const data = await response.json();
            
            if (data.status === 'success') {
                const etaDisplay = document.getElementById('route-eta-display');
                if (etaDisplay) {
                    etaDisplay.innerHTML = `
                        <strong>Enhanced ETA:</strong> ${data.data.adjusted_eta_hours}h
                        <br><small>Base: ${data.data.base_eta_hours}h | 
                        Weather impact: ${data.data.weather_impact_percent}%</small>
                    `;
                }
            }
        } catch (error) {
            console.warn('Failed to fetch enhanced ETA, trying legacy...');
            // Fallback to legacy ETA
            await this.updateLegacyETA();
        }
    }

    /**
     * Fallback to legacy ETA calculation
     */
    async updateLegacyETA() {
        try {
            const response = await fetch('/maritime/api/route/eta');
            const data = await response.json();
            
            if (data.status === 'success') {
                const etaDisplay = document.getElementById('route-eta-display');
                if (etaDisplay) {
                    etaDisplay.innerHTML = `
                        <strong>ETA:</strong> ${data.data.adjusted_eta}h
                        <br><small>Base: ${data.data.base_eta}h</small>
                    `;
                }
            }
        } catch (error) {
            console.warn('All ETA endpoints failed');
        }
    }

    /**
     * Setup auto-refresh mechanism for live data updates
     * Weather: 5 minutes, Analytics: 2 minutes
     */
    setupAutoRefresh() {
        // Refresh weather every 5 minutes, analytics every 2 minutes
        this.updateInterval = setInterval(() => {
            this.loadWeatherData();
            this.dataScience.loadAISData();
        }, 300000); // 5 minutes
        
        console.log('🔄 Auto-refresh enabled (5 minute intervals)');
    }

    /**
     * Setup event listeners for user interactions
     */
    setupEventListeners() {
        const refreshButton = document.getElementById('refresh-weather');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.loadWeatherData();
                this.showNotification('Refreshing MET Norway data...', 'info');
            });
        }
        
        // Add click handler for optimization buttons
        const optimizeButtons = document.querySelectorAll('.btn-outline-primary, .btn-outline-success');
        optimizeButtons.forEach(button => {
            if (button.disabled) {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showNotification('This feature is coming soon!', 'info');
                });
            }
        });
    }

    /**
     * Update API status display based on service availability
     */
    updateStatusDisplay() {
        const statusElement = document.getElementById('api-status');
        if (statusElement) {
            if (this.weatherService.isOnline) {
                statusElement.className = 'badge bg-success';
                statusElement.textContent = `MET Norway Connected`;
                statusElement.title = `Data source: ${this.weatherService.currentSource}`;
            } else {
                statusElement.className = 'badge bg-warning';
                statusElement.textContent = 'Offline Mode';
                statusElement.title = 'Using simulated data';
            }
        }
    }

    /**
     * Show user notification (simple implementation)
     * @param {string} message - Notification message
     * @param {string} type - Notification type (info, success, warning, error)
     */
    showNotification(message, type = 'info') {
        // Simple notification implementation - can be enhanced with toast library
        console.log(`📢 ${type.toUpperCase()}: ${message}`);
        
        // Visual notification for user
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    /**
     * Display error message to user
     * @param {string} message - Error message to display
     */
    displayError(message) {
        const weatherContainer = document.getElementById('weather-data');
        if (weatherContainer) {
            weatherContainer.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning" role="alert">
                        <h6>🌤️ Weather Service Notice</h6>
                        <p class="mb-0">${message}</p>
                        <small class="text-muted">The system will automatically retry.</small>
                    </div>
                </div>
            `;
        }
    }
}

// Initialize dashboard when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM loaded, starting maritime dashboard...');
    const dashboard = new MaritimeDashboard();
    dashboard.initialize().catch(error => {
        console.error('❌ Dashboard failed to initialize:', error);
    });
});

// Export classes for potential testing or extension
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        MaritimeWeatherService,
        MaritimeDataScience,
        MaritimeRouteManager,
        MaritimeDashboard
    };
}