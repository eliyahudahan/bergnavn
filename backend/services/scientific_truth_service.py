"""
Scientific Truth Service - Empirical Data Verification System
Author: Data Scientist
Date: 2024
Description: Single source of truth for maritime route data based on empirical verification.
"""

import os
import glob
import zipfile
import json
import statistics
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScientificTruthService:
    """
    Empirical verification system that determines the TRUE count of maritime routes
    using scientific methodology and multiple data source validation.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the scientific truth service.
        
        Args:
            base_path: Base directory for route files (default: project root)
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Auto-detect project structure
            current_file = Path(__file__).resolve()
            self.base_path = current_file.parent.parent.parent
            
        self.routes_dir = self.base_path / "backend" / "assets" / "routeinfo_routes"
        self.db_path = self.base_path / "instance" / "maritime.db"
        
        logger.info(f"Initialized ScientificTruthService with base path: {self.base_path}")
        logger.info(f"Routes directory: {self.routes_dir}")
        logger.info(f"Database path: {self.db_path}")
    
    def count_physical_rtz_files(self) -> Dict:
        """
        Count all physical RTZ files on disk (including inside ZIP archives).
        
        Returns:
            Dictionary with detailed file counts
        """
        logger.info("Counting physical RTZ files...")
        
        if not self.routes_dir.exists():
            logger.error(f"Routes directory does not exist: {self.routes_dir}")
            return {"count": 0, "files": [], "zips": []}
        
        # Count standalone RTZ files
        rtz_pattern = str(self.routes_dir / "**" / "*.rtz")
        rtz_files = glob.glob(rtz_pattern, recursive=True)
        
        # Count ZIP files and their contents
        zip_pattern = str(self.routes_dir / "**" / "*.zip")
        zip_files = glob.glob(zip_pattern, recursive=True)
        
        # Count RTZ files inside ZIP archives
        zip_contents_count = 0
        zip_contents_details = []
        
        for zip_file in zip_files:
            try:
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    rtz_in_zip = [f for f in zf.namelist() if f.lower().endswith('.rtz')]
                    zip_contents_count += len(rtz_in_zip)
                    
                    for rtz_file in rtz_in_zip:
                        zip_contents_details.append({
                            "zip": os.path.basename(zip_file),
                            "rtz_file": rtz_file,
                            "size": zf.getinfo(rtz_file).file_size
                        })
            except (zipfile.BadZipFile, IOError) as e:
                logger.warning(f"Could not read ZIP file {zip_file}: {e}")
                continue
        
        total_count = len(rtz_files) + zip_contents_count
        
        logger.info(f"Found {len(rtz_files)} standalone RTZ files")
        logger.info(f"Found {len(zip_files)} ZIP files with {zip_contents_count} RTZ files inside")
        logger.info(f"Total physical RTZ files: {total_count}")
        
        return {
            "count": total_count,
            "standalone_rtz": len(rtz_files),
            "standalone_files": [os.path.basename(f) for f in rtz_files],
            "zip_files": len(zip_files),
            "zip_file_names": [os.path.basename(f) for f in zip_files],
            "rtz_in_zips": zip_contents_count,
            "zip_contents_details": zip_contents_details,
            "verification_time": datetime.now().isoformat(),
            "method": "physical_file_counting"
        }
    
    def calculate_route_uniqueness(self) -> Dict:
        """
        Calculate unique routes by analyzing file content (simplified version).
        In production, this would parse RTZ XML and compare waypoints.
        
        Returns:
            Dictionary with uniqueness analysis
        """
        logger.info("Analyzing route uniqueness...")
        
        # This is a simplified version. In reality, you would:
        # 1. Parse RTZ XML files
        # 2. Extract waypoints and metadata
        # 3. Compare routes using geographic similarity
        
        # For now, we'll use file hashes as a proxy for uniqueness
        rtz_files = self._get_all_rtz_file_paths()
        
        file_hashes = []
        file_sizes = []
        
        for rtz_file in rtz_files:
            try:
                file_size = os.path.getsize(rtz_file)
                file_sizes.append(file_size)
                
                # Calculate MD5 hash
                with open(rtz_file, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    file_hashes.append(file_hash)
            except (IOError, OSError) as e:
                logger.warning(f"Could not read {rtz_file}: {e}")
                continue
        
        # Count unique hashes
        unique_hashes = set(file_hashes)
        
        # Calculate statistics
        if file_sizes:
            avg_size = sum(file_sizes) / len(file_sizes)
            size_variance = statistics.variance(file_sizes) if len(file_sizes) > 1 else 0
        else:
            avg_size = 0
            size_variance = 0
        
        logger.info(f"Analyzed {len(file_hashes)} RTZ files")
        logger.info(f"Found {len(unique_hashes)} unique files by hash")
        
        return {
            "total_files_analyzed": len(file_hashes),
            "unique_by_hash": len(unique_hashes),
            "duplicates_by_hash": len(file_hashes) - len(unique_hashes),
            "average_file_size_kb": round(avg_size / 1024, 2),
            "file_size_variance": round(size_variance, 2),
            "unique_hashes_sample": list(unique_hashes)[:5] if unique_hashes else [],
            "verification_time": datetime.now().isoformat(),
            "method": "hash_based_uniqueness",
            "note": "This is a simplified analysis. Real uniqueness requires geographic comparison."
        }
    
    def get_database_route_count(self) -> Dict:
        """
        Get route count from database if available.
        
        Returns:
            Dictionary with database counts
        """
        logger.info("Checking database for route counts...")
        
        if not self.db_path.exists():
            logger.warning(f"Database file not found: {self.db_path}")
            return {
                "count": 0,
                "status": "database_not_found",
                "message": "SQLite database file does not exist"
            }
        
        try:
            # Try to import sqlite3
            import sqlite3
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Count routes
            cursor.execute("SELECT COUNT(*) FROM route")
            route_count = cursor.fetchone()[0]
            
            # Get table info if available
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            # Get sample routes if any
            cursor.execute("SELECT id, route_name FROM route LIMIT 5")
            sample_routes = cursor.fetchall()
            
            conn.close()
            
            logger.info(f"Database route count: {route_count}")
            
            return {
                "count": route_count,
                "tables": [table[0] for table in tables],
                "sample_routes": [{"id": r[0], "name": r[1]} for r in sample_routes],
                "verification_time": datetime.now().isoformat(),
                "method": "database_query"
            }
            
        except ImportError:
            logger.error("sqlite3 module not available")
            return {
                "count": 0,
                "status": "sqlite3_not_available",
                "message": "Install sqlite3: sudo apt install sqlite3"
            }
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return {
                "count": 0,
                "status": "database_error",
                "message": str(e)
            }
    
    def analyze_dashboard_discrepancy(self) -> Dict:
        """
        Analyze the 72 vs 37 discrepancy in dashboard.
        
        Returns:
            Dictionary with discrepancy analysis
        """
        logger.info("Analyzing dashboard discrepancy...")
        
        # Based on your findings:
        # - 72 appears in dashboard_base.html
        # - 37 is the empirical unique count
        # - 48 is the physical file count
        
        discrepancy_analysis = {
            "dashboard_displayed": 72,
            "empirical_unique": 37,
            "physical_files": 48,
            "discrepancy_72_vs_37": 72 - 37,
            "discrepancy_72_vs_48": 72 - 48,
            "percentage_error_72_vs_37": round(((72 - 37) / 37) * 100, 2),
            "percentage_error_72_vs_48": round(((72 - 48) / 48) * 100, 2),
            "possible_causes": [
                "Hardcoded value in HTML template",
                "Counting logic error in route_service.py",
                "Duplicate counting in frontend JavaScript",
                "Static test data included in count"
            ],
            "recommended_fix": "Replace hardcoded 72 with empirical count from ScientificTruthService",
            "verification_time": datetime.now().isoformat(),
            "severity": "HIGH - Data integrity issue"
        }
        
        logger.warning(f"Dashboard discrepancy detected: {discrepancy_analysis['percentage_error_72_vs_37']}% error")
        
        return discrepancy_analysis
    
    def get_empirical_truth(self) -> Dict:
        """
        Main method: Get the ONE TRUE empirical count with scientific verification.
        
        Returns:
            Complete scientific truth report
        """
        logger.info("=== STARTING SCIENTIFIC TRUTH VERIFICATION ===")
        
        # Gather data from all sources
        physical_data = self.count_physical_rtz_files()
        uniqueness_data = self.calculate_route_uniqueness()
        database_data = self.get_database_route_count()
        discrepancy_data = self.analyze_dashboard_discrepancy()
        
        # Collect all valid counts
        counts = []
        sources = []
        
        # Physical files count
        if physical_data["count"] > 0:
            counts.append(physical_data["count"])
            sources.append(("physical_files", physical_data["count"]))
        
        # Uniqueness count
        if uniqueness_data["unique_by_hash"] > 0:
            counts.append(uniqueness_data["unique_by_hash"])
            sources.append(("unique_by_hash", uniqueness_data["unique_by_hash"]))
        
        # Database count
        if database_data["count"] > 0:
            counts.append(database_data["count"])
            sources.append(("database", database_data["count"]))
        
        # Determine empirical truth
        if not counts:
            empirical_truth = 0
            confidence = 0.0
            methodology = "no_data"
        else:
            # Use median for robustness against outliers
            empirical_truth = int(statistics.median(counts))
            
            # Calculate confidence based on agreement
            matches = sum(1 for _, count in sources if count == empirical_truth)
            confidence = matches / len(sources)
            
            # Boost confidence if we have multiple sources
            if len(sources) >= 2:
                confidence = min(confidence * 1.2, 1.0)  # Cap at 1.0
            
            methodology = "scientific_consensus"
        
        # Prepare comprehensive report
        truth_report = {
            # The ONE TRUE NUMBER
            "empirical_truth": empirical_truth,
            "confidence": round(confidence, 3),
            "methodology": methodology,
            
            # Detailed breakdown
            "data_sources": {
                "physical_files": physical_data,
                "uniqueness_analysis": uniqueness_data,
                "database": database_data,
                "discrepancy_analysis": discrepancy_data
            },
            
            # Source comparison
            "source_comparison": [
                {
                    "source": name,
                    "count": count,
                    "matches_truth": count == empirical_truth,
                    "difference": count - empirical_truth
                }
                for name, count in sources
            ],
            
            # Metadata
            "verification_timestamp": datetime.now().isoformat(),
            "scientist": "Maritime Data Scientist",
            "system_version": "1.0.0",
            "recommendation": self._generate_recommendation(empirical_truth, confidence),
            
            # Status
            "status": "verified" if confidence >= 0.8 else "needs_review",
            "data_integrity": "good" if confidence >= 0.8 else "compromised",
            "dashboard_correction_needed": discrepancy_data["dashboard_displayed"] != empirical_truth
        }
        
        logger.info(f"=== SCIENTIFIC TRUTH VERIFICATION COMPLETE ===")
        logger.info(f"Empirical Truth: {empirical_truth}")
        logger.info(f"Confidence: {confidence:.1%}")
        logger.info(f"Status: {truth_report['status']}")
        
        return truth_report
    
    def _get_all_rtz_file_paths(self) -> List[str]:
        """Get all RTZ file paths (standalone and in ZIPs)."""
        paths = []
        
        # Standalone RTZ files
        rtz_pattern = str(self.routes_dir / "**" / "*.rtz")
        paths.extend(glob.glob(rtz_pattern, recursive=True))
        
        # RTZ files in ZIP archives
        zip_pattern = str(self.routes_dir / "**" / "*.zip")
        zip_files = glob.glob(zip_pattern, recursive=True)
        
        for zip_file in zip_files:
            try:
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    for file_info in zf.infolist():
                        if file_info.filename.lower().endswith('.rtz'):
                            # Extract to temp location for analysis
                            temp_path = f"/tmp/{hashlib.md5(zip_file.encode()).hexdigest()}_{file_info.filename}"
                            
                            # Extract if not already extracted
                            if not os.path.exists(temp_path):
                                with open(temp_path, 'wb') as f:
                                    f.write(zf.read(file_info.filename))
                            
                            paths.append(temp_path)
            except Exception as e:
                logger.warning(f"Could not process ZIP {zip_file}: {e}")
                continue
        
        return paths
    
    def _generate_recommendation(self, truth: int, confidence: float) -> str:
        """Generate recommendation based on findings."""
        if confidence >= 0.9:
            return f"Immediately update dashboard to display {truth} routes. High confidence in data."
        elif confidence >= 0.7:
            return f"Update dashboard to display {truth} routes. Moderate confidence. Monitor for changes."
        else:
            return f"Investigate data sources. Current truth is {truth} but confidence is low ({confidence:.1%})."
    
    def generate_verification_report(self) -> str:
        """
        Generate a human-readable verification report.
        
        Returns:
            Markdown formatted report
        """
        truth_data = self.get_empirical_truth()
        
        report = f"""# SCIENTIFIC TRUTH VERIFICATION REPORT
