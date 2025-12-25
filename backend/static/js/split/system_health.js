// backend/static/js/split/system_health.js
/**
 * System Health Widget for Maritime Dashboard
 * Adds system monitoring to the existing maritime dashboard
 */

class SystemHealthWidget {
    constructor() {
        this.baseUrl = '/api/system';
        this.updateInterval = 30000; // 30 seconds
        this.autoRefresh = true;
        
        this.initializeWidget();
        this.loadSystemHealth();
        this.startAutoRefresh();
    }
    
    initializeWidget() {
        // Create HTML structure for the widget
        const container = document.getElementById('system-health-widget');
        if (!container) return;
        
        container.innerHTML = `
            <div class="col-md-3 mb-3">
                <div class="text-center">
                    <h3 id="total-routes-count" class="mb-1">--</h3>
                    <small class="text-muted">Total Routes</small>
                    <div class="mt-1">
                        <span class="badge bg-success bg-opacity-25 text-success" id="db-status">
                            <i class="bi bi-database me-1"></i>Connected
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3 mb-3">
                <div class="text-center">
                    <h3 id="active-vessels-count" class="mb-1">--</h3>
                    <small class="text-muted">Active Vessels</small>
                    <div class="mt-1">
                        <span class="badge bg-success bg-opacity-25 text-success" id="ais-status">
                            <i class="bi bi-ship me-1"></i>Live
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3 mb-3">
                <div class="text-center">
                    <h3 id="services-healthy" class="mb-1">--</h3>
                    <small class="text-muted">Services Healthy</small>
                    <div class="mt-1">
                        <span class="badge bg-success bg-opacity-25 text-success" id="health-status">
                            <i class="bi bi-check-circle me-1"></i>Good
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3 mb-3">
                <div class="text-center">
                    <h3 id="response-time" class="mb-1">-- ms</h3>
                    <small class="text-muted">Avg Response</small>
                    <div class="mt-1">
                        <span class="badge bg-info bg-opacity-25 text-info" id="performance-status">
                            <i class="bi bi-lightning me-1"></i>Fast
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="col-12 mt-3">
                <div class="progress" style="height: 6px;">
                    <div id="system-health-progress" class="progress-bar bg-success" style="width: 100%"></div>
                </div>
                <small class="text-muted d-flex justify-content-between mt-1">
                    <span id="system-version">BergNavn v1.0.0</span>
                    <span id="last-update-time">--:--</span>
                </small>
            </div>
        `;
    }
    
    async loadSystemHealth() {
        try {
            // Load all system data in parallel
            const [summary, health, metrics] = await Promise.all([
                this.fetchData('/summary'),
                this.fetchData('/health'),
                this.fetchData('/metrics')
            ]);
            
            this.updateWidget(summary, health, metrics);
            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('Failed to load system health:', error);
            this.showErrorState();
        }
    }
    
