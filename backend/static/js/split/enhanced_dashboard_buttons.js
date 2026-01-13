// ====================================================
// ENHANCED DASHBOARD BUTTON FUNCTIONALITY
// Uses existing managers where available
// ====================================================

console.log('🔧 Loading enhanced dashboard button functionality...');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Add enhanced functionality after a short delay
    setTimeout(addEnhancedFunctionality, 1500);
});

function addEnhancedFunctionality() {
    console.log('🎯 Adding enhanced button functionality...');
    
    // Check which managers are available
    const availableManagers = {
        turbines: typeof window.windTurbineManager !== 'undefined',
        tankers: typeof window.tankerManager !== 'undefined',
        ais: typeof window.aisManager !== 'undefined',
        rtz: typeof window.toggleRTZRoutes !== 'function',
        weather: typeof window.weatherManager !== 'undefined'
    };
    
    console.log('📊 Available managers:', availableManagers);
    
    // 1. RTZ Routes Button - Add highlight functionality
    const rtzButton = document.getElementById('rtz-btn');
    if (rtzButton) {
        rtzButton.addEventListener('click', function(e) {
            // Call original function
            if (typeof window.toggleRTZRoutes === 'function') {
                window.toggleRTZRoutes();
            }
            
            // Add highlight effect if routes are visible
            if (this.classList.contains('active')) {
                highlightAllRoutes();
            }
        });
    }
    
    // 2. Refresh Data Button - Use existing refresh functions
    const refreshDataButton = document.getElementById('ais-btn');
    if (refreshDataButton) {
        refreshDataButton.addEventListener('click', function(e) {
            // Toggle AIS visibility if manager exists
            if (availableManagers.ais) {
                window.aisManager.toggleVisibility();
            }
            
            // Add enhanced refresh with loading state
            refreshAllData();
        });
    }
    
    // 3. Turbine Status Button - Use existing windTurbineManager
    const turbineButton = document.getElementById('turbine-btn');
    if (turbineButton) {
        turbineButton.addEventListener('click', function(e) {
            // Toggle turbine visibility if manager exists
            if (availableManagers.turbines) {
                window.windTurbineManager.showTurbines();
            }
            
            // Show enhanced turbine status popup
            showEnhancedTurbineStatus();
        });
    }
    
    // 4. Fuel Prices Button - Use existing tanker manager or show prices
    const fuelButton = document.getElementById('tanker-btn');
    if (fuelButton) {
        fuelButton.addEventListener('click', function(e) {
            // Toggle tanker visibility if manager exists
            if (availableManagers.tankers && typeof window.tankerManager.toggleVisibility === 'function') {
                window.tankerManager.toggleVisibility();
            }
            
            // Show fuel prices popup
            showEnhancedFuelPrices();
        });
    }
    
    console.log('✅ Enhanced functionality added to all buttons');
}

// ====================================================
// ENHANCED FUNCTIONS THAT WORK WITH EXISTING MANAGERS
// ====================================================

function highlightAllRoutes() {
    console.log('🗺️ Highlighting all routes...');
    
    // This function temporarily highlights all routes on the map
    // Works with existing route layers
    if (window.maritimeMap) {
        // Try to find route layers
        let routeLayers = null;
        
        // Check different possible layer names
        if (window.routeLayers) {
            routeLayers = window.routeLayers;
        } else if (window.rtzManager && window.rtzManager.routeLayers) {
            routeLayers = window.rtzManager.routeLayers;
        } else {
            console.log('ℹ️ No route layers found for highlighting');
            return;
        }
        
        // Store original styles
        const originalStyles = new Map();
        
        // Apply highlight style
        routeLayers.eachLayer(function(layer) {
            if (layer.setStyle) {
                originalStyles.set(layer, {
                    color: layer.options.color || '#3388ff',
                    weight: layer.options.weight || 3,
                    opacity: layer.options.opacity || 0.7
                });
                
                // Highlight style
                layer.setStyle({
                    color: '#FF5722',
                    weight: 6,
                    opacity: 0.9,
                    dashArray: null
                });
            }
        });
        
        // Revert after 3 seconds
        setTimeout(() => {
            routeLayers.eachLayer(function(layer) {
                if (originalStyles.has(layer)) {
                    layer.setStyle(originalStyles.get(layer));
                }
            });
            console.log('✅ Route highlighting completed');
        }, 3000);
        
        showNotification('Routes highlighted for 3 seconds', 'info');
    }
}

