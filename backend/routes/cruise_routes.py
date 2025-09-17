"""
Cruise routes module.
All route handling is delegated to cruise_controller.py via cruise_bp.
This ensures that CRUD logic remains centralized in the controller,
avoiding direct imports of individual functions.
"""

from backend.controllers.cruise_controller import cruise_bp

# Expose blueprint for app.py
cruise_blueprint = cruise_bp
