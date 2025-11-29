# dev_check.py
# Automated health test for development environment

import os
import sys
import traceback
from datetime import datetime

OUTPUT_FILE = "dev_check_output.txt"

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, "a") as f:
        f.write(msg + "\n")

# Clear previous output
open(OUTPUT_FILE, "w").close()

log("==========================================")
log("  DEV ENVIRONMENT CHECK - BergNavn")
log(f"  Timestamp: {datetime.now().isoformat()}")
log("==========================================\n")

try:
    log("1) 🟦 Importing Flask app…")
    from app import create_app
    app = create_app(testing=True, start_scheduler=False)
    log("   ✔ App loaded successfully\n")
except Exception as e:
    log("   ❌ ERROR loading app:")
    log(str(e))
    log(traceback.format_exc())
    sys.exit(1)

try:
    log("2) 🟦 Testing database connection…")
    from backend.extensions import db
    with app.app_context():
        db.session.execute(db.text("SELECT 1"))
    log("   ✔ Database connection OK\n")
except Exception as e:
    log("   ❌ Database error:")
    log(str(e))
    log(traceback.format_exc())

try:
    log("3) 🟦 Testing model imports…")
    with app.app_context():
        from backend import models
    log("   ✔ All models imported\n")
except Exception as e:
    log("   ❌ Model import error:")
    log(str(e))
    log(traceback.format_exc())

try:
    log("4) 🟦 Testing PostGIS geometry…")
    from geoalchemy2 import WKTElement
    test_geom = WKTElement("LINESTRING(10 10, 20 20)", srid=4326)
    log("   ✔ Geometry object created successfully\n")
except Exception as e:
    log("   ❌ Geometry error:")
    log(str(e))
    log(traceback.format_exc())

try:
    log("5) 🟦 Running a Route evaluate test…")
    with app.app_context():
        from backend.services.route_evaluator import evaluate_route
        evaluate_route(1)
    log("   ✔ Route evaluator works\n")
except Exception as e:
    log("   ❌ Route evaluator error:")
    log(str(e))
    log(traceback.format_exc())


log("\n==========================================")
log("  ✔ FINISHED! Output saved to dev_check_output.txt")
log("==========================================")