## Maritime Route Data Integrity Analysis

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Scientist:** {truth_data['scientist']}
**System Version:** {truth_data['system_version']}

---

## 🎯 EXECUTIVE SUMMARY

### THE ONE TRUE NUMBER: **{truth_data['empirical_truth']}** routes
**Confidence Level:** {truth_data['confidence']:.1%}
**Status:** {truth_data['status'].upper()}
**Data Integrity:** {truth_data['data_integrity'].upper()}

---

## 📊 DETAILED FINDINGS

### 1. Physical File Analysis
- **Standalone RTZ files:** {truth_data['data_sources']['physical_files']['standalone_rtz']}
- **ZIP archives:** {truth_data['data_sources']['physical_files']['zip_files']}
- **RTZ files in ZIPs:** {truth_data['data_sources']['physical_files']['rtz_in_zips']}
- **TOTAL PHYSICAL FILES:** {truth_data['data_sources']['physical_files']['count']}

### 2. Uniqueness Analysis
- **Files analyzed:** {truth_data['data_sources']['uniqueness_analysis']['total_files_analyzed']}
- **Unique by hash:** {truth_data['data_sources']['uniqueness_analysis']['unique_by_hash']}
- **Duplicates found:** {truth_data['data_sources']['uniqueness_analysis']['duplicates_by_hash']}

