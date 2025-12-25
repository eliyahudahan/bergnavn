#!/usr/bin/env python3
"""
Configuration validation for migrations
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def validate_configuration():
    """Validate all required configuration for migrations"""
    
    errors = []
    warnings = []
    
    # Required for migrations
    required_vars = [
        'DATABASE_URL',
        'FLASK_APP'
    ]
    
    # Recommended for production
    recommended_vars = [
        'FLASK_ENV',
        'DISABLE_AIS_SERVICE'
    ]
    
    print("🔧 Validating configuration...")
    
    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"❌ Required environment variable missing: {var}")
        else:
            print(f"✅ {var} is set")
    
    # Check recommended variables
    for var in recommended_vars:
        if not os.getenv(var):
            warnings.append(f"⚠️  Recommended variable not set: {var}")
        else:
            print(f"✅ {var} = {os.getenv(var)}")
    
    # Database URL validation
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        if 'postgresql://' not in db_url:
            errors.append("❌ DATABASE_URL should start with 'postgresql://'")
    
    # Flask environment validation
    flask_env = os.getenv('FLASK_ENV', 'development')
    if flask_env not in ['development', 'production', 'testing']:
        warnings.append(f"⚠️  FLASK_ENV has unusual value: {flask_env}")
    
    # Print results
    print("\n" + "="*60)
    
    if errors:
        print("❌ CONFIGURATION ERRORS:")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        print("\n⚠️  CONFIGURATION WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
    
    if not errors and not warnings:
        print("✅ All configuration checks passed!")
    
    print("="*60)
    
    return len(errors) == 0

if __name__ == "__main__":
    is_valid = validate_configuration()
    sys.exit(0 if is_valid else 1)
