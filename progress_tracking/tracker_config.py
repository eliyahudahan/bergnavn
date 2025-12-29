"""
Configuration and constants for the progress tracking system
"""

import os
from pathlib import Path

class Config:
    """Configuration settings for the tracker"""
    
    def __init__(self):
        # Project root directory (where this script is located)
        self.PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(__file__)))
        
        # File paths
        self.PLAN_FILE = self.PROJECT_ROOT / "your_plan.md"
        self.PROGRESS_DIR = self.PROJECT_ROOT / "progress"
        self.DAILY_SUMMARY_DIR = self.PROGRESS_DIR / "daily_summaries"
        self.LEARNINGS_DIR = self.PROGRESS_DIR / "learnings"
        self.METRICS_DIR = self.PROGRESS_DIR / "metrics"
        self.BACKUP_DIR = self.PROGRESS_DIR / "backups"
        
        # Analysis settings
        self.DAYS_TO_ANALYZE = 30
        self.COMMIT_WORD_THRESHOLD = 50  # Minimum words for meaningful commit
        
        # ✅ UPDATED: BergNavn-specific keywords for analysis
        self.LEARNING_KEYWORDS = [
            'learned', 'discovered', 'found', 'realized', 
            'figured out', 'understood', 'note:', 'important:',
            # BergNavn specific
            'turbine', 'tanker', 'AIS', 'weather', 'maritime',
            'route', 'optimization', 'risk', 'fuel', 'safety',
            'norwegian', 'bergen', 'shipping', 'commercial',
            'vessel', 'ship', 'nautical', 'navigation', 'sea',
            'ocean', 'wave', 'wind', 'current', 'tide',
            'docking', 'port', 'harbor', 'cargo', 'logistics',
            'efficiency', 'savings', 'ROI', 'cost', 'economic',
            'environmental', 'regulation', 'compliance', 'law',
            'api', 'integration', 'data', 'pipeline', 'real-time'
        ]
        
        self.TASK_KEYWORDS = [
            'fix', 'add', 'update', 'implement', 'create',
            'improve', 'refactor', 'optimize', 'debug',
            # BergNavn specific
            'integrate', 'connect', 'build', 'develop', 'design',
            'calculate', 'compute', 'analyze', 'process', 'collect',
            'fetch', 'retrieve', 'display', 'show', 'visualize',
            'map', 'plot', 'chart', 'graph', 'simulate',
            'test', 'verify', 'validate', 'check', 'ensure',
            'deploy', 'run', 'execute', 'launch', 'start',
            'configure', 'setup', 'install', 'prepare', 'organize',
            'document', 'explain', 'describe', 'summarize', 'report'
        ]
        
        # Ensure directories exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.PROGRESS_DIR,
            self.DAILY_SUMMARY_DIR,
            self.LEARNINGS_DIR,
            self.METRICS_DIR,
            self.BACKUP_DIR
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    def get_git_command(self, days=30):
        """Get git command for history analysis"""
        return f'git log --since="{days} days ago" --pretty=format:"%ad|%an|%s|%H" --date=short'
    
    @property
    def today_str(self):
        """Get today's date as string"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
    
    @property
    def project_keywords(self):
        """Get project-specific keywords for categorization"""
        return {
            'data_pipeline': ['AIS', 'weather', 'api', 'data', 'pipeline', 'fetch'],
            'risk_engine': ['risk', 'safety', 'danger', 'hazard', 'warning', 'alert'],
            'optimization': ['optimize', 'efficient', 'save', 'fuel', 'cost', 'ROI'],
            'visualization': ['map', 'chart', 'display', 'show', 'dashboard', 'plot'],
            'maritime': ['ship', 'vessel', 'nautical', 'navigation', 'sea', 'port'],
            'norway': ['bergen', 'norwegian', 'norway', 'oslo', 'trondheim', 'stavanger']
        }