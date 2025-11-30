# backend/services/rtz_integration.py
"""
RTZ integration wrapper - uses existing RTZ parser module (rtz_parser)
This file orchestrates discovery of RTZ files under backend/assets/routeinfo_routes and
calls the parser and DB saver functions.
"""

import os
from backend.services.rtz_parser import process_all_cities_routes, find_rtz_files

def discover_and_process_rtz():
    """
    Discover RTZ files and process them using existing parser.
    Returns number of saved routes (as process_all_cities_routes returns).
    """
    return process_all_cities_routes()
