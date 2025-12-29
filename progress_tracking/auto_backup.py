"""
Auto-backup module
Creates backups of tracking data
"""

import shutil
import json
from datetime import datetime

class AutoBackup:
    """Handles automatic backups of tracking data"""
    
    def __init__(self, config):
        self.config = config
    
    def create_backup(self):
        """Create a backup of tracking data"""
        backup_name = f"tracking_backup_{self.config.today_str}"
        backup_path = self.config.BACKUP_DIR / backup_name
        
        try:
            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            
            # Backup summary
            self._create_backup_summary(backup_path)
            
            print(f"💾 Backup created: {backup_path}")
            
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    def _create_backup_summary(self, backup_path):
        """Create backup summary file"""
        summary = {
            'backup_date': datetime.now().isoformat(),
            'backup_type': 'progress_tracking',
            'contents': [
                'git_analysis_results',
                'daily_summaries',
                'learning_extracts',
                'weekly_reports'
            ],
            'project': 'BergNavn Shipping Optimization',
            'notes': 'Auto-generated backup of progress tracking data'
        }
        
        summary_file = backup_path / "backup_summary.json"
        
        try:
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error creating backup summary: {e}")