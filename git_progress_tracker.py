#!/usr/bin/env python3
"""
🚢 BergNavn - Git Progress Tracker
📊 Automated progress tracking system for data science projects
Main entry point - run this to track your progress
"""

import os
import sys
import subprocess
from datetime import datetime

# Add the tracking module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'progress_tracking'))

from tracker_config import Config
from git_history_analyzer import GitHistoryAnalyzer
from learning_extractor import LearningExtractor
from report_generator import ReportGenerator
from daily_summary import DailySummaryGenerator
from auto_backup import AutoBackup

class ProgressTracker:
    """Main progress tracking system"""
    
    def __init__(self):
        self.config = Config()
        self.analyzer = GitHistoryAnalyzer(self.config)
        self.learning_extractor = LearningExtractor(self.config)
        self.reporter = ReportGenerator(self.config)
        self.summarizer = DailySummaryGenerator(self.config)
        self.backup = AutoBackup(self.config)
        
    def run_full_analysis(self, sync_git=True):
        """
        Run complete progress analysis
        
        Args:
            sync_git (bool): Whether to sync with Git first
        """
        print("=" * 60)
        print("🚢 BergNavn - Progress Tracking System")
        print("=" * 60)
        
        # 0. Sync with Git if requested
        if sync_git:
            print("\n🔄 Step 0: Syncing with Git...")
            self._sync_with_git()
        
        # 1. Analyze Git history
        print("\n📊 Step 1: Analyzing Git history...")
        git_data = self.analyzer.analyze_recent_activity()
        
        # 2. Extract learnings from your plan
        print("📝 Step 2: Extracting learnings from YOUR_PLAN.md...")
        learnings = self.learning_extractor.extract_todays_learnings()
        
        # 3. Generate reports
        print("📈 Step 3: Generating progress reports...")
        self.reporter.generate_weekly_report(git_data, learnings)
        
        # 4. Create daily summary
        print("📋 Step 4: Creating daily summary...")
        self.summarizer.create_daily_summary(git_data, learnings)
        
        # 5. Auto-backup tracking data
        print("💾 Step 5: Creating backup...")
        self.backup.create_backup()
        
        # 6. Show summary
        self._display_summary(git_data, learnings)
        
    def _sync_with_git(self):
        """Run your existing git_backup.sh script"""
        git_script = os.path.join(self.config.PROJECT_ROOT, "git_backup.sh")
        
        if os.path.exists(git_script):
            try:
                # Run the git backup script
                result = subprocess.run(
                    ['bash', git_script],
                    cwd=self.config.PROJECT_ROOT,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("✅ Git sync completed successfully")
                else:
                    print(f"⚠️  Git sync had issues: {result.stderr[:100]}")
                    
            except Exception as e:
                print(f"⚠️  Could not run git_backup.sh: {e}")
        else:
            print("ℹ️  git_backup.sh not found, continuing without Git sync")
    
    def _display_summary(self, git_data, learnings):
        """Display summary of analysis"""
        print("\n" + "=" * 60)
        print("✅ Progress Tracking Complete!")
        print("=" * 60)
        
        print(f"\n📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if git_data:
            print(f"\n📊 Git Activity (Last {self.config.DAYS_TO_ANALYZE} days):")
            print(f"   • Total Commits: {git_data.get('total_commits', 0)}")
            print(f"   • Active Days: {git_data.get('active_days', 0)}")
            print(f"   • Most Active Day: {git_data.get('most_active_day', 'N/A')}")
            
            # Show BergNavn specific analysis
            print(f"\n🎯 BergNavn Project Analysis:")
            project_keywords = self.config.project_keywords
            for category, keywords in project_keywords.items():
                related_commits = self._count_related_commits(git_data, keywords)
                if related_commits > 0:
                    print(f"   • {category.replace('_', ' ').title()}: {related_commits} commit(s)")
        
        if learnings:
            print(f"\n📝 Today's Learnings: {len(learnings)} item(s)")
            for i, learning in enumerate(learnings[:3], 1):
                print(f"   {i}. {learning[:80]}..." if len(learning) > 80 else f"   {i}. {learning}")
        
        print(f"\n📁 Generated Files:")
        print(f"   • Weekly Report: progress/weekly_report.md")
        print(f"   • Daily Summary: progress/daily_summaries/")
        print(f"   • Learnings: progress/learnings/")
        print(f"   • Metrics: progress/metrics/")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Review report: cat progress/weekly_report.md")
        print(f"   2. Update YOUR_PLAN.md with today's progress")
        print(f"   3. Run tracker again tomorrow")
    
    def _count_related_commits(self, git_data, keywords):
        """Count commits related to specific keywords"""
        if not git_data or not git_data.get('commits'):
            return 0
        
        count = 0
        for commit in git_data.get('commits', []):
            message = commit.get('message', '').lower()
            if any(keyword.lower() in message for keyword in keywords):
                count += 1
        
        return count

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BergNavn Progress Tracker')
    parser.add_argument('--no-git-sync', action='store_true', 
                       help='Skip Git synchronization')
    
    args = parser.parse_args()
    
    tracker = ProgressTracker()
    tracker.run_full_analysis(sync_git=not args.no_git_sync)

if __name__ == "__main__":
    main()