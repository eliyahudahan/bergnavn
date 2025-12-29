"""
Daily summary generation module
Creates daily progress summaries
"""

import json
from datetime import datetime

class DailySummaryGenerator:
    """Generates daily progress summaries"""
    
    def __init__(self, config):
        self.config = config
    
    def create_daily_summary(self, git_data, learnings):
        """Create daily summary of progress"""
        
        summary = {
            'date': self.config.today_str,
            'timestamp': datetime.now().isoformat(),
            'git_activity': self._summarize_git_activity(git_data),
            'learnings': learnings,
            'plan_status': self._check_plan_status(),
            'metrics': self._calculate_daily_metrics(git_data)
        }
        
        # Save summary to file
        self._save_daily_summary(summary)
        
        return summary
    
    def _summarize_git_activity(self, git_data):
        """Summarize Git activity for the day"""
        if not git_data or not git_data.get('commits'):
            return {'has_activity': False, 'commit_count': 0}
        
        today = self.config.today_str
        todays_commits = [c for c in git_data.get('commits', []) 
                         if c.get('date') == today]
        
        return {
            'has_activity': len(todays_commits) > 0,
            'commit_count': len(todays_commits),
            'commits': todays_commits[:5],  # First 5 commits
            'meaningful_commits': sum(1 for c in todays_commits 
                                    if c.get('is_meaningful', False))
        }
    
    def _check_plan_status(self):
        """Check if plan file was updated today"""
        if not self.config.PLAN_FILE.exists():
            return {'exists': False, 'updated_today': False}
        
        try:
            # Get file modification time
            mtime = self.config.PLAN_FILE.stat().st_mtime
            mod_date = datetime.fromtimestamp(mtime).date()
            today = datetime.now().date()
            
            return {
                'exists': True,
                'updated_today': mod_date == today,
                'last_modified': datetime.fromtimestamp(mtime).isoformat()
            }
            
        except Exception:
            return {'exists': True, 'updated_today': False}
    
    def _calculate_daily_metrics(self, git_data):
        """Calculate daily metrics"""
        metrics = {
            'analysis_date': self.config.today_str,
            'total_learnings': 0,
            'productivity_score': 0
        }
        
        if git_data and git_data.get('commits'):
            todays_commits = [c for c in git_data.get('commits', []) 
                            if c.get('date') == self.config.today_str]
            
            # Simple productivity score
            commit_score = len(todays_commits) * 10
            meaningful_score = sum(1 for c in todays_commits 
                                 if c.get('is_meaningful', False)) * 20
            
            metrics['productivity_score'] = commit_score + meaningful_score
            metrics['daily_commits'] = len(todays_commits)
        
        return metrics
    
    def _save_daily_summary(self, summary):
        """Save daily summary to file"""
        filename = self.config.DAILY_SUMMARY_DIR / f"summary_{self.config.today_str}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"📋 Daily summary saved: {filename}")
            
        except Exception as e:
            print(f"Error saving daily summary: {e}")