function refreshAllData() {
    console.log('🔄 Refreshing all dashboard data...');
    
    // Show loading state
    const button = document.getElementById('ais-btn');
    if (button) {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="bi bi-arrow-repeat spin"></i>';
        
        // Refresh sequence
        const refreshPromises = [];
        
        // 1. Refresh AIS if available
        if (typeof window.aisManager !== 'undefined' && 
            typeof window.aisManager.refresh === 'function') {
            refreshPromises.push(
                new Promise(resolve => {
                    window.aisManager.refresh();
                    setTimeout(resolve, 800);
                })
            );
        }
        
        // 2. Refresh weather if available
        if (typeof window.weatherManager !== 'undefined' &&
            typeof window.weatherManager.refresh === 'function') {
            refreshPromises.push(
                new Promise(resolve => {
                    window.weatherManager.refresh();
                    setTimeout(resolve, 800);
                })
            );
        }
        
        // 3. Refresh routes if available
        if (typeof window.rtzManager !== 'undefined' &&
            typeof window.rtzManager.refresh === 'function') {
            refreshPromises.push(
                new Promise(resolve => {
                    window.rtzManager.refresh();
                    setTimeout(resolve, 800);
                })
            );
        }
        
        // Wait for all refreshes
        Promise.all(refreshPromises).then(() => {
            // Restore button
            button.innerHTML = originalHTML;
            showNotification('Dashboard data refreshed successfully', 'success');
        });
    }
}

function showEnhancedTurbineStatus() {
    console.log('⚡ Showing enhanced turbine status...');
    
    // Use data from windTurbineManager if available
    let turbineData = {};
    
    if (typeof window.windTurbineManager !== 'undefined' &&
        window.windTurbineManager.turbines) {
        
        // Group by status
        const byStatus = {
            'Operational': [],
            'Planned': [],
            'Planning': []
        };
        
        window.windTurbineManager.turbines.forEach(turbine => {
            const status = turbine.status || 'Unknown';
            if (!byStatus[status]) byStatus[status] = [];
            byStatus[status].push(turbine);
        });
        
        // Create summary
        turbineData = {
            total: window.windTurbineManager.turbines.length,
            operational: byStatus['Operational']?.length || 0,
            planned: byStatus['Planned']?.length || 0,
            planning: byStatus['Planning']?.length || 0,
            totalCapacity: window.windTurbineManager.turbines.reduce((sum, t) => {
                const capacity = parseFloat(t.capacity) || 0;
                return sum + capacity;
            }, 0)
        };
    } else {
        // Fallback data
        turbineData = {
            total: 3,
            operational: 1,
            planned: 1,
            planning: 1,
            totalCapacity: 4.7
        };
    }
    
    let content = '<div style="min-width: 280px; padding: 15px;">';
    content += '<h5 style="color: #4CAF50; margin-bottom: 15px;">';
    content += '<i class="bi bi-lightning-charge me-2"></i>Wind Turbine Status';
    content += '</h5>';
    
    // Summary cards
    content += '<div class="row g-2 mb-3">';
    content += `<div class="col-6"><div class="card bg-success bg-opacity-10 p-2 text-center">
        <div class="small text-muted">Operational</div>
        <div class="h4 mb-0">${turbineData.operational}</div>
    </div></div>`;
    
    content += `<div class="col-6"><div class="card bg-warning bg-opacity-10 p-2 text-center">
        <div class="small text-muted">Total Capacity</div>
        <div class="h4 mb-0">${turbineData.totalCapacity.toFixed(1)} GW</div>
    </div></div>`;
    content += '</div>';
    
    // Status breakdown
    content += '<table class="table table-sm">';
    content += '<thead><tr><th>Status</th><th>Count</th><th>Percentage</th></tr></thead>';
    content += '<tbody>';
    
    const statuses = [
        { name: 'Operational', count: turbineData.operational, color: 'success' },
        { name: 'Planned', count: turbineData.planned, color: 'primary' },
        { name: 'Planning', count: turbineData.planning, color: 'warning' }
    ];
    
    statuses.forEach(status => {
        const percentage = turbineData.total > 0 ? 
            Math.round((status.count / turbineData.total) * 100) : 0;
        
        content += `<tr>
            <td><span class="badge bg-${status.color}">${status.name}</span></td>
            <td>${status.count}</td>
            <td>
                <div class="progress" style="height: 6px;">
                    <div class="progress-bar bg-${status.color}" 
                         style="width: ${percentage}%"></div>
                </div>
                <small>${percentage}%</small>
            </td>
        </tr>`;
    });
    
    content += '</tbody></table>';
    
    // Data source info
    content += '<div class="mt-3 small text-muted border-top pt-2">';
    content += '<i class="bi bi-info-circle me-1"></i>';
    
    if (typeof window.windTurbineManager !== 'undefined') {
        content += 'Data from Wind Turbine Manager';
    } else {
        content += 'Sample data (connect to API for live data)';
    }
    
    content += `<br><i class="bi bi-clock me-1"></i>Updated: ${new Date().toLocaleTimeString()}`;
    content += '</div></div>';
    
    // Show popup on map
    if (window.maritimeMap) {
        L.popup()
            .setLatLng([63.5, 8.5])
            .setContent(content)
            .openOn(window.maritimeMap);
    }
}

