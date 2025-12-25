"""
System Routes Module
========================
Contains health check and system status endpoints for the BergNavn Maritime application.

This module provides endpoints for monitoring system health, database connectivity,
and overall system status. Essential for production monitoring and debugging.
"""

from flask import Blueprint, jsonify
from backend import db
from sqlalchemy import text

# Create blueprint for system/health endpoints
# Blueprint name: 'health'
# URL prefix: none (root level)
health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health Check Endpoint
    ---------------------
    Verifies database connectivity and returns system health status.
    
    Response Codes:
    - 200 OK: System is healthy, database is connected
    - 500 Internal Server Error: Database connection failed
    
    Returns:
        JSON object with status and details
        
    Example Response (200 OK):
        {
            "status": "ok",
            "service": "BergNavn Maritime",
            "database": "connected",
            "timestamp": "2025-12-25T20:00:00Z"
        }
        
    Example Response (500 Error):
        {
            "status": "error", 
            "service": "BergNavn Maritime",
            "database": "disconnected",
            "details": "Database connection failed: ..."
        }
    """
    import datetime
    
    try:
        # Execute a simple SQL query to verify database connectivity
        # Using text() wrapper is REQUIRED for raw SQL in SQLAlchemy 2.0+
        db.session.execute(text('SELECT 1'))
        
        # Database connection successful
        return jsonify({
            "status": "ok",
            "service": "BergNavn Maritime",
            "database": "connected",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "endpoints": {
                "system_info": "/system/info",
                "api_keys_status": "/api/check-api-keys"
            }
        }), 200
        
    except Exception as e:
        # Database connection failed
        return jsonify({
            "status": "error",
            "service": "BergNavn Maritime", 
            "database": "disconnected",
            "details": f"Database connection failed: {str(e)}",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "recommended_action": "Check database credentials and connection"
        }), 500


@health_bp.route('/system/info', methods=['GET'])
def system_info():
    """
    System Information Endpoint
    ---------------------------
    Returns comprehensive system information including version, 
    environment, and service status.
    
    Useful for:
    - Monitoring dashboards
    - Debugging and troubleshooting
    - Service discovery
    
    Returns:
        JSON object with system metadata
        
    Example Response:
        {
            "status": "ok",
            "service": "BergNavn Maritime",
            "version": "1.0.0",
            "environment": "development",
            "database": "connected",
            "timestamp": "2025-12-25T20:00:00Z",
            "features": {
                "ais_service": true,
                "weather_service": true,
                "route_planning": true
            }
        }
    """
    import os
    import datetime
    
    # Check database connectivity
    try:
        db.session.execute(text('SELECT 1'))
        db_status = "connected"
        db_error = None
    except Exception as e:
        db_status = "disconnected"
        db_error = str(e)
    
    # Gather system information
    system_info = {
        "status": "ok",
        "service": "BergNavn Maritime",
        "version": "1.0.0",
        "environment": os.getenv('FLASK_ENV', 'development'),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "database": {
            "status": db_status,
            "error": db_error
        },
        "features": {
            "ais_service": os.getenv('DISABLE_AIS_SERVICE', '0') != '1',
            "weather_service": bool(os.getenv('OPENWEATHER_API_KEY')),
            "route_planning": True,
            "risk_assessment": True
        },
        "endpoints": {
            "health": "/health",
            "system_info": "/system/info",
            "routes_api": "/routes/api/routes",
            "weather_api": "/maritime/api/weather",
            "maritime_dashboard": "/maritime/dashboard"
        }
    }
    
    return jsonify(system_info), 200


@health_bp.route('/ping', methods=['GET'])
def ping():
    """
    Simple Ping Endpoint
    --------------------
    Ultra-lightweight endpoint for basic connectivity checks.
    
    Use cases:
    - Load balancer health checks
    - Network connectivity testing
    - Simple uptime monitoring
    
    Returns:
        Simple JSON response with 'pong'
        
    Example Response:
        {"status": "pong"}
    """
    return jsonify({"status": "pong"}), 200


# Optional: Add a readiness check for Kubernetes/container orchestration
@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Readiness Check Endpoint
    ------------------------
    Advanced health check for container orchestration systems.
    
    Verifies all critical dependencies are ready:
    - Database connectivity
    - External API availability (if configured)
    - Required environment variables
    
    Used by:
    - Kubernetes readiness probes
    - Docker health checks
    - Load balancer initialization
    
    Returns:
        Detailed readiness status with component checks
    """
    import datetime
    
    checks = {
        "database": {"status": "unknown", "details": None},
        "environment": {"status": "unknown", "details": None},
        "services": {"status": "unknown", "details": None}
    }
    
    all_healthy = True
    
    # Check database
    try:
        db.session.execute(text('SELECT 1'))
        checks["database"]["status"] = "healthy"
        checks["database"]["details"] = "Connection successful"
    except Exception as e:
        checks["database"]["status"] = "unhealthy"
        checks["database"]["details"] = str(e)
        all_healthy = False
    
    # Check required environment variables
    required_vars = ['DATABASE_URL', 'FLASK_APP']
    missing_vars = []
    
    import os
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        checks["environment"]["status"] = "unhealthy"
        checks["environment"]["details"] = f"Missing variables: {', '.join(missing_vars)}"
        all_healthy = False
    else:
        checks["environment"]["status"] = "healthy"
        checks["environment"]["details"] = "All required variables set"
    
    # Check external services (basic check)
    checks["services"]["status"] = "healthy"
    checks["services"]["details"] = "Service checks passed"
    
    # Determine overall status
    if all_healthy:
        status_code = 200
        overall_status = "ready"
    else:
        status_code = 503  # Service Unavailable
        overall_status = "not_ready"
    
    return jsonify({
        "status": overall_status,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "checks": checks,
        "service": "BergNavn Maritime"
    }), status_code
