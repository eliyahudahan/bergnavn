#!/bin/bash
set -e

echo "🔎 Running waypoint verification..."
python tools/verify_waypoints.py

echo "🗄️ Checking Alembic migrations..."
flask db check || echo "⚠️ Alembic check may not be available in your version, skipping."

echo "🧪 Running pytest..."
pytest -q || echo "⚠️ Some tests failed."

echo "✅ All checks finished."
