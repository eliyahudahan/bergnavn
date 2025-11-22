"""
RTZ File Generator
Generates standard RTZ files from optimized routes
Ensures compatibility with vessel navigation systems
"""

from xml.etree import ElementTree as ET
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RTZGenerator:
    """
    Generates RTZ (Route Exchange) files for vessel navigation systems
    Converts optimized routes to industry-standard format
    """
    
    def __init__(self):
        self.namespace = "http://www.cirm.org/RTZ/1/2"
        self.version = "1.2"
    
    def generate_rtz(self, route_data: Dict) -> str:
        """
        Generate RTZ XML from route data
        
        Args:
            route_data: Optimized route with waypoints and metadata
            
        Returns:
            str: RTZ XML content
        """
        try:
            # Create root element with namespace
            ET.register_namespace('', self.namespace)
            root = ET.Element(f'{{{self.namespace}}}route')
            root.set('version', self.version)
            root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            
            # Add route info
            route_info = ET.SubElement(root, f'{{{self.namespace}}}routeInfo')
            self._add_route_info(route_info, route_data)
            
            # Add waypoints
            waypoints = ET.SubElement(root, f'{{{self.namespace}}}waypoints')
            self._add_waypoints(waypoints, route_data.get('waypoints', []))
            
            # Add schedule (optional)
            schedule = ET.SubElement(root, f'{{{self.namespace}}}schedule')
            self._add_schedule(schedule, route_data)
            
            # Convert to string with proper formatting
            return self._pretty_print(root)
            
        except Exception as e:
            logger.error(f"RTZ generation failed: {e}")
            return self._generate_fallback_rtz(route_data)
    
    def _add_route_info(self, parent, route_data: Dict) -> None:
        """Add route information to RTZ"""
        ET.SubElement(parent, f'{{{self.namespace}}}routeName').text = \
            route_data.get('route_name', 'Optimized Route')
        ET.SubElement(parent, f'{{{self.namespace}}}routeAuthor').text = 'BergNavn AI'
        ET.SubElement(parent, f'{{{self.namespace}}}routeStatus').text = 'Optimized'
        
        # Add vessel constraints
        vessel_info = ET.SubElement(parent, f'{{{self.namespace}}}vessel')
        ET.SubElement(vessel_info, f'{{{self.namespace}}}vesselName').text = \
            route_data.get('vessel_name', 'Generic Vessel')
        ET.SubElement(vessel_info, f'{{{self.namespace}}}maxDraught').text = '10.0'
    
    def _add_waypoints(self, parent, waypoints: List[Dict]) -> None:
        """Add waypoints to RTZ"""
        for i, wp in enumerate(waypoints):
            waypoint = ET.SubElement(parent, f'{{{self.namespace}}}waypoint')
            waypoint.set('id', str(i + 1))
            
            position = ET.SubElement(waypoint, f'{{{self.namespace}}}position')
            ET.SubElement(position, f'{{{self.namespace}}}lat').text = str(wp.get('lat', 0))
            ET.SubElement(position, f'{{{self.namespace}}}lon').text = str(wp.get('lon', 0))
            
            if wp.get('name'):
                ET.SubElement(waypoint, f'{{{self.namespace}}}name').text = wp['name']
            
            # Add leg information
            if i > 0:
                leg = ET.SubElement(waypoint, f'{{{self.namespace}}}leg')
                ET.SubElement(leg, f'{{{self.namespace}}}speed').text = '12.0'
                ET.SubElement(leg, f'{{{self.namespace}}}geometryType').text = 'Loxodrome'
    
    def _add_schedule(self, parent, route_data: Dict) -> None:
        """Add schedule information to RTZ"""
        manual = ET.SubElement(parent, f'{{{self.namespace}}}manual')
        ET.SubElement(manual, f'{{{self.namespace}}}eta').text = \
            route_data.get('eta', datetime.utcnow().isoformat() + 'Z')
    
    def _pretty_print(self, element) -> str:
        """Return pretty-printed XML string"""
        try:
            from xml.dom import minidom
            rough_string = ET.tostring(element, 'utf-8')
            parsed = minidom.parseString(rough_string)
            return parsed.toprettyxml(indent="  ")
        except Exception:
            # Fallback to basic tostring
            return ET.tostring(element, encoding='unicode')
    
    def _generate_fallback_rtz(self, route_data: Dict) -> str:
        """Generate fallback RTZ when main generation fails"""
        root = ET.Element('route')
        ET.SubElement(root, 'routeName').text = route_data.get('route_name', 'Fallback Route')
        ET.SubElement(root, 'generator').text = 'BergNavn AI'
        ET.SubElement(root, 'timestamp').text = datetime.utcnow().isoformat()
        return ET.tostring(root, encoding='unicode')