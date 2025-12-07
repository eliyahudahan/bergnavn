def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_fuel_optimization(vessels):
    """
    Safe fuel optimization calculator that will NEVER throw a 500.
    """
    try:
        results = []
        for v in vessels:
            speed = safe_float(v.get("speed"), 0.0)
            fuel_rate = safe_float(v.get("fuel_rate"), 0.0)
            efficiency = safe_float(v.get("efficiency"), 90.0)

            if speed <= 0:
                impact = 0
                savings = 0
            else:
                # simplified formula
                impact = max(0, 100 - efficiency)
                savings = impact * 0.12

            results.append({
                "mmsi": v.get("mmsi"),
                "impact": impact,
                "savings": savings,
                "status": "ok"
            })

        return {
            "total_vessels": len(results),
            "items": results,
            "summary": {
                "avg_savings": round(sum(r["savings"] for r in results) / (len(results) or 1), 2)
            }
        }

    except Exception as e:
        return {
            "error": True,
            "message": f"Fuel optimization internal error: {str(e)}"
        }
