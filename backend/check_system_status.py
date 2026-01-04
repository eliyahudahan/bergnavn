#!/usr/bin/env python3
"""
System Status Checker for BergNavn
Checks all core components and reports status
"""

import sys
import os
import subprocess
from datetime import datetime

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    return {
        'status': '✅' if version.major == 3 and version.minor >= 8 else '❌',
        'version': f"{version.major}.{version.minor}.{version.micro}",
        'required': '3.8+'
    }

def check_imports():
    """Check if core modules can be imported"""
    imports = [
        ('flask', 'Flask'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('torch', 'torch'),
        ('sklearn', 'sklearn'),
    ]
    
    results = []
    for module, name in imports:
        try:
            __import__(module)
            results.append(('✅', name))
        except ImportError as e:
            results.append(('❌', f"{name}: {str(e)}"))
    
    return results

def check_database():
    """Check database connection"""
    try:
        from backend.database import db
        result = db.session.execute('SELECT 1').first()
        return ('✅', 'Database connection successful')
    except Exception as e:
        return ('❌', f'Database error: {str(e)}')

def check_services():
    """Check external services"""
    services = []
    
    # AIS Service
    try:
        from backend.services.ais_service import AISService
        ais = AISService()
        status = ais.test_connection()
        services.append(('✅' if status else '❌', 'AIS Service'))
    except Exception as e:
        services.append(('❌', f'AIS Service: {str(e)}'))
    
    # Weather Service
    try:
        from backend.services.weather_service import WeatherService
        weather = WeatherService()
        status = weather.test_connection()
        services.append(('✅' if status else '❌', 'Weather Service'))
    except Exception as e:
        services.append(('❌', f'Weather Service: {str(e)}'))
    
    return services

def check_directories():
    """Check required directories exist"""
    directories = [
        ('backend/assets', 'Assets directory'),
        ('backend/assets/ais_data', 'AIS data directory'),
        ('backend/assets/weather_data', 'Weather data directory'),
        ('backend/assets/routeinfo_routes', 'Route data directory'),
        ('backend/static/js/split', 'JavaScript files'),
        ('backend/templates', 'HTML templates'),
    ]
    
    results = []
    for path, description in directories:
        if os.path.exists(path):
            results.append(('✅', f"{description}: {path}"))
        else:
            results.append(('❌', f"{description}: MISSING ({path})"))
    
    return results

def check_apis():
    """Check API endpoints are accessible"""
    import requests
    
    apis = [
        ('http://localhost:5000/api/health', 'Local API Health'),
        ('http://localhost:5000/api/ais/status', 'AIS API'),
        ('http://localhost:5000/api/weather/status', 'Weather API'),
    ]
    
    results = []
    for url, name in apis:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results.append(('✅', f"{name}: {url}"))
            else:
                results.append(('⚠️', f"{name}: HTTP {response.status_code}"))
        except Exception as e:
            results.append(('❌', f"{name}: {str(e)}"))
    
    return results

def check_data_files():
    """Check important data files exist"""
    files = [
        ('backend/assets/routeinfo_routes/bergen/route.json', 'Bergen route data'),
        ('backend/config/config.py', 'Configuration file'),
        ('backend/database/__init__.py', 'Database init'),
        ('backend/services/__init__.py', 'Services init'),
    ]
    
    results = []
    for path, description in files:
        if os.path.exists(path):
            # Check if file has content
            size = os.path.getsize(path)
            results.append(('✅', f"{description}: {size} bytes"))
        else:
            results.append(('❌', f"{description}: MISSING"))
    
    return results

def run_system_check():
    """Run complete system check"""
    print(f"\n{'🚢 BERGENAVN SYSTEM CHECK '.ljust(60, '=')}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Python Version
    print_section("Python Environment")
    py_check = check_python_version()
    print(f"{py_check['status']} Python {py_check['version']} (requires {py_check['required']})")
    
    # 2. Imports
    print_section("Core Imports")
    for status, message in check_imports():
        print(f"{status} {message}")
    
    # 3. Database
    print_section("Database")
    status, message = check_database()
    print(f"{status} {message}")
    
    # 4. Services
    print_section("External Services")
    for status, message in check_services():
        print(f"{status} {message}")
    
    # 5. Directories
    print_section("Directory Structure")
    for status, message in check_directories():
        print(f"{status} {message}")
    
    # 6. Data Files
    print_section("Data Files")
    for status, message in check_data_files():
        print(f"{status} {message}")
    
    # 7. APIs (if running)
    print_section("API Endpoints")
    for status, message in check_apis():
        print(f"{status} {message}")
    
    print(f"\n{'='*60}")
    print("🎯 NEXT STEPS:")
    print("1. Fix any ❌ items above")
    print("2. Run: python3 run.py (to start server)")
    print("3. Open: http://localhost:5000")
    print("4. Then add simulation features")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run_system_check()