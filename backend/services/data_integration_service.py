# backend/services/data_integration_service.py
"""
BergNavn Data Integration Service
Integrates real AIS data with NCA routes for live maritime tracking
"""

class DataIntegrationService:
    def __init__(self):
        self.ais_service = AISLiveService()
        self.free_ais_service = FreeAisService()
        
    def get_live_maritime_data(self):
        """Get integrated maritime data for frontend"""
        try:
            # Try real AIS first
            real_ships = self.ais_service.ships_data
            
            # Fallback to free service if no real data
            if not real_ships or len(real_ships) == 0:
                real_ships = self.free_ais_service.get_norwegian_commercial_vessels()
            
            # Combine with NCA route data
            integrated_data = {
                'ships': real_ships,
                'routes': self._get_nca_routes(),
                'timestamp': datetime.now().isoformat(),
                'data_source': 'real' if self.ais_service.is_connected else 'simulated'
            }
            
            return integrated_data
            
        except Exception as e:
            print(f"Data integration error: {e}")
            return self._get_fallback_data()