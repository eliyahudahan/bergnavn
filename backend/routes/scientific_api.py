"""
Scientific API endpoints for empirical data verification.
Add this to your existing routes.
"""

from flask import Blueprint, jsonify, request, current_app
from backend.services.scientific_truth_service import (
    ScientificTruthService, 
    get_scientific_truth,
    generate_full_report
)
import json

# Create blueprint
scientific_bp = Blueprint('scientific', __name__, url_prefix='/api/scientific')


@scientific_bp.route('/truth', methods=['GET'])
def get_scientific_truth_endpoint():
    """
    Get the scientifically verified truth about route counts.
    
    Returns:
        JSON with empirical verification data
    """
    try:
        service = ScientificTruthService()
        truth_data = service.get_empirical_truth()
        
        return jsonify({
            "success": True,
            "data": truth_data,
            "message": f"Scientific verification complete. Empirical truth: {truth_data['empirical_truth']}"
        })
    
    except Exception as e:
        current_app.logger.error(f"Scientific truth error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to perform scientific verification"
        }), 500


@scientific_bp.route('/verification-report', methods=['GET'])
def get_verification_report():
    """
    Get a full verification report in markdown format.
    
    Returns:
        Markdown report as text
    """
    try:
        report = generate_full_report()
        
        return report, 200, {'Content-Type': 'text/markdown'}
    
    except Exception as e:
        current_app.logger.error(f"Report generation error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate verification report"
        }), 500


@scientific_bp.route('/physical-files', methods=['GET'])
def get_physical_files():
    """
    Get detailed information about physical RTZ files.
    
    Returns:
        JSON with file details
    """
    try:
        service = ScientificTruthService()
        file_data = service.count_physical_rtz_files()
        
        return jsonify({
            "success": True,
            "data": file_data,
            "message": f"Found {file_data['count']} physical RTZ files"
        })
    
    except Exception as e:
        current_app.logger.error(f"Physical files error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to analyze physical files"
        }), 500


@scientific_bp.route('/discrepancy-analysis', methods=['GET'])
def get_discrepancy_analysis():
    """
    Analyze the discrepancy between dashboard and empirical data.
    
    Returns:
        JSON with discrepancy analysis
    """
    try:
        service = ScientificTruthService()
        analysis = service.analyze_dashboard_discrepancy()
        
        return jsonify({
            "success": True,
            "data": analysis,
            "message": f"Dashboard shows {analysis['dashboard_displayed']}, empirical truth is {analysis['empirical_unique']}"
        })
    
    except Exception as e:
        current_app.logger.error(f"Discrepancy analysis error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to analyze discrepancies"
        }), 500


@scientific_bp.route('/verify-now', methods=['POST'])
def run_verification_now():
    """
    Run scientific verification immediately and update cache.
    
    Returns:
        JSON with fresh verification results
    """
    try:
        # Force fresh verification
        service = ScientificTruthService()
        truth_data = service.get_empirical_truth()
        
        # Generate report file
        report = service.generate_verification_report()
        report_path = service.base_path / "verification_report.md"
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        return jsonify({
            "success": True,
            "data": truth_data,
            "report_path": str(report_path),
            "message": "Fresh verification completed successfully"
        })
    
    except Exception as e:
        current_app.logger.error(f"Verification error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to run verification"
        }), 500


# Health check endpoint
@scientific_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check for scientific verification service.
    
    Returns:
        JSON health status
    """
    try:
        service = ScientificTruthService()
        
        # Quick check of routes directory
        routes_dir_exists = service.routes_dir.exists()
        db_exists = service.db_path.exists()
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "checks": {
                "routes_directory": "exists" if routes_dir_exists else "missing",
                "database_file": "exists" if db_exists else "missing",
                "service": "operational"
            },
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# Register this in your main app.py or __init__.py
# from backend.routes.scientific_api import scientific_bp
# app.register_blueprint(scientific_bp)