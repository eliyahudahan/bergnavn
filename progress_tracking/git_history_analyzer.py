"""
Git history analysis module
Extracts and analyzes commit history for progress tracking
"""

import subprocess
import json
from datetime import datetime, timedelta
from collections import Counter
import re

class GitHistoryAnalyzer:
    """Analyzes Git commit history for progress tracking"""
    
    def __init__(self, config):
        self.config = config
    
    def analyze_recent_activity(self, days=None):
        """
        Analyze Git activity for the specified number of days
        
        Returns:
            dict: Analysis results including commits, activity patterns, etc.
        """
        if days is None:
            days = self.config.DAYS_TO_ANALYZE
        
        # Get commit history
        commits = self._get_commit_history(days)
        
        if not commits:
            return self._create_empty_analysis()
        
        # Analyze commit messages
        commit_analysis = self._analyze_commit_messages(commits)
        
        # Calculate activity metrics
        activity_metrics = self._calculate_activity_metrics(commits)
        
        # Combine all analysis
        analysis = {
            'total_commits': len(commits),
            'commits': commits,
            'commit_analysis': commit_analysis,
            'activity_metrics': activity_metrics,
            'analysis_date': datetime.now().isoformat(),
            'days_analyzed': days
        }
        
        # Save metrics to file
        self._save_metrics(analysis)
        
        return analysis
    
    def _get_commit_history(self, days):
        """Retrieve commit history from Git"""
        cmd = self.config.get_git_command(days)
        
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=self.config.PROJECT_ROOT
            )
            
            if result.returncode != 0:
                print(f"Warning: Git command failed: {result.stderr}")
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line and '|' in line:
                    date, author, message, commit_hash = line.split('|', 3)
                    commits.append({
                        'date': date,
                        'author': author,
                        'message': message.strip(),
                        'hash': commit_hash,
                        'is_meaningful': self._is_meaningful_commit(message)
                    })
            
            return commits
            
        except Exception as e:
            print(f"Error retrieving Git history: {e}")
            return []
    
    def _is_meaningful_commit(self, message):
        """Check if commit message contains meaningful content"""
        # Remove common non-meaningful patterns
        patterns_to_ignore = [
            r'^Merge',
            r'^Revert',
            r'^Update README',
            r'^minor fix',
            r'^typo',
            r'^small fix'
        ]
        
        for pattern in patterns_to_ignore:
            if re.search(pattern, message, re.IGNORECASE):
                return False
        
        # Check if message has minimum words
        words = message.split()
        return len(words) >= 3  # At least 3 words
    
    def _analyze_commit_messages(self, commits):
        """Analyze patterns in commit messages"""
        messages = [c['message'] for c in commits]
        
        # Count keywords
        keyword_counts = {}
        for keyword in self.config.TASK_KEYWORDS:
            count = sum(1 for msg in messages if keyword.lower() in msg.lower())
            if count > 0:
                keyword_counts[keyword] = count
        
        # Categorize commits by type
        commit_types = {
            'feature': sum(1 for msg in messages if any(word in msg.lower() 
                       for word in ['add', 'implement', 'create'])),
            'fix': sum(1 for msg in messages if any(word in msg.lower() 
                     for word in ['fix', 'debug', 'error'])),
            'improvement': sum(1 for msg in messages if any(word in msg.lower() 
                              for word in ['improve', 'optimize', 'refactor'])),
            'other': len(messages) - sum(keyword_counts.values())
        }
        
        return {
            'keyword_counts': keyword_counts,
            'commit_types': commit_types,
            'avg_message_length': sum(len(msg.split()) for msg in messages) / len(messages)
        }
    
    def _calculate_activity_metrics(self, commits):
        """Calculate various activity metrics"""
        if not commits:
            return {}
        
        dates = [c['date'] for c in commits]
        date_counts = Counter(dates)
        
        # Calculate streaks
        current_streak = self._calculate_current_streak(commits)
        
        return {
            'active_days': len(date_counts),
            'commits_by_day': dict(date_counts),
            'most_active_day': max(date_counts.items(), key=lambda x: x[1])[0] if date_counts else None,
            'current_streak_days': current_streak,
            'avg_commits_per_day': len(commits) / max(len(date_counts), 1),
            'last_commit_date': max(dates) if dates else None
        }
    
    def _calculate_current_streak(self, commits):
        """Calculate current consecutive days with commits"""
        if not commits:
            return 0
        
        # Get unique dates sorted
        dates = sorted(set(c['date'] for c in commits), reverse=True)
        today = datetime.now().date()
        streak = 0
        
        for i, date_str in enumerate(dates):
            commit_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if this is consecutive from today
            expected_date = today - timedelta(days=i)
            if commit_date == expected_date:
                streak += 1
            else:
                break
        
        return streak
    
    def _create_empty_analysis(self):
        """Create empty analysis structure when no commits found"""
        return {
            'total_commits': 0,
            'commits': [],
            'commit_analysis': {},
            'activity_metrics': {},
            'analysis_date': datetime.now().isoformat(),
            'days_analyzed': self.config.DAYS_TO_ANALYZE
        }
    
    def _save_metrics(self, analysis):
        """Save metrics to JSON file"""
        metrics_file = self.config.METRICS_DIR / f"metrics_{self.config.today_str}.json"
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save metrics: {e}")