from .clock import Clock
from .cruise import Cruise
from .port import Port
from .locations import Location
from .route import Route
from .voyage_leg import VoyageLeg
from .weather_status import WeatherStatus

# EXISTING MODELS THAT WERE MISSING
from .base_route import BaseRoute
from .route_file import RouteFile  
from .route_leg import RouteLeg
from .waypoint import Waypoint
from .hazard_zone import HazardZone

# NEW MODELS - CRITICAL FOR METADATA REGISTRATION
from .ship import Ship
from .fuel_efficiency import FuelEfficiencyCalculation  
from .ship_coefficients import ShipTypeCoefficient

__all__ = [
    'Clock', 'Cruise', 'Port', 'Location', 'Route', 'VoyageLeg', 
    'WeatherStatus', 'BaseRoute', 'RouteFile', 'RouteLeg', 'Waypoint',
    'HazardZone', 'Ship', 'FuelEfficiencyCalculation', 'ShipTypeCoefficient'
]