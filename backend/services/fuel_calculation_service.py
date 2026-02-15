# backend/services/fuel_calculation_service.py
"""
Advanced fuel consumption calculator with weather integration.
Uses cubic law with wind and wave resistance factors.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def calculate_realistic_fuel_consumption(
    speed_knots: float, 
    displacement_tons: float = 8000.0,
    wind_speed_ms: float = 0.0,
    wind_direction_deg: float = 0.0,
    wave_height_m: float = 0.0,
    vessel_heading_deg: float = 0.0
) -> Dict[str, Any]:
    """
    Calculate realistic fuel consumption with weather effects.
    
    Based on maritime engineering principles:
    1. Cubic law for base consumption: Fuel ∝ Speed^3
    2. Wind resistance: Headwind increases consumption
    3. Wave resistance: Higher waves increase resistance significantly
    """
    
    # 1. Base consumption (cubic law)
    k_base = 0.000045  # Empirical coefficient
    base_consumption_t_h = k_base * (speed_knots ** 3) * (displacement_tons / 8000.0)
    
    # 2. Calculate relative wind angle (0° = headwind, 180° = tailwind)
    relative_wind_angle = abs((wind_direction_deg - vessel_heading_deg + 180) % 360 - 180)
    
    # 3. Wind resistance factor (empirical formula)
    # Headwind (0-90°) has strongest effect
    if relative_wind_angle <= 90:
        wind_factor = 1.0 + (wind_speed_ms * 0.04)  # 4% increase per m/s for headwind
    elif relative_wind_angle <= 150:
        wind_factor = 1.0 + (wind_speed_ms * 0.02)  # 2% for beam wind
    else:
        wind_factor = 1.0 - (wind_speed_ms * 0.01)  # 1% reduction for tailwind
    
    wind_factor = max(0.85, min(wind_factor, 1.3))  # Bound between 0.85 and 1.3
    
    # 4. Wave resistance factor (significant effect!)
    if wave_height_m <= 0.5:
        wave_factor = 1.0  # Calm sea
    elif wave_height_m <= 1.5:
        wave_factor = 1.0 + (wave_height_m - 0.5) * 0.15  # 15% per meter
    elif wave_height_m <= 3.0:
        wave_factor = 1.15 + (wave_height_m - 1.5) * 0.25  # 25% per meter
    else:
        wave_factor = 1.525 + (wave_height_m - 3.0) * 0.4  # 40% per meter for rough seas
    
    # 5. Calculate total adjusted consumption
    adjusted_consumption_t_h = base_consumption_t_h * wind_factor * wave_factor
    
    # 6. Calculate CO2 emissions (DNV 2025 factor: 3.114 tCO2/t fuel)
    co2_emissions_t_h = adjusted_consumption_t_h * 3.114
    
    # 7. Estimate optimal speed (considering weather)
    # In rough conditions, slower is more efficient
    if wave_height_m > 2.0 or wind_factor > 1.2:
        optimal_speed = speed_knots * 0.85  # Reduce speed by 15% in bad weather
    else:
        # Standard optimal: find speed where fuel/speed ratio is best
        optimal_speed = min(12.0, speed_knots * 0.95)  # 5% reduction for calm seas
    
    optimal_speed = max(8.0, min(optimal_speed, 16.0))  # Keep within safe limits
    
    # 8. Calculate optimal fuel consumption
    optimal_base = k_base * (optimal_speed ** 3) * (displacement_tons / 8000.0)
    optimal_consumption_t_h = optimal_base * wind_factor * wave_factor
    
    # 9. Calculate potential savings
    if adjusted_consumption_t_h > 0:
        savings_percent = ((adjusted_consumption_t_h - optimal_consumption_t_h) / 
                         adjusted_consumption_t_h) * 100
        savings_percent = max(0, min(savings_percent, 30))  # Cap at 30%
    else:
        savings_percent = 0
    
    # 10. Calculate cost (approx 700 USD/ton for marine fuel)
    fuel_cost_usd_h = adjusted_consumption_t_h * 700
    potential_savings_usd_h = (adjusted_consumption_t_h - optimal_consumption_t_h) * 700
    
    # 11. Get weather notes
    weather_notes = _get_weather_notes(wave_height_m, wind_speed_ms, wind_factor)
    
    return {
        'current': {
            'speed_knots': round(speed_knots, 1),
            'fuel_consumption_t_h': round(adjusted_consumption_t_h, 3),
            'co2_emissions_t_h': round(co2_emissions_t_h, 3),
            'fuel_cost_usd_h': round(fuel_cost_usd_h, 0),
            'weather_impact_percent': round(((wind_factor * wave_factor) - 1) * 100, 1)
        },
        'optimal': {
            'speed_knots': round(optimal_speed, 1),
            'fuel_consumption_t_h': round(optimal_consumption_t_h, 3),
            'fuel_cost_usd_h': round(optimal_consumption_t_h * 700, 0)
        },
        'analysis': {
            'potential_savings_percent': round(savings_percent, 1),
            'potential_savings_usd_h': round(potential_savings_usd_h, 0),
            'wind_resistance_factor': round(wind_factor, 3),
            'wave_resistance_factor': round(wave_factor, 3),
            'weather_notes': weather_notes
        },
        'assumptions': {
            'fuel_price_usd_per_ton': 700,
            'co2_conversion_factor': 3.114,
            'base_vessel_displacement_tons': displacement_tons,
            'calculation_model': 'cubic_law_with_weather_resistance'
        }
    }

def _get_weather_notes(wave_height_m: float, wind_speed_ms: float, wind_factor: float) -> str:
    """Generate human-readable weather impact notes."""
    notes = []
    
    if wave_height_m > 2.0:
        notes.append(f"⚠️ Rough seas ({wave_height_m}m waves): High resistance")
    elif wave_height_m > 1.0:
        notes.append(f"↗️ Moderate waves ({wave_height_m}m): Increased resistance")
    
    if wind_factor > 1.15:
        notes.append(f"💨 Strong headwind ({wind_speed_ms} m/s): Significant drag")
    elif wind_factor > 1.05:
        notes.append(f"🌬️ Moderate wind: Some resistance")
    elif wind_factor < 0.95:
        notes.append(f"⏬ Favorable tailwind: Reduced consumption")
    
    if not notes:
        notes.append("✅ Calm conditions: Minimal weather impact")
    
    return " | ".join(notes)