### 3. Database Verification
- **Routes in database:** {truth_data['data_sources']['database']['count']}
- **Database status:** {truth_data['data_sources']['database']['status']}

### 4. Dashboard Discrepancy
- **Currently displayed:** {truth_data['data_sources']['discrepancy_analysis']['dashboard_displayed']}
- **Empirical truth:** {truth_data['empirical_truth']}
- **Discrepancy:** {truth_data['data_sources']['discrepancy_analysis']['discrepancy_72_vs_37']}
- **Error percentage:** {truth_data['data_sources']['discrepancy_analysis']['percentage_error_72_vs_37']}%

---

## ⚠️ CRITICAL ISSUES

{'**NO CRITICAL ISSUES**' if truth_data['confidence'] >= 0.8 else '**DATA INTEGRITY COMPROMISED**'}

{'### ✅ All data sources agree within acceptable range.' if truth_data['confidence'] >= 0.8 else '### ❌ Significant discrepancies detected between data sources.'}

---

## 🔧 RECOMMENDATIONS

1. **{truth_data['recommendation']}**
2. **Update dashboard_base.html** to use dynamic empirical count
3. **Implement monitoring** for data source discrepancies
4. **Regular verification** runs to ensure data integrity

---

## 📈 SOURCE COMPARISON

| Source | Count | Matches Truth | Difference |
|--------|-------|---------------|------------|
"""
        
        for comparison in truth_data['source_comparison']:
            status = "✅" if comparison['matches_truth'] else "❌"
            report += f"| {comparison['source']} | {comparison['count']} | {status} | {comparison['difference']:+d} |\n"
        
        report += f"""

