/* backend/static/js/split/ais_performance.js */
/**
 * Performance optimizations for AIS display - Stops map flickering completely
 */

(function() {
    console.log('🎯 Applying AIS performance optimizations');
    
    // Patch the aisManager to be completely passive
    const originalStartUpdates = window.aisManager?.startRealTimeUpdates;
    
    if (window.aisManager && originalStartUpdates) {
        // Replace with passive version
        window.aisManager.startRealTimeUpdates = function() {
            console.log('⚠️ AIS updates in passive mode (no auto-refresh)');
            return this;
        };
        
        // Make fetch function manual only
        const originalFetch = window.aisManager.fetchRealTimeVessels;
        window.aisManager.fetchRealTimeVessels = function() {
            console.log('🔄 Manual AIS refresh');
            return originalFetch.call(this);
        };
        
        console.log('✅ AIS Manager patched to passive mode');
    }
    
    // Add CSS to freeze all AIS-related animations
    const style = document.createElement('style');
    style.textContent = `
        /* Freeze all AIS-related animations */
        .vessel-marker,
        .leaflet-marker-icon,
        .ais-layer * {
            animation: none !important;
            transition: none !important;
            transition-duration: 0s !important;
        }
        
        /* Prevent map container updates */
        #maritime-map .leaflet-marker-pane,
        #maritime-map .leaflet-overlay-pane {
            will-change: auto !important;
        }
    `;
    document.head.appendChild(style);
})();