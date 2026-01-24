/* backend/static/js/split/fix_dancing_markers.js */
/**
 * FIX FOR DANCING ROUTE MARKERS
 * Stops start/end/waypoint markers from moving around on the map
 */

(function() {
    console.log('📍 FIXING DANCING ROUTE MARKERS');
    
    // Wait for map to load
    const waitForMap = setInterval(() => {
        if (window.map && document.getElementById('maritime-map')) {
            clearInterval(waitForMap);
            applyMarkerFix();
        }
    }, 500);
    
    function applyMarkerFix() {
        console.log('✅ Map loaded, applying marker fix...');
        
        // CSS FIX: Force markers to stay still
        const markerStyles = document.createElement('style');
        markerStyles.id = 'dancing-markers-fix';
        markerStyles.textContent = `
            /* === ABSOLUTE FIX FOR DANCING MARKERS === */
            /* This overrides any animation/transition on markers */
            
            /* Target all route-related markers */
            .route-start-marker,
            .route-end-marker,
            .route-waypoint-marker,
            .rtz-marker,
            [class*="marker"][class*="route"],
            .leaflet-marker-icon[class*="route"],
            .leaflet-div-icon[class*="route"] {
                /* KILL ALL ANIMATIONS */
                animation: none !important;
                -webkit-animation: none !important;
                animation-name: none !important;
                animation-duration: 0s !important;
                animation-iteration-count: 1 !important;
                animation-play-state: paused !important;
                animation-delay: -999999s !important;
                
                /* KILL ALL TRANSITIONS */
                transition: none !important;
                -webkit-transition: none !important;
                transition-property: none !important;
                transition-duration: 0s !important;
                
                /* LOCK POSITION - NO MOVEMENT */
                transform: none !important;
                -webkit-transform: none !important;
                transform-origin: center !important;
                
                /* FIXED SIZE AND POSITION */
                width: 12px !important;
                height: 12px !important;
                margin-left: -6px !important;
                margin-top: -6px !important;
                
                /* PREVENT ANY CHANGES */
                will-change: auto !important;
                position: absolute !important;
            }
            
            /* Specific colors for each marker type */
            .route-start-marker {
                background-color: #28a745 !important;
                border: 2px solid white !important;
                box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.3) !important;
            }
            
            .route-end-marker {
                background-color: #dc3545 !important;
                border: 2px solid white !important;
                box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.3) !important;
            }
            
            .route-waypoint-marker {
                background-color: #007bff !important;
                border: 2px solid white !important;
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3) !important;
            }
            
            /* Also fix any parent containers */
            .leaflet-marker-pane,
            .leaflet-overlay-pane {
                animation: none !important;
                transition: none !important;
            }
        `;
        document.head.appendChild(markerStyles);
        
        // JavaScript FIX: Freeze existing markers
        setTimeout(() => {
            const markers = document.querySelectorAll(`
                .route-start-marker,
                .route-end-marker,
                .route-waypoint-marker,
                .leaflet-marker-icon
            `);
            
            markers.forEach(marker => {
                // Freeze transform
                marker.style.transform = 'none';
                marker.style.webkitTransform = 'none';
                
                // Remove any animation classes
                marker.classList.remove('pulse');
                marker.classList.remove('rtz-pulse');
                marker.classList.remove('animated');
                
                // Add static class
                marker.classList.add('marker-static');
            });
            
            console.log(`✅ Fixed ${markers.length} markers`);
            
            // Watch for new markers being added
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1 && 
                            (node.classList?.contains('leaflet-marker-icon') ||
                             node.classList?.contains('route-start-marker') ||
                             node.classList?.contains('route-end-marker'))) {
                            
                            // Apply fixes to new markers
                            node.style.transform = 'none';
                            node.style.animation = 'none';
                            node.style.transition = 'none';
                            console.log('📍 Fixed newly added marker');
                        }
                    });
                });
            });
            
            observer.observe(document.getElementById('maritime-map'), {
                childList: true,
                subtree: true
            });
            
        }, 1000);
        
        console.log('✅ Dancing markers fix applied');
    }
    
    // Also patch Leaflet's marker creation if possible
    if (window.L && L.Marker) {
        const originalSetIcon = L.Marker.prototype.setIcon;
        L.Marker.prototype.setIcon = function(icon) {
            const result = originalSetIcon.call(this, icon);
            
            // After icon is set, remove animations
            if (this._icon) {
                this._icon.style.animation = 'none';
                this._icon.style.transition = 'none';
                this._icon.style.transform = 'none';
            }
            
            return result;
        };
        
        console.log('✅ Patched Leaflet Marker class');
    }
})();