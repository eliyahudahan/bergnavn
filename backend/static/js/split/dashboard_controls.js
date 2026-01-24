// static/js/split/dashboard_controls.js
// Dashboard controls for Maritime Dashboard

class DashboardControls {
    constructor() {
        this.map = null;
        this.isInitialized = false;
        this.layers = {
            rtz: true,
            weather: true,
            ais: true
        };
    }

    init(mapInstance) {
        console.log('🎮 Initializing dashboard controls...');
        this.map = mapInstance;
        this.setupEventListeners();
        this.isInitialized = true;
    }

    setupEventListeners() {
        // Toggle buttons
        const toggleButtons = ['rtz-toggle-btn', 'weather-toggle-btn', 'ais-toggle-btn'];
        
        toggleButtons.forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btn) {
                btn.addEventListener('click', (e) => {
                    const target = e.currentTarget;
                    target.classList.toggle('active');
                    const isActive = target.classList.contains('active');
                    
                    // Store state
                    const layerType = btnId.replace('-toggle-btn', '');
                    this.layers[layerType] = isActive;
                    
                    // Dispatch custom event
                    const event = new CustomEvent('layerToggle', {
                        detail: { layer: layerType, visible: isActive }
                    });
                    document.dispatchEvent(event);
                    
                    console.log(`🎯 ${layerType.toUpperCase()} layer ${isActive ? 'enabled' : 'disabled'}`);
                });
            }
        });

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Refreshing...';
                
                // Dispatch refresh event
                document.dispatchEvent(new Event('dashboardRefresh'));
                
                // Restore button after delay
                setTimeout(() => {
                    refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh';
                }, 2000);
            });
        }

        // Legend toggle
        const legendToggleBtn = document.getElementById('legend-toggle-btn');
        if (legendToggleBtn) {
            legendToggleBtn.addEventListener('click', () => {
                // Toggle legend panel
                this.toggleLegend();
            });
        }

        // RTZ panel controls
        this.setupRTZPanelControls();
    }

    setupRTZPanelControls() {
        const showPanelBtn = document.getElementById('show-rtz-panel');
        const controlPanel = document.getElementById('rtz-control-panel');
        
        if (showPanelBtn && controlPanel) {
            showPanelBtn.addEventListener('click', () => {
                controlPanel.style.display = controlPanel.style.display === 'none' ? 'block' : 'none';
            });
        }

        const closePanelBtn = document.querySelector('.btn-close-panel');
        if (closePanelBtn && controlPanel) {
            closePanelBtn.addEventListener('click', () => {
                controlPanel.style.display = 'none';
            });
        }

        // Route search
        const routeSearch = document.getElementById('route-search');
        if (routeSearch) {
            routeSearch.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase();
                const routeItems = document.querySelectorAll('#routes-list .route-item');
                
                routeItems.forEach(item => {
                    const routeName = item.querySelector('.route-name').textContent.toLowerCase();
                    item.style.display = routeName.includes(searchTerm) ? 'flex' : 'none';
                });
            });
        }
    }

    toggleLegend() {
        // Check if Bootstrap modal is available
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const legendModal = new bootstrap.Modal(document.getElementById('legendModal'));
            legendModal.show();
        } else {
            // Fallback: toggle simple legend display
            const legendElement = document.querySelector('.leaflet-control-legend');
            if (legendElement) {
                legendElement.style.display = legendElement.style.display === 'none' ? 'block' : 'none';
            } else {
                this.createLegend();
            }
        }
    }

    createLegend() {
        const legend = L.control({ position: 'bottomright' });
        
        legend.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'leaflet-control-legend');
            div.innerHTML = `
                <div class="legend-title">Map Legend</div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #28a745;"></div>
                    <div class="legend-label">Route Start</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #dc3545;"></div>
                    <div class="legend-label">Route End</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #007bff;"></div>
                    <div class="legend-label">Waypoint</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #28a745; height: 3px; margin-top: 6px;"></div>
                    <div class="legend-label">RTZ Route</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #ffc107;"></div>
                    <div class="legend-label">Vessel</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #17a2b8;"></div>
                    <div class="legend-label">Weather Station</div>
                </div>
            `;
            return div;
        };
        
        if (this.map) {
            legend.addTo(this.map);
        }
    }

    // Public methods to control specific layers
    toggleRTZLayer(show) {
        this.layers.rtz = show;
        const btn = document.getElementById('rtz-toggle-btn');
        if (btn) {
            if (show) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
        document.dispatchEvent(new CustomEvent('layerToggle', {
            detail: { layer: 'rtz', visible: show }
        }));
    }

    toggleWeatherLayer(show) {
        this.layers.weather = show;
        const btn = document.getElementById('weather-toggle-btn');
        if (btn) {
            if (show) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
        document.dispatchEvent(new CustomEvent('layerToggle', {
            detail: { layer: 'weather', visible: show }
        }));
    }

    toggleAISLayer(show) {
        this.layers.ais = show;
        const btn = document.getElementById('ais-toggle-btn');
        if (btn) {
            if (show) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
        document.dispatchEvent(new CustomEvent('layerToggle', {
            detail: { layer: 'ais', visible: show }
        }));
    }

    // Update stats display
    updateStats(stats) {
        if (stats.vessels) {
            const vesselCount = document.getElementById('vessel-count');
            const activeVessels = document.getElementById('active-vessels');
            if (vesselCount) vesselCount.textContent = stats.vessels.total || 0;
            if (activeVessels) activeVessels.textContent = stats.vessels.active || 0;
            
            // Update vessel type
            const vesselType = document.getElementById('vessel-type');
            if (vesselType && stats.vessels.types) {
                const types = Object.keys(stats.vessels.types).slice(0, 2);
                vesselType.textContent = types.length > 0 ? types.join(', ') : 'No vessels';
            }
        }

        if (stats.weather) {
            const weatherTemp = document.getElementById('weather-temp');
            const weatherWind = document.getElementById('weather-wind');
            const weatherLocation = document.getElementById('weather-location');
            
            if (weatherTemp && stats.weather.temperature) {
                weatherTemp.textContent = `${stats.weather.temperature}°C`;
            }
            if (weatherWind && stats.weather.wind) {
                weatherWind.textContent = `${stats.weather.wind} m/s`;
            }
            if (weatherLocation && stats.weather.location) {
                weatherLocation.textContent = stats.weather.location;
            }
        }

        if (stats.routes) {
            const routeCount = document.getElementById('route-count');
            const routeCountBadge = document.getElementById('route-count-badge');
            const waypointCount = document.getElementById('waypoint-count');
            
            if (routeCount && stats.routes.total) {
                routeCount.textContent = stats.routes.total;
            }
            if (routeCountBadge && stats.routes.total) {
                routeCountBadge.textContent = stats.routes.total;
            }
            if (waypointCount && stats.routes.waypoints) {
                waypointCount.textContent = stats.routes.waypoints;
            }
        }
    }

    // Handle port filtering
    setupPortFiltering(routesData) {
        const cityBadges = document.querySelectorAll('.city-badge[data-port]');
        
        cityBadges.forEach(badge => {
            badge.addEventListener('click', () => {
                const port = badge.dataset.port;
                
                // Remove active class from all badges
                document.querySelectorAll('.city-badge').forEach(b => {
                    b.classList.remove('active');
                });
                
                // Add active class to clicked badge
                badge.classList.add('active');
                
                // Dispatch filter event
                document.dispatchEvent(new CustomEvent('portFilter', {
                    detail: { port: port === 'reset' ? null : port }
                }));
                
                console.log(`📍 Filter applied for port: ${port}`);
            });
        });
    }

    // Show notification
    showNotification(message, type = 'info') {
        const types = {
            'info': 'alert-info',
            'success': 'alert-success',
            'warning': 'alert-warning',
            'error': 'alert-danger'
        };
        
        const alertClass = types[type] || types.info;
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            max-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Create global instance
window.dashboardControls = new DashboardControls();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardControls;
}