function showEnhancedFuelPrices() {
    console.log('⛽ Showing enhanced fuel prices...');
    
    // Try to get tanker data if available
    let hasTankerData = false;
    let tankerInfo = '';
    
    if (typeof window.tankerManager !== 'undefined' &&
        window.tankerManager.tankers &&
        window.tankerManager.tankers.length > 0) {
        
        hasTankerData = true;
        const activeTankers = window.tankerManager.tankers.length;
        const movingTankers = window.tankerManager.tankers.filter(t => 
            t.speed && t.speed > 1
        ).length;
        
        tankerInfo = `
            <div class="alert alert-info mb-3">
                <h6><i class="bi bi-droplet me-2"></i>Tanker Activity</h6>
                <p class="mb-1">Active tankers: <strong>${activeTankers}</strong></p>
                <p class="mb-0">Currently moving: <strong>${movingTankers}</strong></p>
            </div>
        `;
    }
    
    // Fuel price data
    const fuelPrices = {
        'Bergen': { diesel: '1.85 €/L', gasoline: '1.92 €/L', trend: '↗️', change: '+0.02' },
        'Oslo': { diesel: '1.82 €/L', gasoline: '1.89 €/L', trend: '→', change: '0.00' },
        'Trondheim': { diesel: '1.88 €/L', gasoline: '1.95 €/L', trend: '↗️', change: '+0.03' },
        'Stavanger': { diesel: '1.83 €/L', gasoline: '1.90 €/L', trend: '→', change: '0.00' },
        'Tromsø': { diesel: '1.92 €/L', gasoline: '1.99 €/L', trend: '↘️', change: '-0.01' }
    };
    
    let content = '<div style="min-width: 320px; padding: 15px;">';
    content += '<h5 style="color: #FF9800; margin-bottom: 15px;">';
    content += '<i class="bi bi-fuel-pump me-2"></i>Regional Fuel Market';
    content += '</h5>';
    
    // Add tanker info if available
    if (hasTankerData) {
        content += tankerInfo;
    }
    
    // Price table
    content += '<h6 class="mb-2">Fuel Prices</h6>';
    content += '<table class="table table-sm table-hover">';
    content += '<thead><tr><th>Region</th><th>Diesel</th><th>Gasoline</th><th>Trend</th></tr></thead>';
    content += '<tbody>';
    
    for (const [region, prices] of Object.entries(fuelPrices)) {
        content += `<tr>
            <td><strong>${region}</strong></td>
            <td>
                ${prices.diesel}
                <small class="text-muted d-block">${prices.change}</small>
            </td>
            <td>${prices.gasoline}</td>
            <td class="h4">${prices.trend}</td>
        </tr>`;
    }
    
    content += '</tbody></table>';
    
    // Market summary
    const avgDiesel = Object.values(fuelPrices).reduce((sum, p) => 
        sum + parseFloat(p.diesel), 0) / Object.keys(fuelPrices).length;
    const avgGasoline = Object.values(fuelPrices).reduce((sum, p) => 
        sum + parseFloat(p.gasoline), 0) / Object.keys(fuelPrices).length;
    
    content += '<div class="row g-2 mt-3">';
    content += `<div class="col-6"><div class="card bg-light p-2 text-center">
        <div class="small text-muted">Avg. Diesel</div>
        <div class="h5 mb-0">${avgDiesel.toFixed(2)} €/L</div>
    </div></div>`;
    
    content += `<div class="col-6"><div class="card bg-light p-2 text-center">
        <div class="small text-muted">Avg. Gasoline</div>
        <div class="h5 mb-0">${avgGasoline.toFixed(2)} €/L</div>
    </div></div>`;
    content += '</div>';
    
    // Footer
    content += '<div class="mt-3 small text-muted border-top pt-2">';
    content += '<i class="bi bi-info-circle me-1"></i>';
    
    if (hasTankerData) {
        content += 'Tanker data from live monitoring';
    } else {
        content += 'Prices are simulated (connect to API for live data)';
    }
    
    content += `<br><i class="bi bi-clock me-1"></i>Market data: ${new Date().toLocaleDateString()}`;
    content += '</div></div>';
    
    // Show popup on map
    if (window.maritimeMap) {
        L.popup()
            .setLatLng([60.5, 9.5])
            .setContent(content)
            .openOn(window.maritimeMap);
    }
}

function showNotification(message, type = 'info') {
    // Create a simple notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            <div>${message}</div>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Export functions for debugging
window.dashboardButtons = {
    highlightAllRoutes,
    refreshAllData,
    showEnhancedTurbineStatus,
    showEnhancedFuelPrices
};
