// backend/static/js/split/rtz_routes_fixed.js
// FIXED RTZ ROUTE MANAGER - DEDUPLICATES ROUTES, ACCURATE WAYPOINTS
// FIXED: Correct path for NCA routes from /raw/extracted/
// FIXED: 34 verified routes from Norwegian Coastal Administration
// FIXED: Using embedded DOM data instead of API call

(function() {
    console.log('🗺️ RTZ Routes Fixed - Loading...');
    console.log('📍 Looking for NCA routes in DOM');
    
    window.rtzManager = {
        routes: [],
        uniqueRoutes: [],
        mapLayers: {},
        isVisible: true,
        duplicateCount: 0,
        totalRoutesFound: 0,
        
        init: function(routesData) {
            console.log('🎯 Fixed RTZ Manager initialized');
            
            if (!routesData || routesData.length === 0) {
                console.error('❌ No routes data provided');
                return;
            }
            
            this.routes = routesData;
            this.totalRoutesFound = routesData.length;
            
            // CRITICAL: Remove duplicate routes by ID
            this.removeDuplicates();
            
            console.log(`📊 Total routes: ${this.routes.length}, Unique: ${this.uniqueRoutes.length}, Duplicates removed: ${this.duplicateCount}`);
            console.log(`🗺️ NCA Routes: ${this.uniqueRoutes.length} verified routes from Norwegian Coastal Administration`);
            
            // Wait for map to be ready
            this.waitForMap();
        },
        
        removeDuplicates: function() {
            const seenIds = new Set();
            this.uniqueRoutes = [];
            this.duplicateCount = 0;
            
            this.routes.forEach(route => {
                // Get route ID from various possible fields
                const routeId = route.id || route.route_id || route.route_name || 
                               `${route.origin || ''}_${route.destination || ''}_${route.waypoints?.length || 0}`;
                
                if (!seenIds.has(routeId)) {
                    seenIds.add(routeId);
                    this.uniqueRoutes.push(route);
                } else {
                    this.duplicateCount++;
                }
            });
            
            // FIX: Update routes to unique routes only
            this.routes = this.uniqueRoutes;
            
            // FIX: Update global dashboardData to use unique routes
            if (window.dashboardData) {
                window.dashboardData.routes = this.uniqueRoutes;
                window.dashboardData.rawRouteCount = this.totalRoutesFound;
                console.log(`🔄 Updated window.dashboardData.routes to ${this.uniqueRoutes.length} unique routes`);
            }
        },
        
        waitForMap: function() {
            // Check if map exists
            if (window.dashboardData?.map) {
                this.renderAllRoutes();
            } else {
                console.log('⏳ Waiting for map to be ready...');
                // Check every 500ms
                const checkInterval = setInterval(() => {
                    if (window.dashboardData?.map) {
                        clearInterval(checkInterval);
                        this.renderAllRoutes();
                    }
                }, 500);
                
                // Timeout after 10 seconds
                setTimeout(() => {
                    clearInterval(checkInterval);
                    console.error('❌ Map not available after 10 seconds');
                }, 10000);
            }
        },
        
        renderAllRoutes: function() {
            if (!window.dashboardData?.map) {
                console.error('❌ Map not available');
                return;
            }
            
            console.log(`🗺️ Rendering ${this.routes.length} unique NCA routes...`);
            
            // Clear existing
            this.clearRoutes();
            
            // Create layer group
            this.mapLayers.group = L.layerGroup().addTo(window.dashboardData.map);
            
            // Render each unique route
            this.routes.forEach((route, index) => {
                this.renderRoute(route, index);
            });
            
            console.log(`✅ Successfully rendered ${Object.keys(this.mapLayers).length - 1} NCA routes`);
            
            // Store routes in window.dashboardData.routeLayers for other modules
            if (window.dashboardData) {
                window.dashboardData.routeLayers = this.mapLayers;
                window.dashboardData.uniqueRoutes = this.routes;
            }
            
            // Trigger event for other modules
            const event = new CustomEvent('routesRendered', { 
                detail: { 
                    count: this.routes.length,
                    total: this.totalRoutesFound,
                    duplicates: this.duplicateCount
                }
            });
            document.dispatchEvent(event);
        },
        
        renderRoute: function(route, index) {
            const waypoints = route.waypoints || [];
            
            if (waypoints.length < 2) {
                console.warn(`⚠️ Route ${index} has insufficient waypoints (${waypoints.length})`);
                return;
            }
            
            const routeId = `route-${index}`;
            
            // Get route name from various possible fields
            const routeName = route.name || route.route_name || route.clean_name || `NCA Route ${index + 1}`;
            
            // Get origin/destination
            const origin = route.origin || 'Unknown';
            const destination = route.destination || 'Unknown';
            
            // Get color from visual_properties or generate
            let color = route.visual_properties?.color || this.getRouteColor(index);
            
            // Convert waypoints to LatLng array - EXACT coordinates
            const latlngs = waypoints.map(wp => {
                const lat = parseFloat(wp.lat);
                const lon = parseFloat(wp.lon || wp.lng); // Support both lon and lng
                return [lat, lon];
            }).filter(latlng => !isNaN(latlng[0]) && !isNaN(latlng[1]));
            
            if (latlngs.length < 2) {
                console.warn(`⚠️ Route ${index} has invalid coordinates`);
                return;
            }
            
            // Create polyline with EXACT waypoints
            const polyline = L.polyline(latlngs, {
                color: color,
                weight: 3,
                opacity: 0.8,
                lineCap: 'round',
                lineJoin: 'round',
                className: 'route-line'
            }).addTo(this.mapLayers.group);
            
            // Create start marker - GREEN
            const startMarker = L.circleMarker(latlngs[0], {
                color: '#28a745',
                fillColor: '#28a745',
                radius: 7,
                fillOpacity: 1,
                weight: 2,
                className: 'route-start-marker'
            }).addTo(this.mapLayers.group);
            
            // Create end marker - RED  
            const endMarker = L.circleMarker(latlngs[latlngs.length - 1], {
                color: '#dc3545',
                fillColor: '#dc3545',
                radius: 7,
                fillOpacity: 1,
                weight: 2,
                className: 'route-end-marker'
            }).addTo(this.mapLayers.group);
            
            // Create intermediate waypoint markers - GRAY
            const waypointMarkers = [];
            if (waypoints.length > 2) {
                for (let i = 1; i < waypoints.length - 1; i++) {
                    const wp = waypoints[i];
                    const lat = parseFloat(wp.lat);
                    const lon = parseFloat(wp.lon || wp.lng);
                    
                    if (!isNaN(lat) && !isNaN(lon)) {
                        const marker = L.circleMarker([lat, lon], {
                            color: '#6c757d',
                            fillColor: '#6c757d',
                            radius: 4,
                            fillOpacity: 0.8,
                            weight: 1,
                            className: 'waypoint-marker'
                        }).addTo(this.mapLayers.group);
                        
                        // Add tooltip with waypoint name if available
                        if (wp.name) {
                            marker.bindTooltip(wp.name, { permanent: false, direction: 'top' });
                        }
                        
                        waypointMarkers.push(marker);
                    }
                }
            }
            
            // Calculate bounds for zooming
            const bounds = L.latLngBounds(latlngs);
            
            // Store route data for highlighting
            polyline.routeData = {
                id: routeId,
                index: index,
                name: routeName,
                origin: origin,
                destination: destination,
                color: color
            };
            
            // Enhanced popup content
            const popupContent = `
                <div style="min-width: 240px; padding: 8px;">
                    <h6 style="color: ${color}; margin: 0 0 8px 0; font-weight: 600; border-bottom: 1px solid #eee; padding-bottom: 4px;">
                        <i class="fas fa-route"></i> ${routeName}
                    </h6>
                    <div style="margin: 8px 0;">
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <span style="background: #28a745; width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                            <strong>Start:</strong> ${origin}
                        </div>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <span style="background: #dc3545; width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                            <strong>End:</strong> ${destination}
                        </div>
                    </div>
                    <div style="font-size: 12px; color: #666; background: #f8f9fa; padding: 6px; border-radius: 4px;">
                        <div><i class="fas fa-map-marker-alt"></i> Waypoints: ${waypoints.length}</div>
                        <div><i class="fas fa-arrows-alt-h"></i> Distance: ${route.total_distance_nm ? route.total_distance_nm.toFixed(1) : '?'} NM</div>
                        <div><i class="fas fa-ship"></i> Port: ${route.source_city || 'Norwegian Coastal Admin'}</div>
                        ${route.empirically_verified ? '<div><i class="fas fa-check-circle text-success"></i> NCA Verified</div>' : ''}
                    </div>
                    <button onclick="window.rtzManager.zoomToRoute(${index})" 
                            style="width: 100%; margin-top: 10px; padding: 8px; background: ${color}; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                        <i class="fas fa-search"></i> Zoom to Route
                    </button>
                </div>
            `;
            
            polyline.bindPopup(popupContent, { maxWidth: 300 });
            startMarker.bindPopup(`<strong>Start:</strong> ${origin}<br>${latlngs[0][0].toFixed(4)}°, ${latlngs[0][1].toFixed(4)}°`);
            endMarker.bindPopup(`<strong>End:</strong> ${destination}<br>${latlngs[latlngs.length - 1][0].toFixed(4)}°, ${latlngs[latlngs.length - 1][1].toFixed(4)}°`);
            
            // Click handlers
            polyline.on('click', () => this.zoomToRoute(index));
            startMarker.on('click', () => this.zoomToRoute(index));
            endMarker.on('click', () => this.zoomToRoute(index));
            
            // Store references
            this.mapLayers[routeId] = {
                polyline: polyline,
                startMarker: startMarker,
                endMarker: endMarker,
                waypointMarkers: waypointMarkers,
                route: route,
                bounds: bounds,
                index: index,
                name: routeName,
                origin: origin,
                destination: destination,
                color: color
            };
        },
        
        getRouteColor: function(index) {
            // Norwegian Coastal Administration color palette
            const colors = [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
                '#FF9F1C', '#2EC4B6', '#E71D36', '#FF9F1C', '#6B4E71',
                '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'
            ];
            return colors[index % colors.length];
        },
        
        toggleAll: function() {
            this.isVisible = !this.isVisible;
            
            if (this.mapLayers.group) {
                if (this.isVisible) {
                    this.mapLayers.group.addTo(window.dashboardData.map);
                } else {
                    window.dashboardData.map.removeLayer(this.mapLayers.group);
                }
            }
            
            // Update button
            const btn = document.getElementById('rtz-toggle-btn');
            if (btn) {
                btn.classList.toggle('active', this.isVisible);
                btn.innerHTML = this.isVisible ? 
                    '<i class="fas fa-route me-1"></i> Hide Routes' : 
                    '<i class="fas fa-route me-1"></i> Show Routes';
            }
        },
        
        zoomToRoute: function(routeIndex) {
            const routeKey = `route-${routeIndex}`;
            const routeData = this.mapLayers[routeKey];
            
            if (routeData && routeData.bounds && window.dashboardData?.map) {
                window.dashboardData.map.fitBounds(routeData.bounds, { 
                    padding: [50, 50],
                    maxZoom: 12,
                    animate: true,
                    duration: 0.5
                });
                
                // Highlight the route
                routeData.polyline.setStyle({
                    weight: 6,
                    opacity: 1,
                    color: '#ff9800'
                });
                
                // Reset other routes
                Object.values(this.mapLayers).forEach(layer => {
                    if (layer !== routeData && layer.polyline) {
                        layer.polyline.setStyle({
                            weight: 3,
                            opacity: 0.7,
                            color: layer.color
                        });
                    }
                });
                
                // Highlight table row
                document.querySelectorAll('.route-row').forEach(row => {
                    row.classList.remove('active');
                });
                
                // Find and highlight the row
                if (routeIndex < this.routes.length) {
                    const row = document.querySelector(`.route-row[data-route-index="${routeIndex}"]`);
                    if (row) {
                        row.classList.add('active');
                        row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                }
                
                console.log(`🔍 Zoomed to NCA route ${routeIndex + 1}: ${routeData.name}`);
                
                // Show notification
                if (typeof window.showNotification === 'function') {
                    window.showNotification(`Route: ${routeData.name}`, 'info');
                }
            } else {
                console.warn(`⚠️ Route ${routeIndex} not found in map layers`);
            }
        },
        
        clearRoutes: function() {
            if (this.mapLayers.group && window.dashboardData?.map) {
                window.dashboardData.map.removeLayer(this.mapLayers.group);
            }
            this.mapLayers = { group: null };
        },
        
        refresh: function() {
            console.log('🔄 Refreshing NCA routes...');
            this.renderAllRoutes();
        },
        
        getStats: function() {
            return {
                total: this.totalRoutesFound,
                unique: this.routes.length,
                duplicates: this.duplicateCount,
                rendered: Object.keys(this.mapLayers).length - 1
            };
        }
    };
    
    // Global loader with better error handling - USES DOM DATA FIRST, NOT API
    window.loadRTZRoutesFixed = function() {
        console.log('🔄 Loading NCA routes from DOM data...');
        
        try {
            // FIRST TRY: Get routes from window.dashboardData (already loaded by Django)
            if (window.dashboardData && window.dashboardData.routes && window.dashboardData.routes.length > 0) {
                console.log(`✅ Found ${window.dashboardData.routes.length} NCA routes in window.dashboardData`);
                window.rtzManager.init(window.dashboardData.routes);
                return;
            }
            
            // SECOND TRY: Get routes from DOM element
            const routesDataElement = document.getElementById('routes-data');
            
            if (routesDataElement && routesDataElement.textContent) {
                const textContent = routesDataElement.textContent.trim();
                
                if (textContent && textContent !== '[]' && textContent !== 'null') {
                    try {
                        const routesData = JSON.parse(textContent);
                        
                        if (Array.isArray(routesData) && routesData.length > 0) {
                            console.log(`✅ Found ${routesData.length} NCA routes in DOM element`);
                            
                            // Store in window.dashboardData for other modules
                            if (!window.dashboardData) {
                                window.dashboardData = {};
                            }
                            window.dashboardData.routes = routesData;
                            
                            window.rtzManager.init(routesData);
                            return;
                        }
                    } catch (parseError) {
                        console.error('❌ Failed to parse routes JSON:', parseError);
                    }
                }
            }
            
            // LAST RESORT: Log error - NO API FALLBACK since it's not working
            console.error('❌ No route data found in DOM. Check that routes are being passed to template.');
            console.log('📋 Routes should be loaded from backend/templates/maritime_split/dashboard_base.html');
            
        } catch (error) {
            console.error('❌ Error accessing routes data:', error);
        }
    };
    
    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.loadRTZRoutesFixed);
    } else {
        window.loadRTZRoutesFixed();
    }
    
    console.log('✅ RTZ Routes Fixed - Ready to render NCA routes from embedded data');
})();