    async fetchData(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`);
        return await response.json();
    }
    
    updateWidget(summary, health, metrics) {
        // Update counts in the widget
        if (summary?.data?.routes?.total) {
            document.getElementById('total-routes-count').textContent = summary.data.routes.total;
            document.getElementById('system-routes-count').textContent = summary.data.routes.total;
        }
        
        if (summary?.services?.ais?.active_vessels) {
            document.getElementById('active-vessels-count').textContent = summary.services.ais.active_vessels;
        }
        
        // Update health status
        if (health?.checks) {
            const healthyServices = health.checks.filter(c => c.status === 'healthy').length;
            const totalServices = health.checks.length;
            const healthPercentage = Math.round((healthyServices / totalServices) * 100);
            
            document.getElementById('services-healthy').textContent = `${healthyServices}/${totalServices}`;
            
            // Update health progress bar
            const progressBar = document.getElementById('system-health-progress');
            if (progressBar) {
                progressBar.style.width = `${healthPercentage}%`;
                progressBar.className = `progress-bar ${
                    healthPercentage >= 90 ? 'bg-success' :
                    healthPercentage >= 70 ? 'bg-warning' : 'bg-danger'
                }`;
            }
            
            // Update health status badge
            const healthStatus = document.getElementById('health-status');
            if (healthStatus) {
                healthStatus.className = `badge ${
                    healthPercentage >= 90 ? 'bg-success bg-opacity-25 text-success' :
                    healthPercentage >= 70 ? 'bg-warning bg-opacity-25 text-warning' : 'bg-danger bg-opacity-25 text-danger'
                }`;
                healthStatus.innerHTML = `<i class="bi bi-${
                    healthPercentage >= 90 ? 'check-circle' :
                    healthPercentage >= 70 ? 'exclamation-circle' : 'exclamation-triangle'
                } me-1"></i>${healthPercentage >= 90 ? 'Good' : healthPercentage >= 70 ? 'Degraded' : 'Poor'}`;
            }
        }
        
        // Update performance metrics
        if (metrics?.timers?.database_query_ms) {
            document.getElementById('response-time').textContent = 
                `${Math.round(metrics.timers.database_query_ms)} ms`;
        }
        
        // Update service status badges
        this.updateServiceBadges(summary);
        
        // Update system info
        if (summary?.system?.version) {
            document.getElementById('system-version').textContent = 
                `BergNavn v${summary.system.version}`;
        }
        
        if (summary?.system?.uptime_seconds) {
            const uptime = this.formatUptime(summary.system.uptime_seconds);
            document.getElementById('system-uptime').textContent = uptime;
        }
    }
    
    updateServiceBadges(summary) {
        if (!summary?.services) return;
        
        // Database status
        const dbStatus = document.getElementById('db-status');
        if (dbStatus && summary.services.database) {
            const isHealthy = summary.services.database.status === 'healthy';
            dbStatus.className = `badge ${
                isHealthy ? 'bg-success bg-opacity-25 text-success' : 'bg-danger bg-opacity-25 text-danger'
            }`;
            dbStatus.innerHTML = `<i class="bi bi-database me-1"></i>${
                isHealthy ? 'Connected' : 'Disconnected'
            }`;
        }
        
        // AIS status
        const aisStatus = document.getElementById('ais-status');
        if (aisStatus && summary.services.ais) {
            const isHealthy = summary.services.ais.status === 'healthy';
            aisStatus.className = `badge ${
                isHealthy ? 'bg-success bg-opacity-25 text-success' : 'bg-danger bg-opacity-25 text-danger'
            }`;
            aisStatus.innerHTML = `<i class="bi bi-ship me-1"></i>${
                isHealthy ? 'Live' : 'Offline'
            }`;
        }
        
        // Performance status
        const perfStatus = document.getElementById('performance-status');
        if (perfStatus && summary.performance) {
            const responseTime = summary.performance.database_response_ms || 0;
            const isFast = responseTime < 100;
            const isOk = responseTime < 500;
            
            perfStatus.className = `badge ${
                isFast ? 'bg-success bg-opacity-25 text-success' :
                isOk ? 'bg-warning bg-opacity-25 text-warning' : 'bg-danger bg-opacity-25 text-danger'
            }`;
            perfStatus.innerHTML = `<i class="bi bi-lightning me-1"></i>${
                isFast ? 'Fast' : isOk ? 'Normal' : 'Slow'
            }`;
        }
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        document.getElementById('last-update-time').textContent = timeStr;
    }
    
    formatUptime(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
        return `${Math.floor(seconds / 86400)}d`;
    }
    
    showErrorState() {
        const container = document.getElementById('system-health-widget');
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center py-3">
                    <i class="bi bi-exclamation-triangle text-warning fs-1"></i>
                    <p class="mt-2 text-muted">System health data unavailable</p>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.systemHealthWidget.loadSystemHealth()">
                        <i class="bi bi-arrow-clockwise me-1"></i> Retry
                    </button>
                </div>
            `;
        }
    }
    
    startAutoRefresh() {
        if (this.autoRefresh) {
            setInterval(() => {
                this.loadSystemHealth();
            }, this.updateInterval);
        }
    }
    
    // Public method for manual refresh
    refresh() {
        this.loadSystemHealth();
    }
}

// Initialize when dashboard loads
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on maritime dashboard
    if (window.location.pathname.includes('/maritime/dashboard')) {
        window.systemHealthWidget = new SystemHealthWidget();
        
        // Add refresh button to dashboard controls
        const controls = document.querySelector('.dashboard-controls div:nth-child(2)');
        if (controls) {
            const refreshBtn = document.createElement('button');
            refreshBtn.className = 'control-btn';
            refreshBtn.innerHTML = '<i class="bi bi-cpu"></i> System Health';
            refreshBtn.onclick = () => window.systemHealthWidget.refresh();
            controls.appendChild(refreshBtn);
        }
    }
});