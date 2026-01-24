#!/bin/bash
# Backup script for simulation files
BACKUP_DIR="simulation_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Backing up simulation files to: $BACKUP_DIR"

# Backup template
cp backend/templates/maritime_split/realtime_simulation.html "$BACKUP_DIR/"

# Backup JS files
cp backend/static/js/split/simulation_core.js "$BACKUP_DIR/" 2>/dev/null || true
cp backend/static/js/split/turbine_alerts.js "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Backup complete:"
ls -la "$BACKUP_DIR/"
