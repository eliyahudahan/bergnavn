// static/js/split/maritime_weather.js
// Weather-specific helpers (stub)

(function () {
    window.MARITIME_WEATHER = window.MARITIME_WEATHER || {};
    window.MARITIME_WEATHER.iconForCondition = function(code) {
        // simple mapping
        const map = { 'rain': '🌧️', 'clear': '☀️', 'cloudy': '☁️' };
        return map[code] || '🌊';
    };
})();
