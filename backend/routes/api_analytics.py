@analytics_bp.route("/fuel-optimization")
def fuel_optimization():
    try:
        vessels = ais_service.get_all_cached() or []
        data = compute_fuel_optimization(vessels)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": True, "details": str(e)}), 200
