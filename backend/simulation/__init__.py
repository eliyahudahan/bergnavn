"""
Simulation package for BergNavn.
Integrates with existing RTZ, Weather, Risk, and Alert services.
"""

from backend.simulation.integrated_simulator import IntegratedShipSimulator, get_simulator

__all__ = ['IntegratedShipSimulator', 'get_simulator']
