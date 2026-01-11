// backend/static/js/split/rtz_routes_fixed.js
// Fixed RTZ route manager with accurate waypoint positioning

(function() {
    window.rtzManager = {
        routes: [],
        mapLayers: {},
        isVisible: true,
        
        init: function(routesData) {
            console.log('🎯 Fixed RTZ Manager initialized');
            this.routes = routesData || [];
            
            if (this.routes.length > 0) {
                console.log(`📊 Processing ${this.routes.length} routes`);
                this.renderAllRoutes();
            }
        },
        
        renderAllRoutes: function() {
            if (!window.map) {
                console.error('Map not available');
                return;
            }
            
            // Clear existing
            this.clearRoutes();
            
            // Create layer group
            this.mapLayers.group = L.layerGroup().addTo(window.map);
            
            // Render each route
            this.routes.forEach((route, index) => {
                this.renderRoute(route, index);
            });
            
            console.log(`✅ Rendered ${this.routes.length} routes`);
        },
        
        renderRoute: function(route, index) {
            const waypoints = route.waypoints || [];
            if (waypoints.length < 2) {
                console.warn(`Route ${index} has insufficient waypoints`);
                return;
            }
            
            const routeId = `route-${index}`;
            const color = this.getRouteColor(index);
            
            // Convert waypoints to LatLng array - EXACT coordinates
            const latlngs = waypoints.map(wp => {
                const lat = parseFloat(wp.lat);
                const lon = parseFloat(wp.lon);
                return [lat, lon];
            });
            
            // Create polyline with EXACT waypoints
            const polyline = L.polyline(latlngs, {
                color: color,
                weight: 2,
                opacity: 0.7,
                lineCap: 'round',
                lineJoin: 'round'
            }).addTo(this.mapLayers.group);
            
            // Create start marker - EXACT first waypoint
            const startMarker = L.circleMarker(latlngs[0], {
                color: '#28a745',
                fillColor: '#28a745',
                radius: 6,
                fillOpacity: 1,
                weight: 2
            }).addTo(this.mapLayers.group);
            
            // Create end marker - EXACT last waypoint
            const endMarker = L.circleMarker(latlngs[latlngs.length - 1], {
                color: '#dc3545',
                fillColor: '#dc3545',
                radius: 7,
                fillOpacity: 1,
                weight: 2
            }).addTo(this.mapLayers.group);
            
            // Create intermediate markers
            const waypointMarkers = [];
            if (waypoints.length > 2) {
                for (let i = 1; i < waypoints.length - 1; i++) {
                    const wp = waypoints[i];
                    const marker = L.circleMarker([wp.lat, wp.lon], {
                        color: '#007bff',
                        fillColor: '#007bff',
                        radius: 4,
                        fillOpacity: 0.8,
                        weight: 1
                    }).addTo(this.mapLayers.group);
                    waypointMarkers.push(marker);
                }
            }
            
            // Popup content
            const popupContent = `
                <div style="min-width: 180px;">
                    <h6 style="color: ${color}; margin: 0 0 8px 0;">
                        <i class="fas fa-route"></i> ${route.name || `Route ${index + 1}`}
                    </h6>
                    <p style="margin: 4px 0; font-size: 12px;">
                        <strong>Start:</strong> ${latlngs[0][0].toFixed(4)}, ${latlngs[0][1].toFixed(4)}
                    </p>
                    <p style="margin: 4px 0; font-size: 12px;">
                        <strong>End:</strong> ${latlngs[latlngs.length - 1][0].toFixed(4)}, ${latlngs[latlngs.length - 1][1].toFixed(4)}
                    </p>
                    <p style="margin: 4px 0; font-size: 12px;">
                        <strong>Points:</strong> ${waypoints.length}
                    </p>
                </div>
            `;
            
            polyline.bindPopup(popupContent);
            
            // Store references
            this.mapLayers[routeId] = {
                polyline: polyline,
                startMarker: startMarker,
                endMarker: endMarker,
                waypointMarkers: waypointMarkers,
                route: route,
                bounds: L.latLngBounds(latlngs)
            };
        },
        
        getRouteColor: function(index) {
            const colors = ['#1a2980', '#26d0ce', '#ff6b6b', '#4ECDC4', '#45B7D1', '#96CEB4'];
            return colors[index % colors.length];
        },
        
        toggleAll: function() {
            this.isVisible = !this.isVisible;
            
            if (this.mapLayers.group) {
                if (this.isVisible) {
                    this.mapLayers.group.addTo(window.map);
                } else {
                    window.map.removeLayer(this.mapLayers.group);
                }
            }
            
            // Update button
            const btn = document.getElementById('rtz-btn');
            if (btn) {
                btn.classList.toggle('active', this.isVisible);
            }
        },
        
        zoomToRoute: function(routeIndex) {
            const routeKey = `route-${routeIndex}`;
            const routeData = this.mapLayers[routeKey];
            
            if (routeData && routeData.bounds) {
                window.map.fitBounds(routeData.bounds, { padding: [50, 50] });
            }
        },
        
        clearRoutes: function() {
            if (this.mapLayers.group && window.map) {
                window.map.removeLayer(this.mapLayers.group);
            }
            this.mapLayers = {};
        }
    };
    
    // Global loader
    window.loadRTZRoutesFixed = function() {
        console.log('🔄 Loading RTZ routes...');
        
        try {
            const routesDataElement = document.getElementById('routes-data');
            if (routesDataElement && routesDataElement.textContent) {
                const routesData = JSON.parse(routesDataElement.textContent);
                if (routesData.length > 0) {
                    window.rtzManager.init(routesData);
                    return;
                }
            }
        } catch (error) {
            console.error('Failed to parse routes:', error);
        }
        
        // Fallback API call
        fetch('/maritime/api/rtz/routes')
            .then(response => response.json())
            .then(data => {
                if (data.routes && data.routes.length > 0) {
                    window.rtzManager.init(data.routes);
                }
            })
            .catch(error => console.error('API fallback failed:', error));
    };
})();