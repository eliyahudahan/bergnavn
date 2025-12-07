# backend/services/fuel_optimizer_service.py
# English-only comments inside file as requested.
import math
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ================================
# EMPIRICAL CUBIC PROPULSION MODEL
# ================================
def cubic_fuel_consumption(speed_knots: float, displacement_tons: float = 8000.0) -> float:
    """
    Empirical cubic model: fuel approx = k * v^3 scaled by displacement.
    Returns fuel consumption in metric tons per hour (approx).
    """
    try:
        speed = float(speed_knots or 0.0)
        if speed <= 0.0:
            return 0.0

        # Empirical constant calibrated for coastal vessels
        k = 0.000045
        consumption = k * (speed ** 3) * (displacement_tons / 8000.0)
        return round(consumption, 6)
    except Exception as e:
        logger.exception("[cubic_fuel_consumption] error")
        return 0.0

# ==============================================
# MAIN OPTIMIZER (ASYNC)
# ==============================================
async def optimize_vessel_async(ais: dict, weather: dict) -> dict:
    """
    Async optimizer using cubic propulsion model.
    Always returns safe values and does not raise.
    Designed to be imported by routes (synchronous or async).
    """
    try:
        # Defaults and safe parsing
        speed = float(ais.get("sog", 0) or 0.0)
        if speed <= 0:
            # use a sensible default operational speed
            speed = 10.0

        displacement = float(ais.get("displacement_tons", 8000) or 8000.0)

        wind_speed = float(weather.get("wind_speed", 0) or 0.0)
        wind_dir = float(weather.get("wind_direction", 0) or 0.0)

        # -------------- WIND IMPACT (empirical) --------------
        # Headwind increases effective resistance; tailwind reduces.
        # Simple sign-based factor:
        try:
            if 0 <= (wind_dir % 360) <= 90 or 270 <= (wind_dir % 360) <= 360:
                wind_factor = 1.0 + (0.03 * wind_speed)  # headwind penalty
            else:
                wind_factor = 1.0 - (0.015 * wind_speed)  # tailwind benefit
        except Exception:
            wind_factor = 1.0

        # Clamp wind factor to reasonable bounds
        wind_factor = max(0.85, min(wind_factor, 1.25))

        # -------------- FUEL EVALUATION --------------
        current_fuel_tons = cubic_fuel_consumption(speed, displacement) * wind_factor

        # recommended optimal speed (simple empirical rule - keep within safe band)
        # Use cubic model insight: small reductions in speed give larger fuel savings.
        # Start by nudging speed toward an empirical optimal range.
        optimal_speed = speed

        # If vessel is above typical optimal range, reduce
        if speed > 13.0:
            optimal_speed = speed - 1.5
        elif speed > 11.0:
            optimal_speed = speed - 0.8
        elif speed < 8.0:
            optimal_speed = speed + 1.0  # bring slow ships up to efficient band

        # Adjust optimal speed further by wind_factor (headwind -> reduce speed)
        if wind_factor > 1.10:
            optimal_speed -= 0.8
        elif wind_factor < 0.95:
            optimal_speed += 0.4

        # Clamp to safety bounds
        optimal_speed = max(6.0, min(optimal_speed, 16.0))

        optimized_fuel_tons = cubic_fuel_consumption(optimal_speed, displacement) * wind_factor

        # Compute percent saving (safe math)
        if current_fuel_tons > 0:
            fuel_saving_percent = round(100.0 * (1.0 - (optimized_fuel_tons / current_fuel_tons)), 2)
        else:
            fuel_saving_percent = 0.0

        return {
            "status": "ok",
            "model": "cubic_propulsion",
            "current_speed_knots": round(speed, 2),
            "optimal_speed_knots": round(optimal_speed, 2),
            "fuel_tons_current": round(current_fuel_tons, 6),
            "fuel_tons_optimal": round(optimized_fuel_tons, 6),
            "fuel_saving_percent": fuel_saving_percent,
            "wind_factor": round(wind_factor, 4),
            "timestamp": datetime.now().isoformat(),
            "fallback_used": False
        }

    except Exception as e:
        logger.exception("[optimize_vessel_async] SAFE FALLBACK")
        # Safe fallback payload, never raises
        return {
            "status": "fallback",
            "current_speed_knots": float(ais.get("sog", 0) or 0.0),
            "optimal_speed_knots": float(ais.get("sog", 0) or 0.0),
            "fuel_tons_current": 0.0,
            "fuel_tons_optimal": 0.0,
            "fuel_saving_percent": 0.0,
            "timestamp": datetime.now().isoformat(),
            "fallback_used": True
        }
