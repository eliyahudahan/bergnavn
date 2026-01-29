// backend/static/js/split/dashboard_controls.js
// Dashboard controls - SIMPLE AND EFFECTIVE VERSION

class DashboardControls {
    constructor() {
        this.map = null;
        this.layers = {
            rtz: true,
            weather: true,
            ais: true
        };
    }

    init(mapInstance) {
        console.log('🎮 Dashboard controls initialized');
        this.map = mapInstance;
        this.setupEventListeners();
        this.setupRouteTableInteractivity();
    }

    setupEventListeners() {
        // Toggle buttons
        ['rtz-toggle-btn', 'weather-toggle-btn', 'ais-toggle-btn'].forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btn) {
                btn.addEventListener('click', (e) => {
                    const target = e.currentTarget;
                    target.classList.toggle('active');
                    const isActive = target.classList.contains('active');
                    const layerType = btnId.replace('-toggle-btn', '');
                    this.layers[layerType] = isActive;
                    console.log(`🎯 ${layerType.toUpperCase()} layer ${isActive ? 'enabled' : 'disabled'}`);
                });
            }
        });

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Refreshing...';
                refreshBtn.disabled = true;
                
                setTimeout(() => {
                    refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh';
                    refreshBtn.disabled = false;
                    this.showNotification('Dashboard refreshed', 'success');
                }, 2000);
            });
        }

        // Show RTZ panel button
        const showPanelBtn = document.getElementById('show-rtz-panel');
        if (showPanelBtn) {
            showPanelBtn.addEventListener('click', () => {
                const routesTable = document.querySelector('.dashboard-card:has(#routes-table-body)');
                if (routesTable) {
                    routesTable.scrollIntoView({ behavior: 'smooth' });
                    this.showNotification('Showing routes list', 'info');
                }
            });
        }
    }

    setupRouteTableInteractivity() {
        const routeRows = document.querySelectorAll('.route-row');
        if (routeRows.length === 0) return;
        
        console.log(`📋 Setting up ${routeRows.length} route rows`);
        
        // Add click handlers to route rows
        routeRows.forEach(row => {
            const routeId = row.dataset.routeId;
            
            row.style.cursor = 'pointer';
            row.style.transition = 'background-color 0.2s';
            
            row.addEventListener('click', (e) => {
                if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
                
                // Highlight row
                routeRows.forEach(r => {
                    r.classList.remove('route-row-highlighted');
                    r.style.backgroundColor = '';
                });
                
                row.classList.add('route-row-highlighted');
                row.style.backgroundColor = 'rgba(52, 152, 219, 0.15)';
                
                // Highlight on map
                this.highlightRouteOnMap(routeId);
                
                // Show notification
                const routeName = row.querySelector('.route-name-display')?.textContent || `Route ${routeId}`;
                this.showNotification(`Selected: ${routeName}`, 'info');
            });
            
            // Hover effects
            row.addEventListener('mouseenter', () => {
                if (!row.classList.contains('route-row-highlighted')) {
                    row.style.backgroundColor = 'rgba(52, 152, 219, 0.05)';
                }
            });
            
            row.addEventListener('mouseleave', () => {
                if (!row.classList.contains('route-row-highlighted')) {
                    row.style.backgroundColor = '';
                }
            });
        });
        
        // Action buttons
        document.querySelectorAll('.view-route-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const routeId = btn.dataset.routeId;
                this.zoomToRoute(routeId);
            });
        });
        
        document.querySelectorAll('.highlight-route-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const routeId = btn.dataset.routeId;
                this.highlightRoute(routeId);
            });
        });
        
        document.querySelectorAll('.route-info-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const routeId = btn.dataset.routeId;
                this.showRouteInfo(routeId);
            });
        });
    }
    
    highlightRouteOnMap(routeId) {
        if (window.rtzWaypoints && window.rtzWaypoints.highlightRoute) {
            window.rtzWaypoints.highlightRoute(routeId);
        } else {
            console.warn('RTZ Waypoints module not available');
        }
    }
    
    zoomToRoute(routeId) {
        if (!this.map) return;
        
        // Try to get route data
        let routeData = null;
        try {
            const routesDataElement = document.getElementById('routes-data');
            if (routesDataElement && routesDataElement.textContent) {
                const routesData = JSON.parse(routesDataElement.textContent);
                routeData = routesData.find(r => 
                    r.route_id === routeId || 
                    r.id === routeId || 
                    `route-${r.route_id || r.id}` === routeId
                );
            }
        } catch (e) {
            console.error('Error getting route data:', e);
        }
        
        if (routeData && routeData.waypoints && routeData.waypoints.length > 0) {
            const bounds = L.latLngBounds(
                routeData.waypoints.map(wp => [wp.lat || wp.latitude, wp.lon || wp.longitude])
            );
            
            if (bounds.isValid()) {
                this.map.fitBounds(bounds, {
                    padding: [50, 50],
                    maxZoom: 10,
                    animate: true
                });
                
                this.highlightRouteOnMap(routeId);
                this.showNotification('Zoomed to route', 'success');
                return;
            }
        }
        
        this.showNotification('Could not zoom to route', 'warning');
    }
    
    highlightRoute(routeId) {
        // Highlight in table
        const row = document.querySelector(`.route-row[data-route-id="${routeId}"]`);
        if (row) {
            row.click();
        }
        
        // Highlight on map
        this.highlightRouteOnMap(routeId);
    }
    
    showRouteInfo(routeId) {
        // Simple info display
        const row = document.querySelector(`.route-row[data-route-id="${routeId}"]`);
        if (row) {
            const routeName = row.querySelector('.route-name-display')?.textContent || `Route ${routeId}`;
            const portBadge = row.querySelector('.badge.bg-primary');
            const portName = portBadge ? portBadge.textContent : 'Unknown port';
            
            this.showNotification(`${routeName} (${portName}) - Details would open here`, 'info');
        }
    }
    
    showNotification(message, type = 'info') {
        // Simple notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: ${type === 'success' ? '#d4edda' : type === 'warning' ? '#fff3cd' : '#d1ecf1'};
            color: ${type === 'success' ? '#155724' : type === 'warning' ? '#856404' : '#0c5460'};
            padding: 12px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 9999;
            max-width: 300px;
            border: 1px solid ${type === 'success' ? '#c3e6cb' : type === 'warning' ? '#ffeaa7' : '#bee5eb'};
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize
window.dashboardControls = new DashboardControls();

document.addEventListener('DOMContentLoaded', function() {
    const checkMap = setInterval(() => {
        if (window.map) {
            clearInterval(checkMap);
            window.dashboardControls.init(window.map);
            console.log('✅ Dashboard controls ready');
        }
    }, 100);
});