// static/js/split/maritime_core.js
// Core helpers for maritime dashboard (module stub)

(function () {
    // Expose simple helpers on window.MARITIME_CORE
    window.MARITIME_CORE = window.MARITIME_CORE || {};
    window.MARITIME_CORE.formatLatLon = function (lat, lon) {
        return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
    };
})();