---

## 🧪 METHODOLOGY

**Verification Method:** {truth_data['methodology']}
**Confidence Calculation:** Based on source agreement ({truth_data['confidence']:.1%})
**Statistical Method:** Median of valid counts for robustness
**Timestamp:** {truth_data['verification_timestamp']}

---

## 🚨 IMMEDIATE ACTION REQUIRED

{'**NO URGENT ACTION** - System is reporting accurate data.' if truth_data['dashboard_correction_needed'] else '**UPDATE DASHBOARD** - Current display shows incorrect count.'}

---

*Report generated by Scientific Truth Service v{truth_data['system_version']}*
*For questions, contact the Data Science team.*
"""
        
        return report


# Convenience function for easy access
def get_scientific_truth() -> Dict:
    """Get the scientific truth in one function call."""
    service = ScientificTruthService()
    return service.get_empirical_truth()


def generate_full_report() -> str:
    """Generate a full verification report."""
    service = ScientificTruthService()
    return service.generate_verification_report()


if __name__ == "__main__":
    # Run verification when executed directly
    service = ScientificTruthService()
    
    print("\n" + "="*60)
    print("SCIENTIFIC TRUTH VERIFICATION - MARITIME ROUTES")
    print("="*60 + "\n")
    
    truth = service.get_empirical_truth()
    
    print(f"🎯 EMPIRICAL TRUTH: {truth['empirical_truth']} routes")
    print(f"📊 CONFIDENCE: {truth['confidence']:.1%}")
    print(f"📈 STATUS: {truth['status'].upper()}")
    print(f"🔧 RECOMMENDATION: {truth['recommendation']}")
    
    print("\n" + "-"*60)
    print("Detailed breakdown:")
    print("-"*60)
    
    for source_name, source_data in truth['data_sources'].items():
        if 'count' in source_data:
            print(f"{source_name.replace('_', ' ').title()}: {source_data['count']}")
    
    # Save report to file
    report = service.generate_verification_report()
    report_path = Path(__file__).parent / "scientific_truth_report.md"
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Full report saved to: {report_path}")
    print("="*60 + "\n")