"""
AIS Service - Provides vessel data
"""

from datetime import datetime
import random

def get_current_ais_data():
    """Get current AIS vessel data"""
    
    ports = [
        {"name": "Bergen", "lat": 60.392, "lon": 5.324},
        {"name": "Oslo", "lat": 59.913, "lon": 10.752},
        {"name": "Stavanger", "lat": 58.972, "lon": 5.731},
        {"name": "Trondheim", "lat": 63.430, "lon": 10.395},
    ]
    
    vessels = []
    vessel_types = ['Cargo', 'Tanker', 'Passenger', 'Fishing']
    
    for i in range(random.randint(5, 12)):
        port = random.choice(ports)
        vessels.append({
            'mmsi': f'25712345{i}',
            'name': f'MS NORWAY {i+1}',
            'lat': port['lat'] + random.uniform(-0.2, 0.2),
            'lon': port['lon'] + random.uniform(-0.2, 0.2),
            'speed': random.uniform(5, 20),
            'course': random.uniform(0, 360),
            'type': random.choice(vessel_types),
            'destination': port['name'],
            'timestamp': datetime.now().isoformat()
        })
    
    return {
        'vessels': vessels,
        'count': len(vessels),
        'timestamp': datetime.now().isoformat()
    }
