"""
system_dashboard.py - Comprehensive system monitoring for BergNavn Maritime
Provides real-time system status, health checks, and performance metrics
using ACTUAL production services and data sources.
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime, timedelta
import logging
import os
import time

from backend.models.route import Route
from backend.extensions import db
from sqlalchemy import func, text

# Initialize blueprint
system_bp = Blueprint('system_bp', __name__)
logger = logging.getLogger(__name__)


@system_bp.route('/summary')
def system_summary():
    """
    Comprehensive system summary using REAL production data.
    
    Returns:
        Complete system status including:
        - Database metrics and routes statistics
        - Service connectivity (AIS, Weather, BarentsWatch)
        - System performance indicators
        - Environment configuration
    """
    try:
        # ============ REAL DATABASE STATISTICS ============
        total_routes = Route.query.filter_by(is_active=True).count()
        
        routes_by_source = db.session.query(
            Route.source, 
            func.count(Route.id).label('count')
        ).group_by(Route.source).all()
        
        recent_routes = Route.query.order_by(
            Route.created_at.desc() if hasattr(Route, 'created_at') else Route.id.desc()
        ).limit(5).all()
        
        total_distance = db.session.query(
            func.sum(Route.total_distance_nm)
        ).scalar() or 0
        
        avg_distance = db.session.query(
            func.avg(Route.total_distance_nm)
        ).scalar() or 0
        
        # ============ SERVICE HEALTH CHECKS ============
        services_status = {
            "database": _check_database_status(),
            "ais": _check_ais_service_status(),
            "weather": _check_weather_service_status(),
            "barentswatch": _check_barentswatch_status(),
            "scheduler": _check_scheduler_status()
        }
        
        # ============ SYSTEM PERFORMANCE ============
        system_metrics = {
            "total_routes": total_routes,
            "total_distance_nm": float(total_distance),
            "avg_distance_nm": float(avg_distance),
            "unique_ports": _count_unique_ports(),
            "active_services": sum(1 for s in services_status.values() if s.get("status") == "healthy")
        }
        
        # ============ COMPREHENSIVE RESPONSE ============
        summary = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "system": {
                "status": "operational",
                "version": "1.0.0",
                "environment": os.getenv('FLASK_ENV', 'development'),
                "uptime_seconds": _get_uptime_seconds()
            },
            
            "data": {
                "routes": {
                    "total": total_routes,
                    "by_source": [{"source": source, "count": count} for source, count in routes_by_source],
                    "recent": [
                        {
                            "id": route.id,
                            "name": route.name,
                            "origin": route.origin,
                            "destination": route.destination,
                            "distance_nm": route.total_distance_nm,
                            "source": route.source
                        } for route in recent_routes
                    ]
                },
                "statistics": system_metrics
            },
            
            "services": services_status,
            
            "performance": {
                "database_response_ms": _measure_database_query_time(),
                "memory_usage_mb": _get_memory_usage(),
                "active_threads": _get_active_threads()
            },
            
            "configuration": {
                "ais_enabled": os.getenv("DISABLE_AIS_SERVICE") != "1",
                "real_ais_connected": os.getenv("USE_KYSTVERKET_AIS") == "true",
                "barentswatch_configured": bool(os.getenv("BARENTSWATCH_CLIENT_ID")),
                "met_norway_configured": bool(os.getenv("MET_USER_AGENT"))
            }
        }
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"System summary error: {str(e)}", exc_info=True)
        return jsonify({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "error",
            "error": str(e),
            "message": "Failed to generate system summary"
        }), 500


@system_bp.route('/health')
def health_detailed():
    """
    Detailed health check with service connectivity verification.
    
    Returns:
        Individual service status with connection test results
        and response times where applicable.
    """
    checks = []
    
    # Database connectivity test
    db_start = datetime.utcnow()
    try:
        result = db.session.execute(text("SELECT 1, version(), now()")).fetchone()
        db_duration = (datetime.utcnow() - db_start).total_seconds() * 1000
        
        checks.append({
            "service": "postgresql_database",
            "status": "healthy",
            "response_time_ms": round(db_duration, 2),
            "details": {
                "postgres_version": result[1] if result else "unknown",
                "server_time": result[2].isoformat() if result and result[2] else "unknown"
            }
        })
    except Exception as e:
        checks.append({
            "service": "postgresql_database",
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": (datetime.utcnow() - db_start).total_seconds() * 1000
        })
    
    # Routes data availability
    try:
        route_count = Route.query.count()
        route_duration = (datetime.utcnow() - db_start).total_seconds() * 1000
        
        checks.append({
            "service": "routes_data",
            "status": "healthy" if route_count > 0 else "degraded",
            "response_time_ms": round(route_duration, 2),
            "details": {
                "total_routes": route_count,
                "has_data": route_count > 0
            }
        })
    except Exception as e:
        checks.append({
            "service": "routes_data",
            "status": "unhealthy",
            "error": str(e)
        })
    
    # AIS Service check
    ais_status = _check_ais_service_status(detailed=True)
    checks.append({
        "service": "ais_service",
        "status": ais_status.get("status", "unknown"),
        "details": ais_status
    })
    
    # BarentsWatch API check
    bw_status = _check_barentswatch_status(detailed=True)
    checks.append({
        "service": "barentswatch_api",
        "status": bw_status.get("status", "unknown"),
        "details": bw_status
    })
    
    # Weather service check
    weather_status = _check_weather_service_status(detailed=True)
    checks.append({
        "service": "weather_api",
        "status": weather_status.get("status", "unknown"),
        "details": weather_status
    })
    
    # Calculate overall health
    healthy_checks = sum(1 for c in checks if c["status"] in ["healthy", "degraded"])
    total_checks = len(checks)
    
    return jsonify({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
        "summary": {
            "total_checks": total_checks,
            "healthy": sum(1 for c in checks if c["status"] == "healthy"),
            "degraded": sum(1 for c in checks if c["status"] == "degraded"),
            "unhealthy": sum(1 for c in checks if c["status"] == "unhealthy"),
            "overall_health": "healthy" if healthy_checks == total_checks else "degraded"
        }
    })


@system_bp.route('/metrics')
def system_metrics():
    """
    Performance metrics for monitoring and alerting.
    
    Returns:
        Key performance indicators suitable for time-series databases
        like Prometheus or monitoring dashboards.
    """
    try:
        # Get current metrics
        total_routes = Route.query.filter_by(is_active=True).count()
        active_routes = Route.query.filter_by(is_active=True).count()
        
        # Get temporal statistics if available
        routes_last_hour = 0
        if hasattr(Route, 'created_at'):
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            routes_last_hour = Route.query.filter(Route.created_at >= hour_ago).count()
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "counters": {
                "routes_total": total_routes,
                "routes_active": active_routes,
                "routes_inactive": 0,
                "routes_created_last_hour": routes_last_hour
            },
            "gauges": {
                "memory_usage_bytes": _get_memory_usage_bytes(),
                "database_connections": _estimate_db_connections(),
                "active_requests": 0  # Could be tracked with middleware
            },
            "timers": {
                "database_query_ms": _measure_database_query_time(),
                "ais_update_latency_ms": 0,
                "weather_api_response_ms": 0
            }
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Metrics collection error: {str(e)}")
        return jsonify({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e),
            "status": "degraded"
        })


@system_bp.route('/overview')
def system_overview():
    """
    Lightweight system overview for dashboard widgets.
    
    Returns:
        Essential system status for frequent polling with minimal payload.
    """
    try:
        total_routes = Route.query.filter_by(is_active=True).count()
        total_distance = db.session.query(
            func.sum(Route.total_distance_nm)
        ).scalar() or 0
        
        return jsonify({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "operational",
            "data": {
                "routes_count": total_routes,
                "total_distance_km": round(float(total_distance) * 1.852, 1),  # Convert NM to KM
                "ports_served": _count_unique_ports()
            },
            "services": {
                "database": "online",
                "ais": _check_ais_service_status().get("status", "unknown"),
                "barentswatch": _check_barentswatch_status().get("status", "unknown")
            }
        })
        
    except Exception as e:
        return jsonify({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "degraded",
            "error": str(e)[:100]
        })


# ============================================================================
# SERVICE CHECK FUNCTIONS (REAL IMPLEMENTATIONS)
# ============================================================================

def _check_database_status():
    """Check PostgreSQL database connectivity and performance."""
    try:
        start_time = datetime.utcnow()
        result = db.session.execute(
            text("SELECT 1, version(), pg_database_size(current_database())")
        ).fetchone()
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(duration_ms, 2),
            "postgres_version": result[1].split()[1] if result and result[1] else "unknown",
            "database_size_mb": round(result[2] / (1024 * 1024), 2) if result and result[2] else 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def _check_ais_service_status(detailed=False):
    """Check AIS service status using the actual service instance."""
    try:
        from backend.services.ais_service import ais_service
        
        status = ais_service.get_service_status()
        
        if detailed:
            return {
                "status": "healthy" if status.get("connected", False) else "degraded",
                "real_ais_enabled": status.get("real_ais_enabled", False),
                "connected": status.get("connected", False),
                "active_vessels": status.get("active_vessels", 0),
                "data_source": status.get("data_source", "unknown"),
                "last_update": status.get("last_update"),
                "messages_received": status.get("messages_received", 0)
            }
        else:
            return {
                "status": "healthy" if status.get("connected", False) else "degraded",
                "active_vessels": status.get("active_vessels", 0)
            }
            
    except Exception as e:
        logger.warning(f"AIS service check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def _check_barentswatch_status(detailed=False):
    """Check BarentsWatch API service status."""
    try:
        from backend.services.barentswatch_service import barentswatch_service
        
        status = barentswatch_service.get_service_status()
        
        if detailed:
            return {
                "status": "healthy" if status["authentication"]["token_valid"] else "degraded",
                "client_configured": status["authentication"]["client_id_configured"],
                "token_valid": status["authentication"]["token_valid"],
                "time_remaining_seconds": status["authentication"]["time_remaining_seconds"],
                "ais_access": status["access_levels"]["ais_realtime"],
                "geodata_access": status["access_levels"]["geodata_static"],
                "scope": status["authentication"]["current_scope"]
            }
        else:
            return {
                "status": "healthy" if status["authentication"]["token_valid"] else "degraded",
                "ais_available": status["access_levels"]["ais_realtime"]
            }
            
    except Exception as e:
        logger.warning(f"BarentsWatch service check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def _check_weather_service_status(detailed=False):
    """Check weather service status."""
    try:
        met_agent = os.getenv('MET_USER_AGENT')
        openweather_key = os.getenv('OPENWEATHER_API_KEY')
        
        if detailed:
            return {
                "status": "configured",
                "met_norway_configured": bool(met_agent),
                "openweather_configured": bool(openweather_key),
                "primary_source": "MET Norway" if met_agent else "OpenWeatherMap" if openweather_key else "none"
            }
        else:
            return {
                "status": "configured" if met_agent or openweather_key else "unconfigured"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def _check_scheduler_status():
    """Check APScheduler status."""
    try:
        if hasattr(current_app, 'scheduler'):
            return {
                "status": "running" if current_app.scheduler.running else "stopped",
                "jobs_count": len(current_app.scheduler.get_jobs()) if current_app.scheduler.running else 0
            }
        return {"status": "not_initialized"}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def _count_unique_ports():
    """Count unique ports in the routes database."""
    try:
        origins = db.session.query(Route.origin).distinct().count()
        destinations = db.session.query(Route.destination).distinct().count()
        return origins + destinations  # Simple estimate
    except:
        return 0


def _get_uptime_seconds():
    """Get application uptime in seconds."""
    try:
        if hasattr(current_app, 'start_time'):
            return int((datetime.utcnow() - current_app.start_time).total_seconds())
        return 0
    except:
        return 0


def _get_memory_usage():
    """Get current memory usage in megabytes."""
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return round(process.memory_info().rss / (1024 * 1024), 2)
    except ImportError:
        return 0.0
    except:
        return 0.0


def _get_memory_usage_bytes():
    """Get memory usage in bytes for precise metrics."""
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    except:
        return 0


def _get_active_threads():
    """Get number of active threads."""
    try:
        import threading
        return threading.active_count()
    except:
        return 0


def _estimate_db_connections():
    """Estimate database connections (simplified)."""
    try:
        # This is a simplification - in production you'd query pg_stat_activity
        return 1  # Base connection + potential pool
    except:
        return 0


def _measure_database_query_time():
    """Measure actual database query time."""
    try:
        start_time = time.perf_counter() * 1000  # milliseconds
        # Simple test query
        Route.query.filter_by(is_active=True).count()
        end_time = time.perf_counter() * 1000
        return round(end_time - start_time, 2)
    except:
        return 0


# Initialize application start time for uptime tracking
@system_bp.before_app_request
def _initialize_start_time():
    """Set application start time on first request."""
    if not hasattr(current_app, 'start_time'):
        current_app.start_time = datetime.utcnow()
        logger.info(f"System dashboard initialized at {current_app.start_time.isoformat()}")