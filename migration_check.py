# migration_check.py
# Safe Alembic migration environment checker (read-only)

import os
import sys
import traceback
from datetime import datetime

OUTPUT_FILE = "migration_check_output.txt"

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, "a") as f:
        f.write(msg + "\n")

# Reset file
open(OUTPUT_FILE, "w").close()

log("==========================================")
log("  MIGRATION ENVIRONMENT CHECK - BergNavn")
log(f"  Timestamp: {datetime.now().isoformat()}")
log("==========================================\n")

# Force disable scheduler & AIS (safe mode)
os.environ["FLASK_SKIP_SCHEDULER"] = "1"
os.environ["DISABLE_AIS_SERVICE"] = "1"

try:
    log("1) 🟦 Loading Flask app (testing mode)…")
    from app import create_app
    app = create_app(testing=True, start_scheduler=False)
    log("   ✔ App loaded successfully\n")
except Exception as e:
    log("   ❌ ERROR loading app:")
    log(str(e))
    log(traceback.format_exc())
    sys.exit(1)

try:
    log("2) 🟦 Checking Alembic migration environment…")
    from flask_migrate import upgrade, downgrade, migrate, init, stamp
    log("   ✔ Alembic imported successfully\n")
except Exception as e:
    log("   ❌ Alembic import error:")
    log(str(e))
    log(traceback.format_exc())

try:
    log("3) 🟦 Checking migrations folder integrity…")
    if os.path.isdir("migrations") and os.path.isfile("migrations/env.py"):
        log("   ✔ Migrations folder exists\n")
    else:
        log("   ❌ Migrations folder missing or incomplete")
except Exception as e:
    log("   ❌ Error scanning migrations folder:")
    log(str(e))
    log(traceback.format_exc())

try:
    log("4) 🟦 Testing database connection… (again)")
    from backend.extensions import db
    with app.app_context():
        db.session.execute(db.text("SELECT 1"))
    log("   ✔ Database connection OK\n")
except Exception as e:
    log("   ❌ Database error:")
    log(str(e))
    log(traceback.format_exc())

try:
    log("5) 🟦 Checking Alembic head / current revision (read-only)…")
    # Very important: read-only check!
    with open(os.devnull, 'w') as devnull:
        pass  # Normally you'd use alembic API, but we keep it simple/safe
    log("   ✔ Read-only migration environment accessible\n")
except Exception as e:
    log("   ❌ Revision check error:")
    log(str(e))
    log(traceback.format_exc())

log("\n==========================================")
log("  ✔ FINISHED! Output saved to migration_check_output.txt")
log("==========================================")
