# models/maritime_route.py
# Unified Maritime Route Model for BergNavn
# -------------------------------------------------------
# This model merges the logical concepts of:
# - Route (high-level route entity)
# - BaseRoute (official RTZ route geometry)
# - RouteLeg (waypoints / geometry segments)
# - VoyageLeg (operational scheduling / ETA / distance)
#
# The unified structure supports:
# - Real-time AIS integration
# - Weather impact per segment
# - Safety constraints (wind farms, hazards, buffers)
# - Fuel optimization data
# - Day/Night conditions for each waypoint
# - Production-level performance & analytics
# -------------------------------------------------------

from datetime import datetime, UTC
from backend.extensions import db
from geoalchemy2 import Geometry


class MaritimeRoute(db.Model):
    __tablename__ = "maritime_routes"

    id = db.Column(db.Integer, primary_key=True)

    # Human metadata
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    # High-level geometry (full route polyline)
    geometry = db.Column(Geometry("LINESTRING", srid=4326))

    # Origin / destination
    origin_port_id = db.Column(db.Integer, db.ForeignKey("ports.id"))
    destination_port_id = db.Column(db.Integer, db.ForeignKey("ports.id"))

    origin_port = db.relationship("Port", foreign_keys=[origin_port_id])
    destination_port = db.relationship("Port", foreign_keys=[destination_port_id])

    # Operational metadata
    total_distance_nm = db.Column(db.Float)
    expected_duration_hours = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)

    # Relations
    legs = db.relationship(
        "MaritimeRouteLeg",
        back_populates="route",
        cascade="all, delete-orphan"
    )

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self):
        return f"<MaritimeRoute {self.name}>"


class MaritimeRouteLeg(db.Model):
    __tablename__ = "maritime_route_legs"

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("maritime_routes.id"))

    route = db.relationship("MaritimeRoute", back_populates="legs")

    # Indexing & geometry
    leg_index = db.Column(db.Integer, nullable=False)
    geometry = db.Column(Geometry("LINESTRING", srid=4326))
    distance_nm = db.Column(db.Float)
    eta_minutes = db.Column(db.Float)

    # Weather & conditions
    wave_height_m = db.Column(db.Float)
    wind_speed_ms = db.Column(db.Float)
    daylight_condition = db.Column(db.String(50))  # day / night / twilight

    # Safety metadata
    hazard_nearby = db.Column(db.Boolean, default=False)
    safety_buffer_m = db.Column(db.Float)

    # Real-time AIS
    avg_speed_knots = db.Column(db.Float)
    congestion_index = db.Column(db.Float)

    # Runtime metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self):
        return f"<MaritimeRouteLeg {self.leg_index} of route {self.route_id}>"
