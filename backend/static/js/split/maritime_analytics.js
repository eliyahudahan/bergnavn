// static/js/split/maritime_analytics.js
// Analytics stubs — can be extended later.

(function () {
    window.MARITIME_ANALYTICS = window.MARITIME_ANALYTICS || {};
    window.MARITIME_ANALYTICS.computeFuelSaving = function(speed, optimal=12) {
        const dev = Math.abs(speed - optimal);
        return Math.max(0, Math.round(100 - dev*8));
    };
})();
