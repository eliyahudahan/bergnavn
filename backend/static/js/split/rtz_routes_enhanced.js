// backend/static/js/split/rtz_routes_enhanced.js
// Enhanced RTZ route management for maritime dashboard
// Features: Color coding, start/end markers, route control panel, filtering

// Global route manager
window.rtzManager = {
    routes: [],
    layers: {},
    controlPanel: null,
    isVisible: true,
    currentFilter: null,
    
    // Initialize route manager
    init: function(routesData) {
        console.log('🎨 Initializing enhanced RTZ route manager...');
        this.routes = routesData || [];
        
        if (this.routes.length > 0) {
            this.renderAllRoutes();
            this.createControlPanel();
            this.updateRouteStats();
            console.log(`✅ Loaded ${this.routes.length} enhanced routes`);
        } else {
            console.warn('⚠️ No routes data provided to RTZ manager');
        }
    },
    
    // Render all routes on map
    renderAllRoutes: function() {
        if (!window.map) {
            console.error('Map not initialized');
            return;
        }
        
        // Clear existing routes
        this.clearRoutes();
        
        // Create route layers group
        this.layers.group = L.layerGroup().addTo(window.map);
        
        // Render each route
        this.routes.forEach((route, index) => {
            this.renderSingleRoute(route, index);
        });
        
        // Create legend
        this.createLegend();
        
        console.log(`🗺️ Rendered ${this.routes.length} routes on map`);
    },
    
    // Render a single route with enhanced visuals
    renderSingleRoute: function(route, index) {
        const waypoints = route.waypoints || [];
        if (waypoints.length < 2) return;
        
        const visual = route.visual_properties || {};
        const latlngs = waypoints.map(wp => [wp.lat, wp.lon]);
        const routeId = `route-${index}`;
        
        // Create polyline with visual properties
        const polyline = L.polyline(latlngs, {
            color: visual.color || '#3498db',
            weight: visual.weight || 3,
            opacity: visual.opacity || 0.8,
            dashArray: visual.dashArray || 'none',
            lineCap: visual.line_cap || 'round',
            lineJoin: visual.line_join || 'round',
            className: `route-line route-${index}`
        }).addTo(this.layers.group);
        
        // Add start marker
        const startMarker = L.circleMarker([waypoints[0].lat, waypoints[0].lon], {
            color: visual.start_marker_color || '#00FF00',
            radius: visual.start_marker_radius || 8,
            fillColor: visual.start_marker_color || '#00FF00',
            fillOpacity: 1,
            weight: 2,
            className: 'route-start-marker'
        }).addTo(this.layers.group);
        
        // Add end marker
        const endMarker = L.circleMarker([waypoints[waypoints.length-1].lat, waypoints[waypoints.length-1].lon], {
            color: visual.end_marker_color || '#FF0000',
            radius: visual.end_marker_radius || 10,
            fillColor: visual.end_marker_color || '#FF0000',
            fillOpacity: 1,
            weight: 2,
            className: 'route-end-marker'
        }).addTo(this.layers.group);
        
        // Create route label at midpoint if available
        let labelMarker = null;
        if (route.label_position) {
            labelMarker = L.marker([route.label_position.lat, route.label_position.lon], {
                icon: L.divIcon({
                    html: `<div class="route-label" style="background:${visual.color || '#3498db'}20; border-left:4px solid ${visual.color || '#3498db'}">
                             <span style="color:${visual.color || '#3498db'}; font-weight:bold;">${route.name || 'Route ' + (index+1)}</span>
                           </div>`,
                    className: 'route-label-container',
                    iconSize: [140, 35]
                })
            }).addTo(this.layers.group);
        }
        
        // Create popup content
        const popupContent = this.createPopupContent(route, visual.color);
        
        // Add popup to polyline
        polyline.bindPopup(popupContent);
        startMarker.bindPopup(`<strong>🚢 Start:</strong> ${route.name || 'Route ' + (index+1)}<br>${waypoints[0].name || 'Starting point'}`);
        endMarker.bindPopup(`<strong>🎯 Destination:</strong> ${route.name || 'Route ' + (index+1)}<br>${waypoints[waypoints.length-1].name || 'End point'}`);
        
        // Store references
        this.layers[routeId] = {
            polyline: polyline,
            startMarker: startMarker,
            endMarker: endMarker,
            label: labelMarker,
            route: route,
            visible: true
        };
        
        // Add click event for highlighting
        polyline.on('click', (e) => {
            this.highlightRoute(routeId);
            polyline.openPopup();
        });
    },
    
    // Create popup content for route
    createPopupContent: function(route, color) {
        const origin = route.origin || 'Norwegian Coast';
        const destination = route.destination || 'Norwegian Coast';
        const distance = route.total_distance_nm ? route.total_distance_nm.toFixed(1) : 'N/A';
        const waypoints = route.waypoint_count || (route.waypoints ? route.waypoints.length : 0);
        const city = route.source_city ? route.source_city.charAt(0).toUpperCase() + route.source_city.slice(1) : 'Unknown';
        
        return `
            <div class="route-popup">
                <h4 style="color:${color}">${route.name || 'Maritime Route'}</h4>
                <p><strong>🚢 From:</strong> ${origin}</p>
                <p><strong>🎯 To:</strong> ${destination}</p>
                <p><strong>📏 Distance:</strong> ${distance} nautical miles</p>
                <p><strong>📍 Waypoints:</strong> ${waypoints} points</p>
                <p><strong>🏙️ Source:</strong> ${city}</p>
                <div class="color-indicator" style="--route-color:${color}"></div>
            </div>
        `;
    },
    
    // Create control panel
    createControlPanel: function() {
        const panelHtml = `
            <div class="route-control-panel">
                <h4>🛳️ Maritime Routes (${this.routes.length})</h4>
                <div class="route-filter">
                    <input type="text" placeholder="Filter routes by name or city..." id="routeFilterInput">
                </div>
                <div class="route-list" id="routeList">
                    ${this.routes.map((route, index) => this.createRouteItemHtml(route, index)).join('')}
                </div>
                <div class="route-stats">
                    <p><strong>Total Distance:</strong> <span id="totalDistance">${this.calculateTotalDistance().toFixed(1)}</span> NM</p>
                    <p><strong>Total Waypoints:</strong> <span id="totalWaypoints">${this.calculateTotalWaypoints()}</span></p>
                </div>
            </div>
        `;
        
        // Create control panel
        this.controlPanel = L.control({ position: 'topright' });
        this.controlPanel.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'route-control-panel-container');
            div.innerHTML = panelHtml;
            
            // Prevent map click when interacting with panel
            L.DomEvent.disableClickPropagation(div);
            L.DomEvent.disableScrollPropagation(div);
            
            return div;
        };
        
        this.controlPanel.addTo(window.map);
        
        // Add event listeners
        this.setupEventListeners();
        
        console.log('🎛️ Route control panel created');
    },
    
    // Create HTML for route item in control panel
    createRouteItemHtml: function(route, index) {
        const visual = route.visual_properties || {};
        const city = route.source_city ? route.source_city.charAt(0).toUpperCase() + route.source_city.slice(1) : 'Unknown';
        const distance = route.total_distance_nm ? route.total_distance_nm.toFixed(1) : 'N/A';
        const shortName = route.name ? route.name.substring(0, 30) + (route.name.length > 30 ? '...' : '') : `Route ${index+1}`;
        
        return `
            <div class="route-item" data-route-index="${index}">
                <span class="color-dot" style="background-color:${visual.color || '#3498db'}"></span>
                <span class="route-name" title="${route.name || 'Route ' + (index+1)}">${shortName}</span>
                <span class="route-distance">${distance} NM</span>
                <button class="btn-zoom" data-index="${index}" title="Zoom to route">🔍</button>
                <button class="btn-toggle" data-index="${index}" title="Toggle visibility">👁️</button>
            </div>
        `;
    },
    
    // Set up event listeners for control panel
    setupEventListeners: function() {
        setTimeout(() => {
            // Filter input
            const filterInput = document.getElementById('routeFilterInput');
            if (filterInput) {
                filterInput.addEventListener('input', (e) => {
                    this.filterRoutes(e.target.value);
                });
            }
            
            // Zoom buttons
            document.querySelectorAll('.btn-zoom').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const index = parseInt(e.target.getAttribute('data-index'));
                    this.zoomToRoute(index);
                });
            });
            
            // Toggle buttons
            document.querySelectorAll('.btn-toggle').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const index = parseInt(e.target.getAttribute('data-index'));
                    this.toggleRouteVisibility(index);
                    
                    // Update button text
                    const isVisible = this.layers[`route-${index}`]?.visible;
                    btn.textContent = isVisible ? '👁️‍🗨️' : '👁️';
                });
            });
            
            // Route item clicks
            document.querySelectorAll('.route-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('btn-zoom') && !e.target.classList.contains('btn-toggle')) {
                        const index = parseInt(e.currentTarget.getAttribute('data-route-index'));
                        this.highlightRoute(`route-${index}`);
                        this.zoomToRoute(index);
                    }
                });
            });
        }, 100);
    },
    
    // Filter routes by search term
    filterRoutes: function(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        this.currentFilter = term;
        
        // Filter route items in control panel
        const routeItems = document.querySelectorAll('.route-item');
        let visibleCount = 0;
        
        routeItems.forEach(item => {
            const index = parseInt(item.getAttribute('data-route-index'));
            const route = this.routes[index];
            const routeName = (route.name || '').toLowerCase();
            const origin = (route.origin || '').toLowerCase();
            const destination = (route.destination || '').toLowerCase();
            const city = (route.source_city || '').toLowerCase();
            
            const matches = !term || 
                routeName.includes(term) || 
                origin.includes(term) || 
                destination.includes(term) || 
                city.includes(term);
            
            if (matches) {
                item.style.display = 'flex';
                this.showRoute(`route-${index}`);
                visibleCount++;
            } else {
                item.style.display = 'none';
                this.hideRoute(`route-${index}`);
            }
        });
        
        // Update stats
        const statsContainer = document.querySelector('.route-stats');
        if (statsContainer) {
            const visibleRoutes = this.routes.filter((route, index) => {
                const routeName = (route.name || '').toLowerCase();
                const origin = (route.origin || '').toLowerCase();
                const destination = (route.destination || '').toLowerCase();
                const city = (route.source_city || '').toLowerCase();
                
                return !term || 
                    routeName.includes(term) || 
                    origin.includes(term) || 
                    destination.includes(term) || 
                    city.includes(term);
            });
            
            const totalDistance = visibleRoutes.reduce((sum, route) => sum + (route.total_distance_nm || 0), 0);
            const totalWaypoints = visibleRoutes.reduce((sum, route) => sum + (route.waypoint_count || (route.waypoints ? route.waypoints.length : 0)), 0);
            
            document.getElementById('totalDistance').textContent = totalDistance.toFixed(1);
            document.getElementById('totalWaypoints').textContent = totalWaypoints;
        }
        
        console.log(`🔍 Filter: ${visibleCount} routes match "${term}"`);
    },
    
    // Zoom to specific route
    zoomToRoute: function(routeIndex) {
        const routeKey = `route-${routeIndex}`;
        const routeData = this.layers[routeKey];
        
        if (routeData && routeData.route.waypoints) {
            const waypoints = routeData.route.waypoints;
            const bounds = L.latLngBounds(waypoints.map(wp => [wp.lat, wp.lon]));
            window.map.fitBounds(bounds, { padding: [100, 100], maxZoom: 10 });
            
            // Highlight the route
            this.highlightRoute(routeKey);
            
            // Update active item in control panel
            this.setActiveRouteItem(routeIndex);
            
            console.log(`📍 Zoomed to route ${routeIndex}: ${routeData.route.name || 'Unnamed route'}`);
        }
    },
    
    // Highlight a specific route
    highlightRoute: function(routeKey) {
        // Reset all routes to normal style
        Object.keys(this.layers).forEach(key => {
            if (key !== 'group' && this.layers[key] && this.layers[key].polyline) {
                const visual = this.layers[key].route.visual_properties || {};
                this.layers[key].polyline.setStyle({
                    weight: visual.weight || 3,
                    color: visual.color || '#3498db',
                    opacity: visual.opacity || 0.8
                });
                
                // Remove highlight class
                this.layers[key].polyline.getElement().classList.remove('route-selected');
            }
        });
        
        // Highlight selected route
        const selected = this.layers[routeKey];
        if (selected && selected.polyline) {
            const visual = selected.route.visual_properties || {};
            selected.polyline.setStyle({
                weight: visual.highlight_weight || 6,
                color: visual.highlight_color || '#FFFF00',
                opacity: 1
            });
            
            // Bring to front
            selected.polyline.bringToFront();
            
            // Add selection animation
            selected.polyline.getElement().classList.add('route-selected');
            
            // Flash animation
            let flashCount = 0;
            const flashInterval = setInterval(() => {
                const currentOpacity = selected.polyline.options.opacity;
                selected.polyline.setStyle({ 
                    opacity: currentOpacity === 1 ? 0.5 : 1 
                });
                flashCount++;
                if (flashCount >= 6) {
                    clearInterval(flashInterval);
                    selected.polyline.setStyle({ opacity: 1 });
                }
            }, 200);
        }
    },
    
    // Set active route item in control panel
    setActiveRouteItem: function(routeIndex) {
        document.querySelectorAll('.route-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`.route-item[data-route-index="${routeIndex}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    },
    
    // Toggle route visibility
    toggleRouteVisibility: function(routeIndex) {
        const routeKey = `route-${routeIndex}`;
        const routeData = this.layers[routeKey];
        
        if (routeData) {
            const isVisible = routeData.visible;
            
            if (isVisible) {
                this.hideRoute(routeKey);
            } else {
                this.showRoute(routeKey);
            }
            
            routeData.visible = !isVisible;
        }
    },
    
    // Show specific route
    showRoute: function(routeKey) {
        const routeData = this.layers[routeKey];
        if (routeData) {
            if (routeData.polyline) this.layers.group.addLayer(routeData.polyline);
            if (routeData.startMarker) this.layers.group.addLayer(routeData.startMarker);
            if (routeData.endMarker) this.layers.group.addLayer(routeData.endMarker);
            if (routeData.label) this.layers.group.addLayer(routeData.label);
        }
    },
    
    // Hide specific route
    hideRoute: function(routeKey) {
        const routeData = this.layers[routeKey];
        if (routeData) {
            if (routeData.polyline) this.layers.group.removeLayer(routeData.polyline);
            if (routeData.startMarker) this.layers.group.removeLayer(routeData.startMarker);
            if (routeData.endMarker) this.layers.group.removeLayer(routeData.endMarker);
            if (routeData.label) this.layers.group.removeLayer(routeData.label);
        }
    },
    
    // Toggle all routes visibility
    toggleAll: function() {
        this.isVisible = !this.isVisible;
        
        if (this.isVisible) {
            this.layers.group.addTo(window.map);
        } else {
            window.map.removeLayer(this.layers.group);
        }
        
        // Update UI
        const toggleBtn = document.getElementById('rtz-btn');
        if (toggleBtn) {
            toggleBtn.classList.toggle('active', this.isVisible);
        }
        
        console.log(this.isVisible ? '✅ Routes shown' : '🚫 Routes hidden');
    },
    
    // Clear all routes
    clearRoutes: function() {
        if (this.layers.group) {
            window.map.removeLayer(this.layers.group);
        }
        this.layers = {};
    },
    
    // Create legend
    createLegend: function() {
        // Group routes by city and get unique colors
        const cityColors = {};
        this.routes.forEach(route => {
            const city = route.source_city || 'unknown';
            const color = route.visual_properties?.color || '#3498db';
            if (!cityColors[city]) {
                cityColors[city] = {
                    color: color,
                    count: 1
                };
            } else {
                cityColors[city].count++;
            }
        });
        
        // Create legend HTML
        let legendHtml = '';
        Object.entries(cityColors).forEach(([city, data]) => {
            const cityName = city.charAt(0).toUpperCase() + city.slice(1);
            legendHtml += `
                <div class="legend-item">
                    <div class="legend-color" style="background-color:${data.color}"></div>
                    <span class="legend-label">${cityName}</span>
                    <span class="legend-count">${data.count}</span>
                </div>
            `;
        });
        
        // Create legend control
        const legend = L.control({ position: 'bottomright' });
        legend.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'leaflet-control-legend');
            div.innerHTML = `
                <div class="legend-title">Route Cities</div>
                ${legendHtml}
            `;
            
            L.DomEvent.disableClickPropagation(div);
            L.DomEvent.disableScrollPropagation(div);
            
            return div;
        };
        
        legend.addTo(window.map);
        this.layers.legend = legend;
    },
    
    // Calculate total distance of all routes
    calculateTotalDistance: function() {
        return this.routes.reduce((sum, route) => sum + (route.total_distance_nm || 0), 0);
    },
    
    // Calculate total waypoints
    calculateTotalWaypoints: function() {
        return this.routes.reduce((sum, route) => sum + (route.waypoint_count || (route.waypoints ? route.waypoints.length : 0)), 0);
    },
    
    // Update route statistics in dashboard
    updateRouteStats: function() {
        const routeCount = this.routes.length;
        const totalDistance = this.calculateTotalDistance();
        const totalWaypoints = this.calculateTotalWaypoints();
        
        // Update dashboard elements
        const routeCountElement = document.getElementById('route-count');
        if (routeCountElement) {
            routeCountElement.textContent = routeCount;
        }
        
        const routeDisplayElement = document.getElementById('route-display-count');
        if (routeDisplayElement) {
            routeDisplayElement.textContent = routeCount;
        }
        
        const coverageElement = document.getElementById('route-coverage');
        if (coverageElement) {
            const cities = new Set(this.routes.map(r => r.source_city).filter(Boolean));
            coverageElement.textContent = `${cities.size}/10 ports`;
        }
        
        console.log(`📊 Route stats: ${routeCount} routes, ${totalDistance.toFixed(1)} NM, ${totalWaypoints} waypoints`);
    }
};

// Global function to load routes
window.loadEnhancedRTZRoutes = function() {
    console.log('📡 Loading enhanced RTZ routes...');
    
    // Try to get routes from dashboard data first
    if (window.routesData) {
        window.rtzManager.init(window.routesData);
        return;
    }
    
    // Fallback: Fetch from API
    fetch('/maritime/api/rtz/routes/enhanced')
        .then(response => response.json())
        .then(data => {
            if (data.routes && data.routes.length > 0) {
                window.rtzManager.init(data.routes);
            } else {
                console.warn('No routes returned from API');
            }
        })
        .catch(error => {
            console.error('Error loading RTZ routes:', error);
        });
};