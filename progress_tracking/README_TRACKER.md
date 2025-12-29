# BergNavn Progress Tracking System

## Overview

This is an automated progress tracking system for the BergNavn shipping optimization project. The system analyzes Git history, extracts learnings from project documentation, and generates progress reports.

## File Structure

progress_tracking/
├── tracker_config.py # Configuration and constants
├── git_history_analyzer.py # Git history analysis
├── learning_extractor.py # Learning extraction from YOUR_PLAN.md
├── report_generator.py # Report generation
├── daily_summary.py # Daily summary creation
├── auto_backup.py # Auto-backup functionality
└── README_TRACKER.md # This file

progress/ # Generated files
├── weekly_report.md # Weekly progress report
├── daily_summaries/ # Daily JSON summaries
├── learnings/ # Extracted learnings
├── metrics/ # Analysis metrics
└── backups/ # Backup files



## Usage

### Quick Start

1. **First Time Setup**:
   ```bash
   # Make the main tracker executable
   chmod +x git_progress_tracker.py
   
   # Run the tracker
   python3 git_progress_tracker.py

# Update your plan file first
nano YOUR_PLAN.md

# Run the tracker to analyze progress
python3 git_progress_tracker.py

# View the generated report
cat progress/weekly_report.md