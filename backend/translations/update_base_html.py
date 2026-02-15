#!/usr/bin/env python3
"""
Update base.html with translation calls.
This script manually replaces hardcoded text with {{ t() }} calls
since the automatic transformation didn't work properly.
"""
import re
import os
import shutil
from datetime import datetime

def update_base_html():
    """Update base.html with translation function calls."""
    
    base_file = "backend/templates/base.html"
    
    # Check if file exists
    if not os.path.exists(base_file):
        print(f"❌ Error: {base_file} not found")
        return False
    
    # Read the original file
    try:
        with open(base_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Create a backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{base_file}.backup_{timestamp}"
    shutil.copy2(base_file, backup_file)
    print(f"📦 Backup created: {backup_file}")
    
    # Define replacement patterns
    # Format: (pattern_to_search, replacement, description)
    replacements = [
        # Logo and branding
        (r'(<span class="fw-bold">)BergNavn(</span>)', 
         r'\1{{ t("bergnavn", "base_template") }}\2',
         "BergNavn logo text"),
        
        (r'(<small[^>]*>)Maritime Intelligence(</small>)',
         r'\1{{ t("maritime_intelligence", "base_template") }}\2',
         "Maritime Intelligence subtitle"),
        
        # Navigation items
        (r'(<span class="fw-semibold">)Dashboard(</span>)',
         r'\1{{ t("dashboard", "base_template") }}\2',
         "Dashboard navigation"),
        
        (r'(<span class="fw-semibold">)Simulation(</span>)',
         r'\1{{ t("simulation", "base_template") }}\2',
         "Simulation navigation"),
        
        (r'(<span class="fw-semibold">)Routes(</span>)',
         r'\1{{ t("routes", "base_template") }}\2',
         "Routes navigation"),
        
        (r'(<span class="fw-semibold">)Home(</span>)',
         r'\1{{ t("home", "base_template") }}\2',
         "Home navigation"),
        
        # Language selector
        (r'(<i class="bi bi-flag[^>]*></i>\s*)English',
         r'\1{{ t("english", "base_template") }}',
         "English language option"),
        
        (r'(<i class="bi bi-flag-fill[^>]*></i>\s*)Norsk',
         r'\1{{ t("norsk", "base_template") }}',
         "Norwegian language option"),
        
        # Footer content
        (r'(<h6 class="mb-0 fw-bold">)BergNavn Maritime(</h6>)',
         r'\1{{ t("bergnavn_maritime", "base_template") }}\2',
         "Footer title"),
        
        (r'(<small class="opacity-75">)Intelligent Route Optimization System(</small>)',
         r'\1{{ t("intelligent_route_optimization", "base_template") }}\2',
         "Footer subtitle"),
        
        (r'(<i class="bi bi-geo-alt me-1"></i>\s*<span[^>]*>)Norwegian Ports:[^<]*(</span>)',
         r'\1{{ t("norwegian_ports", "base_template") }}\2',
         "Norwegian ports list"),
        
        (r'(<i class="bi bi-cpu me-1"></i>)Flask[^<]*(</small>)',
         r'\1{{ t("technology_stack", "base_template") }}\2',
         "Technology stack"),
        
        (r'(<small class="d-block fw-semibold">)System Status(</small>)',
         r'\1{{ t("system_status", "base_template") }}\2',
         "System Status label"),
        
        (r'(<span id="status-text">)All Systems Operational(</span>)',
         r'\1{{ t("all_systems_operational", "base_template") }}\2',
         "All Systems Operational status"),
        
        (r'(<i class="bi bi-clock me-1"></i>\s*<span[^>]*>)Data updated:(</span>)',
         r'\1{{ t("data_updated", "base_template") }}:\2',
         "Data updated label"),
        
        (r'(<i class="bi bi-code-slash me-1"></i>)API Status:',
         r'\1{{ t("api_status", "base_template") }}:',
         "API Status label"),
        
        (r'(<span class="badge bg-success"[^>]*>)Active(</span>)',
         r'\1{{ t("active", "base_template") }}\2',
         "Active status badge"),
        
        (r'(<small class="opacity-75">)© 2025 BergNavn Maritime \| Research & Development Platform(</small>)',
         r'\1{{ t("copyright", "base_template") }} | {{ t("research_development", "base_template") }}\2',
         "Copyright and platform info"),
        
        (r'(<i class="bi bi-shield-check me-1"></i>\s*)Data sources:[^<]*(</small>)',
         r'\1{{ t("data_sources", "base_template") }}\2',
         "Data sources"),
        
        # Footer links
        (r'(<a[^>]*>)\s*About\s*(</a>)',
         r'\1{{ t("about", "base_template") }}\2',
         "About link"),
        
        (r'(<a[^>]*>)\s*Contact\s*(</a>)',
         r'\1{{ t("contact", "base_template") }}\2',
         "Contact link"),
        
        (r'(<a[^>]*>)\s*Legal\s*(</a>)',
         r'\1{{ t("legal", "base_template") }}\2',
         "Legal link"),
    ]
    
    # Apply replacements
    new_content = content
    changes_made = 0
    
    for pattern, replacement, description in replacements:
        # Check if pattern exists
        if re.search(pattern, new_content):
            new_content, count = re.subn(pattern, replacement, new_content)
            if count > 0:
                changes_made += count
                print(f"✅ Replaced: {description}")
    
    # Also update JavaScript strings
    js_replacements = [
        (r"'All Systems Operational'", "{{ t('all_systems_operational', 'base_template') }}"),
        (r"'Service Degraded'", "{{ t('service_degraded', 'base_template') }}"),
        (r"'API Connection Failed'", "{{ t('api_connection_failed', 'base_template') }}"),
        (r"'Active'", "{{ t('active', 'base_template') }}"),
        (r"'Partial'", "{{ t('partial', 'base_template') }}"),
        (r"'Offline'", "{{ t('offline', 'base_template') }}"),
        (r"'Data updated:'", "{{ t('data_updated', 'base_template') }}:"),
    ]
    
    for old, new in js_replacements:
        if old in new_content:
            new_content = new_content.replace(old, new)
            changes_made += 1
            print(f"✅ Updated JavaScript string: {old}")
    
    # Write the updated file
    try:
        with open(base_file, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        # Restore from backup
        shutil.copy2(backup_file, base_file)
        print("⚠️  Restored original from backup")
        return False
    
    print(f"\n📊 Summary: Made {changes_made} replacements")
    
    if changes_made == 0:
        print("⚠️  No changes were made. The file might already be updated.")
        # Delete the backup since no changes were made
        os.remove(backup_file)
        print("🗑️  Deleted backup (no changes made)")
    
    return changes_made > 0

def verify_changes():
    """Verify that changes were made correctly."""
    base_file = "backend/templates/base.html"
    
    try:
        with open(base_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for some key replacements
        checks = [
            ("{{ t(", "Translation function calls"),
            ("base_template", "base_template category"),
            ("dashboard", "Dashboard translation"),
            ("simulation", "Simulation translation"),
        ]
        
        print("\n🔍 Verification:")
        for check_str, description in checks:
            count = content.count(check_str)
            status = "✅" if count > 0 else "❌"
            print(f"{status} {description}: {count} occurrences")
        
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function to run the script."""
    print("=" * 60)
    print("🔄 Updating base.html with Translation Calls")
    print("=" * 60)
    
    # First, add the translations if needed
    print("\n📝 Step 1: Checking/adding translations...")
    os.system("python add_base_translations.py")
    
    print("\n" + "=" * 60)
    print("🔄 Step 2: Updating base.html...")
    print("=" * 60)
    
    success = update_base_html()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Step 3: Verifying changes...")
        print("=" * 60)
        verify_changes()
        
        print("\n" + "=" * 60)
        print("🎉 Successfully updated base.html!")
        print("\nNext steps:")
        print("1. Start your Flask app: python app.py")
        print("2. Open: http://localhost:5000")
        print("3. Test language switching (English/Norsk)")
        print("4. Check that all text appears correctly")
        print("=" * 60)
    else:
        print("\n❌ Failed to update base.html")

if __name__ == "__main__":
    main()