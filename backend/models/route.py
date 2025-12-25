# backend/models/route.py
"""
Route model for maritime routes. 
Matches the existing database table structure with safe handling for new RTZ fields.
The database already has a 'routes' table with basic columns.
New RTZ-related columns will be added via migration later.
"""
from backend.extensions import db
from datetime import datetime

class Route(db.Model):
    __tablename__ = 'routes'

    # --- EXISTING COLUMNS (confirmed in database) ---
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_days = db.Column(db.Float)
    total_distance_nm = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    origin = db.Column(db.String(100))      # Database column name is 'origin'
    destination = db.Column(db.String(100)) # Database column name is 'destination'
    
    # --- NEW COLUMNS FOR RTZ DATA (to be added via future migration) ---
    # These are defined with safe defaults and nullable=True
    # When the migration runs, they will become proper columns
    source = db.Column(db.String(50), default='NCA', nullable=True)
    rtz_filename = db.Column(db.String(255), nullable=True)
    waypoint_count = db.Column(db.Integer, default=0, nullable=True)
    rtz_file_hash = db.Column(db.String(64), nullable=True)
    vessel_draft_min = db.Column(db.Float, nullable=True)
    vessel_draft_max = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)

    # --- RELATIONSHIPS ---
    legs = db.relationship(
        "VoyageLeg",
        back_populates="route",
        cascade="all, delete-orphan",
        lazy=True
    )
    
    def __repr__(self):
        """String representation of the route."""
        origin_display = self.origin or "Unknown"
        destination_display = self.destination or "Unknown"
        return f'<Route {self.name} ({origin_display}→{destination_display})>'
    
    def safe_getattr(self, attr_name, default=None):
        """Safely get attribute, returns default if column doesn't exist."""
        try:
            return getattr(self, attr_name)
        except Exception:
            return default
    
    def to_dict(self):
        """
        Convert route to dictionary for API and template use.
        Handles missing columns gracefully for backward compatibility.
        """
        return {
            'id': self.id,
            'name': self.name or 'Unnamed Route',
            'origin': self.origin or 'Unknown',
            'destination': self.destination or 'Unknown',
            'total_distance_nm': round(self.total_distance_nm, 1) if self.total_distance_nm else 0,
            'waypoint_count': self.safe_getattr('waypoint_count', 0),
            'description': self.description or f"NCA verified route: {self.name}",
            'source': self.safe_getattr('source', 'NCA'),
            'is_active': self.is_active if self.is_active is not None else True,
            'duration_days': self.duration_days,
            'rtz_filename': self.safe_getattr('rtz_filename'),
            'created_at': self.safe_getattr('created_at'),
            'updated_at': self.safe_getattr('updated_at'),
        }
    
    @classmethod
    def create_from_rtz_data(cls, rtz_data):
        """
        Factory method to create a Route instance from RTZ parser data.
        Only sets fields that exist in the current database schema.
        """
        route = cls()
        route.name = rtz_data.get('name', 'Unnamed RTZ Route')
        route.description = rtz_data.get('description', 'Norwegian Coastal Administration route')
        
        # Map RTZ fields to database columns
        if 'origin_port' in rtz_data:
            route.origin = rtz_data['origin_port']
        elif 'origin' in rtz_data:
            route.origin = rtz_data['origin']
            
        if 'destination_port' in rtz_data:
            route.destination = rtz_data['destination_port']
        elif 'destination' in rtz_data:
            route.destination = rtz_data['destination']
            
        route.total_distance_nm = rtz_data.get('total_distance_nm', 0)
        
        # Try to set new fields if they exist in the model
        try:
            route.source = 'NCA'
            route.rtz_filename = rtz_data.get('filename')
            route.waypoint_count = rtz_data.get('waypoint_count', 0)
        except Exception:
            # Columns don't exist yet, that's OK
            pass
            
        return route
    
    def update_from_rtz_data(self, rtz_data):
        """Update existing route with RTZ data."""
        self.name = rtz_data.get('name', self.name)
        self.description = rtz_data.get('description', self.description)
        
        if 'origin_port' in rtz_data:
            self.origin = rtz_data['origin_port']
        if 'destination_port' in rtz_data:
            self.destination = rtz_data['destination_port']
            
        self.total_distance_nm = rtz_data.get('total_distance_nm', self.total_distance_nm)
        self.updated_at = datetime.utcnow()
        
        # Try to update new fields
        try:
            self.rtz_filename = rtz_data.get('filename', self.rtz_filename)
            self.waypoint_count = rtz_data.get('waypoint_count', self.waypoint_count)
            self.parsed_at = datetime.utcnow()
        except Exception:
            # New columns not available yet
            pass
            
        return self