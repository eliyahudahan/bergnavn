"""
Maritime Service - Orchestrates data fetching and risk assessment.
Follows the same pattern as cruise_service.py.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.services.ais_service import AISService
from backend.services.rtz_parser import RTZParser
from backend.services.weather_service import WeatherService
from backend.services.risk_engine import risk_engine

logger = logging.getLogger(__name__)

class MaritimeService:
    def __init__(self):
        logger.info("Initializing MaritimeService")
        self.ais_service = AISService()
        self.rtz_parser = RTZParser()
        self.weather_service = WeatherService()
        logger.info("✅ MaritimeService initialized successfully")
    
    def get_maritime_dashboard_data(self) -> Dict[str, Any]:
        """
        Get all data needed for the maritime dashboard.
        This is the main method called by the controller.
        """
        try:
            # 1. Get AIS data (vessels)
            ais_data = self.ais_service.get_vessels()
            
            # 2. Get RTZ routes (using the first port for example)
            # In reality, you might want routes for a specific port or vessel
            rtz_data = self.get_sample_rtz_routes()
            
            # 3. Get weather for the area (using Bergen as center point)
            weather_data = self.weather_service.get_weather_for_location(
                lat=60.392,  # Bergen
                lon=5.324
            )
            
            # 4. Assess risks for each vessel
            vessel_risks = []
            for vessel in ais_data.get('vessels', []):
                vessel_risk = risk_engine.assess_vessel_risk(
                    vessel_data=vessel,
                    route_data=rtz_data,
                    weather_data=weather_data
                )
                if vessel_risk:
                    vessel_risks.append({
                        'vessel_mmsi': vessel.get('mmsi'),
                        'vessel_name': vessel.get('name'),
                        'risks': vessel_risk
                    })
            
            # 5. Compose final response
            return {
                'location': 'Norwegian Waters',
                'metadata': {
                    'data_source': ais_data.get('source', 'unknown'),
                    'last_update': datetime.utcnow().isoformat(),
                    'real_time': ais_data.get('metadata', {}).get('real_time', False),
                    'total_vessels': len(ais_data.get('vessels', [])),
                    'total_risks': sum(len(r['risks']) for r in vessel_risks)
                },
                'ports': self.get_norwegian_ports(),
                'source': 'BergNavn Maritime Intelligence',
                'timestamp': datetime.utcnow().isoformat(),
                'vessels': ais_data.get('vessels', []),
                'weather': weather_data,
                'risks': vessel_risks  # NEW: Risk data added here
            }
            
        except Exception as e:
            logger.error(f"Error in get_maritime_dashboard_data: {e}")
            # Return safe fallback data
            return self.get_fallback_data()
    
    def get_sample_rtz_routes(self) -> Dict:
        """Get sample RTZ routes for demonstration."""
        try:
            # This should use your actual RTZ parser
            # For now, return a simple structure
            return {
                'routes': [
                    {
                        'name': 'Bergen - Stavanger',
                        'waypoints': [
                            {'lat': 60.392, 'lon': 5.324},
                            {'lat': 60.0, 'lon': 5.5},
                            {'lat': 59.0, 'lon': 5.7},
                            {'lat': 58.97, 'lon': 5.7331}
                        ]
                    }
                ]
            }
        except Exception as e:
            logger.warning(f"Could not get RTZ routes: {e}")
            return {'routes': []}
    
    def get_norwegian_ports(self) -> List[Dict]:
        """Return list of major Norwegian ports."""
        return [
            {'id': 1, 'name': 'Bergen', 'lat': 60.3913, 'lon': 5.3221, 'country': 'Norway'},
            {'id': 2, 'name': 'Stavanger', 'lat': 58.97, 'lon': 5.7331, 'country': 'Norway'},
            {'id': 3, 'name': 'Oslo', 'lat': 59.9139, 'lon': 10.7522, 'country': 'Norway'},
            {'id': 4, 'name': 'Trondheim', 'lat': 63.4305, 'lon': 10.3951, 'country': 'Norway'},
            {'id': 5, 'name': 'Ålesund', 'lat': 62.4722, 'lon': 6.1497, 'country': 'Norway'},
            {'id': 6, 'name': 'Kristiansand', 'lat': 58.1467, 'lon': 7.9956, 'country': 'Norway'}
        ]
    
    def get_fallback_data(self) -> Dict:
        """Return safe fallback data if something fails."""
        return {
            'location': 'Norwegian Waters',
            'metadata': {
                'data_source': 'fallback',
                'last_update': datetime.utcnow().isoformat(),
                'real_time': False,
                'total_vessels': 0,
                'total_risks': 0
            },
            'ports': self.get_norwegian_ports(),
            'source': 'BergNavn Fallback',
            'timestamp': datetime.utcnow().isoformat(),
            'vessels': [],
            'weather': {},
            'risks': []
        }

# Singleton instance
maritime_service = MaritimeService()