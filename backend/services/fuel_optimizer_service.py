# backend/services/fuel_optimizer_service.py
import logging
from typing import Any, Dict
from backend.services.async_executor import run_in_threadpool
from backend.ml.enhanced_fuel_optimizer import EnhancedFuelOptimizer

logger = logging.getLogger(__name__)

async def optimize_vessel_async(vessel_data: Dict[str, Any], weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """Asynchronously run EnhancedFuelOptimizer and return results."""
    try:
        optimizer = EnhancedFuelOptimizer()
        result = await run_in_threadpool(
            optimizer.calculate_optimal_speed_profile,
            vessel_data,
            weather_data
        )
        logger.info("✅ Fuel optimization completed successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Error during fuel optimization: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
