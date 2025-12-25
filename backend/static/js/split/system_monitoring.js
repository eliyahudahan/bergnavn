// backend/static/js/split/system_monitoring.js
/**
 * System Monitoring Module for BergNavn Dashboard
 * Uses the new /api/system/* endpoints for comprehensive system monitoring
 */

class SystemMonitor {
    constructor() {
        this.baseUrl = '/api/system';
        this.charts = {};
        this.metricsHistory = [];
        this.autoRefreshInterval = null;
        this.isAutoRefresh = true;
        this.updateInterval = 30000; // 30 seconds
        
        this.initializeCharts();
        this.loadAllData();
        this.startAutoRefresh();
        this.setupEventListeners();
    }
    
    initializeCharts() {
        // Performance Chart
        const perfCtx = document.getElementById('performanceChart');
        if (perfCtx) {
            this.charts.performance = new Chart(perfCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Memory Usage (MB)',
                            data: [],
                            borderColor: 'rgb(13, 110, 253)',
                            backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Database Response (ms)',
                            data: [],
                            borderColor: 'rgb(25, 135, 84)',
                            backgroundColor: 'rgba(25, 135, 84, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Value'
                            }
                        }
                    }
                }
            });
        }
        
        // Health Chart
        const healthCtx = document.getElementById('healthChart');
        if (healthCtx) {
            this.charts.health = new Chart(healthCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Healthy', 'Degraded', 'Unhealthy'],
                    datasets: [{
                        data: [1, 1, 1], // Initial equal distribution
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(220, 53, 69, 0.8)'
                        ],
                        borderColor: [
                            'rgb(40, 167, 69)',
                            'rgb(255, 193, 7)',
                            'rgb(220, 53, 69)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
    
    async loadAllData() {
        try {
            await Promise.all([
                this.loadSystemSummary(),
                this.loadHealthCheck(),
                this.loadMetrics()
            ]);
            
            this.updateLastUpdateTime();
            this.logActivity('System', 'Data refresh completed', 'info');
            
        } catch (error) {
            console.error('Failed to load system data:', error);
            this.showError('Failed to load system data');
        }
    }
    
    async loadSystemSummary() {
        try {
            const response = await fetch(`${this.baseUrl}/summary`);
            const data = await response.json();
            
            if (data.status === 'operational') {
                this.updateOverviewCards(data);
                this.updateRecentRoutes(data);
                this.updateSystemInfo(data);
            }
        } catch (error) {
            console.error('Error loading system summary:', error);
        }
    }
    
    async loadHealthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            const data = await response.json();
            
            if (data.checks) {
                this.updateHealthCards(data.checks);
                this.updateHealthChart(data.checks);
                this.updateDetailedServices(data.checks);
            }
        } catch (error) {
            console.error('Error loading health check:', error);
        }
    }
    
    async loadMetrics() {
        try {
            const response = await fetch(`${this.baseUrl}/metrics`);
            const data = await response.json();
            
            if (data.counters) {
                this.updatePerformanceChart(data);
                this.updateMetricsCards(data);
            }
        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }
    
    updateOverviewCards(data) {
        // Total Routes
        const totalRoutes = data.data?.routes?.total || 0;
        document.getElementById('total-routes').textContent = totalRoutes;
        document.getElementById('active-routes').textContent = `${totalRoutes} active`;
        
        const totalDistance = data.statistics?.total_distance_nm || 0;
        document.getElementById('total-distance').textContent = `${totalDistance.toFixed(1)} nm`;
        
        // Active Vessels
        const activeVessels = data.services?.ais?.active_vessels || 0;
        document.getElementById('active-vessels').textContent = activeVessels;
        document.getElementById('ais-connected').textContent = 
            data.services?.ais?.status === 'healthy' ? 'Connected' : 'Disconnected';
        document.getElementById('ais-source').textContent = 
            data.services?.ais?.source || 'Unknown';
        
        // Database
        const dbSize = data.services?.database?.database_size_mb || 0;
        document.getElementById('db-size').textContent = `${dbSize.toFixed(1)} MB`;
        document.getElementById('db-version').textContent = 
            `v${data.services?.database?.postgres_version || '?'}`;
        document.getElementById('db-response').textContent = 
            `${data.services?.database?.response_time_ms || '?'} ms`;
        
        // System Uptime
        const uptimeSeconds = data.system?.uptime_seconds || 0;
        document.getElementById('uptime').textContent = this.formatUptime(uptimeSeconds);
        document.getElementById('memory-usage').textContent = 
            `${data.performance?.memory_usage_mb || '?'} MB`;
        document.getElementById('active-threads').textContent = 
            `${data.performance?.active_threads || '?'} threads`;
        
        // Environment
        document.getElementById('environment').textContent = 
            data.system?.environment || 'development';
        document.getElementById('system-version').textContent = 
            `v${data.system?.version || '1.0.0'}`;
    }
    
    updateHealthCards(checks) {
        const container = document.getElementById('system-health-cards');
        if (!container) return;
        
        const healthy = checks.filter(c => c.status === 'healthy').length;
        const degraded = checks.filter(c => c.status === 'degraded').length;
        const unhealthy = checks.filter(c => c.status === 'unhealthy').length;
        const total = checks.length;
        
        // Update overall health badge
        const overallHealth = document.getElementById('overall-health');
        if (overallHealth) {
            if (unhealthy > 0) {
                overallHealth.className = 'badge bg-danger ms-2';
                overallHealth.textContent = 'Unhealthy';
            } else if (degraded > 0) {
                overallHealth.className = 'badge bg-warning ms-2';
                overallHealth.textContent = 'Degraded';
            } else {
                overallHealth.className = 'badge bg-success ms-2';
                overallHealth.textContent = 'Healthy';
            }
        }
        
        let html = '';
        
        // Database Health
        const dbCheck = checks.find(c => c.service.includes('database'));
        html += `
            <div class="col-md-3 mb-3">
                <div class="card h-100 border-${this.getStatusColor(dbCheck?.status)}">
                    <div class="card-body text-center p-3">
                        <div class="mb-2">
                            <i class="bi bi-database fs-1 text-${this.getStatusColor(dbCheck?.status)}"></i>
                        </div>
                        <h6>Database</h6>
                        <span class="badge bg-${this.getStatusColor(dbCheck?.status)} service-status-badge">
                            ${dbCheck?.status || 'unknown'}
                        </span>
                        ${dbCheck?.details?.postgres_version ? `
                            <small class="d-block mt-2 text-muted">${dbCheck.details.postgres_version}</small>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        // AIS Health
        const aisCheck = checks.find(c => c.service.includes('ais'));
        html += `
            <div class="col-md-3 mb-3">
                <div class="card h-100 border-${this.getStatusColor(aisCheck?.status)}">
                    <div class="card-body text-center p-3">
                        <div class="mb-2">
                            <i class="bi bi-ship fs-1 text-${this.getStatusColor(aisCheck?.status)}"></i>
                        </div>
                        <h6>AIS Service</h6>
                        <span class="badge bg-${this.getStatusColor(aisCheck?.status)} service-status-badge">
                            ${aisCheck?.status || 'unknown'}
                        </span>
                        ${aisCheck?.details?.active_vessels ? `
                            <small class="d-block mt-2 text-muted">${aisCheck.details.active_vessels} vessels</small>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        // BarentsWatch Health
        const bwCheck = checks.find(c => c.service.includes('barentswatch'));
        html += `
            <div class="col-md-3 mb-3">
                <div class="card h-100 border-${this.getStatusColor(bwCheck?.status)}">
                    <div class="card-body text-center p-3">
                        <div class="mb-2">
                            <i class="bi bi-shield-check fs-1 text-${this.getStatusColor(bwCheck?.status)}"></i>
                        </div>
                        <h6>BarentsWatch</h6>
                        <span class="badge bg-${this.getStatusColor(bwCheck?.status)} service-status-badge">
                            ${bwCheck?.status || 'unknown'}
                        </span>
                        ${bwCheck?.details?.ais_access ? `
                            <small class="d-block mt-2 text-muted">AIS: ${bwCheck.details.ais_access ? '✅' : '❌'}</small>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        // Weather Health
        const weatherCheck = checks.find(c => c.service.includes('weather'));
        html += `
            <div class="col-md-3 mb-3">
                <div class="card h-100 border-${this.getStatusColor(weatherCheck?.status)}">
                    <div class="card-body text-center p-3">
                        <div class="mb-2">
                            <i class="bi bi-cloud-sun fs-1 text-${this.getStatusColor(weatherCheck?.status)}"></i>
                        </div>
                        <h6>Weather API</h6>
                        <span class="badge bg-${this.getStatusColor(weatherCheck?.status)} service-status-badge">
                            ${weatherCheck?.status || 'unknown'}
                        </span>
                        ${weatherCheck?.details?.primary_source ? `
                            <small class="d-block mt-2 text-muted">${weatherCheck.details.primary_source}</small>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
        // Update total services badge
        const totalServicesBadge = document.getElementById('total-services');
        if (totalServicesBadge) {
            totalServicesBadge.textContent = `${total} services`;
        }
    }
    
    updateHealthChart(checks) {
        if (!this.charts.health) return;
        
        const healthy = checks.filter(c => c.status === 'healthy').length;
        const degraded = checks.filter(c => c.status === 'degraded').length;
        const unhealthy = checks.filter(c => c.status === 'unhealthy').length;
        
        this.charts.health.data.datasets[0].data = [healthy, degraded, unhealthy];
        this.charts.health.update();
        
        // Update health summary
        const summary = document.getElementById('health-summary');
        if (summary) {
            summary.innerHTML = `
                <div class="alert alert-${unhealthy > 0 ? 'danger' : degraded > 0 ? 'warning' : 'success'}">
                    <div class="d-flex align-items-center">
                        <i class="bi bi-${unhealthy > 0 ? 'exclamation-triangle' : degraded > 0 ? 'exclamation-circle' : 'check-circle'} me-2"></i>
                        <div>
                            <strong>${healthy}/${checks.length} services healthy</strong>
                            ${unhealthy > 0 ? 
                                `<small class="d-block mt-1">${unhealthy} service(s) need attention</small>` :
                                degraded > 0 ?
                                `<small class="d-block mt-1">${degraded} service(s) degraded</small>` :
                                `<small class="d-block mt-1">All systems operational</small>`
                            }
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    updateDetailedServices(checks) {
        const container = document.getElementById('detailed-services');
        if (!container) return;
        
        let html = '';
        checks.forEach(check => {
            html += `
                <div class="col-md-4 col-lg-3 mb-3">
                    <div class="card h-100 border-start border-start-3 border-${this.getStatusColor(check.status)}">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title mb-0" style="font-size: 0.9rem;">
                                    ${this.formatServiceName(check.service)}
                                </h6>
                                <span class="badge bg-${this.getStatusColor(check.status)}" style="font-size: 0.7rem;">
                                    ${check.status}
                                </span>
                            </div>
                            ${check.response_time_ms ? `
                                <small class="text-muted d-block mb-1">
                                    <i class="bi bi-clock me-1"></i>
                                    ${check.response_time_ms} ms
                                </small>
                            ` : ''}
                            ${check.details ? `
                                <small class="text-muted" style="font-size: 0.75rem;">
                                    ${Object.entries(check.details)
                                        .filter(([key]) => !key.includes('_') || key === 'count')
                                        .slice(0, 2)
                                        .map(([key, value]) => `${key}: ${value}`)
                                        .join('<br>')}
                                </small>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    updatePerformanceChart(metrics) {
        if (!this.charts.performance) return;
        
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Add to history
        this.metricsHistory.push({
            timestamp: now,
            memory: metrics.gauges?.memory_usage_bytes ? 
                metrics.gauges.memory_usage_bytes / (1024 * 1024) : 0,
            dbResponse: metrics.timers?.database_query_ms || 0
        });
        
        // Keep only last 10 entries
        if (this.metricsHistory.length > 10) {
            this.metricsHistory.shift();
        }
        
        // Update chart
        this.charts.performance.data.labels = this.metricsHistory.map(m => m.timestamp);
        this.charts.performance.data.datasets[0].data = this.metricsHistory.map(m => m.memory);
        this.charts.performance.data.datasets[1].data = this.metricsHistory.map(m => m.dbResponse);
        this.charts.performance.update();
    }
    
    updateRecentRoutes(data) {
        const container = document.getElementById('recent-routes');
        if (!container || !data.data?.routes?.recent) return;
        
        let html = '';
        data.data.routes.recent.forEach(route => {
            html += `
                <tr>
                    <td>
                        <small class="d-block">${route.name || 'Unnamed Route'}</small>
                    </td>
                    <td><span class="badge bg-success bg-opacity-25 text-success">${route.origin || '?'}</span></td>
                    <td><span class="badge bg-danger bg-opacity-25 text-danger">${route.destination || '?'}</span></td>
                    <td><small>${route.distance || 0} nm</small></td>
                </tr>
            `;
        });
        
        container.innerHTML = html;
    }
    
    updateMetricsCards(metrics) {
        // Update details text
        const routesDetails = document.getElementById('routes-details');
        if (routesDetails && metrics.counters?.routes_total) {
            routesDetails.textContent = 
                `${metrics.counters.routes_total} total, ${metrics.counters.routes_active || 0} active`;
        }
        
        const aisStatus = document.getElementById('ais-status');
        if (aisStatus) {
            aisStatus.textContent = metrics.counters?.routes_created_last_hour ? 
                `${metrics.counters.routes_created_last_hour} new last hour` : 
                'AIS data';
        }
    }
    
    updateSystemInfo(data) {
        // This method can be expanded to update additional system information
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const dateStr = now.toLocaleDateString([], { day: 'numeric', month: 'short' });
        
        document.getElementById('last-update').textContent = `${dateStr} ${timeStr}`;
    }
    
    logActivity(service, message, type) {
        const container = document.getElementById('activity-log');
        if (!container) return;
        
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const badgeClass = type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'success';
        
        const activityItem = `
            <div class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <small class="mb-1">${service}</small>
                    <small class="text-muted">${now}</small>
                </div>
                <p class="mb-1" style="font-size: 0.85rem;">${message}</p>
                <small><span class="badge bg-${badgeClass}">${type}</span></small>
            </div>
        `;
        
        // Add to beginning and limit to 5 items
        container.innerHTML = activityItem + container.innerHTML;
        const items = container.querySelectorAll('.list-group-item');
        if (items.length > 5) {
            items[items.length - 1].remove();
        }
    }
    
    formatUptime(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
        return `${Math.floor(seconds / 86400)}d`;
    }
    
    formatServiceName(name) {
        return name
            .replace(/_/g, ' ')
            .replace(/([a-z])([A-Z])/g, '$1 $2')
            .replace(/\b\w/g, l => l.toUpperCase())
            .replace('Api', 'API')
            .replace('Ais', 'AIS');
    }
    
    getStatusColor(status) {
        switch(status?.toLowerCase()) {
            case 'healthy':
            case 'ok':
            case 'success':
                return 'success';
            case 'degraded':
            case 'warning':
                return 'warning';
            case 'unhealthy':
            case 'error':
            case 'failed':
                return 'danger';
            default:
                return 'secondary';
        }
    }
    
    startAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        if (this.isAutoRefresh) {
            this.autoRefreshInterval = setInterval(() => {
                this.loadAllData();
            }, this.updateInterval);
        }
    }
    
    toggleAutoRefresh() {
        this.isAutoRefresh = !this.isAutoRefresh;
        const button = document.querySelector('button[onclick*="toggleAutoRefresh"]');
        
        if (button) {
            if (this.isAutoRefresh) {
                button.innerHTML = '<i class="bi bi-pause-fill"></i> Pause auto-refresh';
                button.className = button.className.replace('btn-outline-secondary', 'btn-outline-primary');
                this.startAutoRefresh();
            } else {
                button.innerHTML = '<i class="bi bi-play-fill"></i> Resume auto-refresh';
                button.className = button.className.replace('btn-outline-primary', 'btn-outline-secondary');
                if (this.autoRefreshInterval) {
                    clearInterval(this.autoRefreshInterval);
                    this.autoRefreshInterval = null;
                }
            }
        }
    }
    
    setupEventListeners() {
        // Add any additional event listeners here
    }
    
    showError(message) {
        console.error('System Monitor Error:', message);
        this.logActivity('System', message, 'error');
    }
    
    // Static method for global access
    static refreshAll() {
        if (window.systemMonitorInstance) {
            window.systemMonitorInstance.loadAllData();
        }
    }
    
    static toggleAutoRefresh() {
        if (window.systemMonitorInstance) {
            window.systemMonitorInstance.toggleAutoRefresh();
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.systemMonitorInstance = new SystemMonitor();
    
    // Make methods globally available for HTML onclick handlers
    window.SystemMonitor = {
        refreshAll: () => window.systemMonitorInstance?.loadAllData(),
        toggleAutoRefresh: () => window.systemMonitorInstance?.toggleAutoRefresh()
    };
});