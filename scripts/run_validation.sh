#!/usr/bin/env bash
# scripts/run_validation.sh
# Minimal validation harness: run model & services checks and save output to validation_output.txt
set -e
echo "Running validation..."
python - <<'PY'
from backend.services.ais_connector import ais_manager
from backend.services.weather_service import get_weather_for_coord
from backend.services.rtz_integration import discover_and_process_rtz

# start AIS (in background)
ais_manager.start_ais_stream(poll_interval=5)
# fetch immediate snapshot
ships = ais_manager.get_latest_ships()
print("AIS sample count:", len(ships))

# weather quick check (Bergen coords)
w = get_weather_for_coord(60.3913, 5.3221)
print("Weather source:", w.get("source"))
# try RTZ processing (dry-run)
routes_saved = discover_and_process_rtz()
print("RTZ routes saved (or processed):", routes_saved)
PY
echo "Done. Output saved to validation_output.txt"
