// static/js/split/maritime_map.js
// Additional map utilities (stub)

(function () {
    window.MARITIME_MAP = window.MARITIME_MAP || {};
    window.MARITIME_MAP.flyTo = function (lat, lon, zoom=10) {
        if (window.map) {
            window.map.setView([lat, lon], zoom);
        }
    };
})();
