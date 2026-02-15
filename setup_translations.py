"""
Complete setup script for BergNavn translation system.
Run this to initialize, configure, and test everything.
"""
import sys
import os
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"🚀 {text}")
    print("=" * 60)

def run_command(command, description):
    """Run a shell command with error handling."""
    print(f"\n🔧 {description}")
    print(f"   $ {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout and result.stdout.strip():
                print(f"   📝 Output: {result.stdout[:100]}...")
        else:
            print(f"   ❌ Failed (code: {result.returncode})")
            if result.stderr and result.stderr.strip():
                print(f"   💥 Error: {result.stderr[:100]}")
            return False
        
        return True
    except Exception as e:
        print(f"   💥 Exception: {e}")
        return False

def check_prerequisites():
    """Check if all prerequisites are met."""
    print_header("Checking Prerequisites")
    
    checks = [
        ("Project directory", os.path.exists("backend")),
        ("Templates directory", os.path.exists("backend/templates")),
        ("Translations module", os.path.exists("backend/translations")),
        ("Python 3.x", sys.version_info.major == 3),
    ]
    
    all_ok = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_ok = False
    
    return all_ok

def initialize_translation_system():
    """Initialize the translation system."""
    print_header("Initializing Translation System")
    
    # Create directories
    directories = [
        "backend/translations/data",
        "backend/templates/backups",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Initialize translations
    print("\n📝 Initializing translations...")
    return run_command(
        "python -m backend.translations init",
        "Initializing translation system"
    )

def analyze_templates():
    """Analyze templates for translation needs."""
    print_header("Analyzing Templates")
    
    commands = [
        ("python -m backend.translations backup", "Creating backup"),
        ("python -m backend.translations discover", "Discovering texts"),
        ("python -m backend.translations stats", "Showing statistics"),
    ]
    
    for cmd, desc in commands:
        run_command(cmd, desc)
    
    return True

def preview_changes():
    """Preview what changes will be made."""
    print_header("Previewing Changes")
    
    return run_command(
        "python -m backend.translations transform --dry-run",
        "Previewing template changes"
    )

def apply_transformations():
    """Apply the transformations to templates."""
    print_header("Applying Transformations")
    
    print("\nSelect transformation option:")
    print("1. Transform only base.html (recommended)")
    print("2. Transform all templates")
    print("3. Skip transformations")
    
    choice = input("\nYour choice (1-3): ").strip()
    
    if choice == "3":
        print("Skipping transformations.")
        return True
    
    if choice == "1":
        print("\n🔄 Transforming base.html...")
        return run_command(
            "python -m backend.translations transform --template base.html",
            "Transforming base.html"
        )
    
    if choice == "2":
        print("\n🔄 Transforming all templates...")
        return run_command(
            "python -m backend.translations transform",
            "Transforming all templates"
        )
    
    print("Invalid choice, skipping.")
    return True

def test_system():
    """Test the translation system."""
    print_header("Testing Translation System")
    
    # Create a simple test if needed
    test_file = "test_simple.py"
    if not os.path.exists(test_file):
        test_code = '''import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from backend.translations.flask_integration import get_translator
    translator = get_translator()
    print("✅ Translation system loaded")
    
    # Test translation
    result = translator.translate('home', 'en', 'Home')
    print(f"✅ Test translation: {result}")
    
    # Check Norwegian
    result_no = translator.translate('home', 'no', 'Hjem')
    print(f"✅ Norwegian test: {result_no}")
    
    print("\\n🎉 System is working!")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
'''
        
        with open(test_file, "w") as f:
            f.write(test_code)
    
    return run_command(
        f"python {test_file}",
        "Running system test"
    )

def create_guide():
    """Create quick start guide."""
    print_header("Creating Documentation")
    
    guide = """# Translation System Guide

## Setup Complete!

### Next Steps:
1. Start Flask app: python app.py
2. Open: http://localhost:5000
3. Test language switching

### Manual Commands:
- python -m backend.translations init
- python -m backend.translations transform --dry-run
- python -m backend.translations stats

### API Endpoints:
- GET /api/translations/health
- GET /api/translations/en
- GET /api/translations/no
"""
    
    with open("TRANSLATION_GUIDE.md", "w") as f:
        f.write(guide)
    
    print("📘 Guide created: TRANSLATION_GUIDE.md")
    return True

def main():
    """Main setup function."""
    print("=" * 60)
    print("🌍 BERGNAVN TRANSLATION SYSTEM SETUP")
    print("=" * 60)
    
    print("\nThis will:")
    print("1. Check prerequisites")
    print("2. Initialize system")
    print("3. Analyze templates")
    print("4. Preview changes")
    print("5. Apply transformations")
    print("6. Test system")
    print("7. Create guide")
    
    response = input("\nContinue? (Y/n): ").strip()
    if response.lower() == 'n':
        print("Setup cancelled.")
        return
    
    steps = [
        ("Checking prerequisites", check_prerequisites),
        ("Initializing system", initialize_translation_system),
        ("Analyzing templates", analyze_templates),
        ("Previewing changes", preview_changes),
        ("Applying transformations", apply_transformations),
        ("Testing system", test_system),
        ("Creating guide", create_guide),
    ]
    
    for step_name, step_func in steps:
        print_header(step_name)
        if not step_func():
            print(f"\n⚠️  {step_name} had issues")
            cont = input("Continue anyway? (Y/n): ").strip()
            if cont.lower() == 'n':
                print("Setup stopped.")
                return
    
    print_header("🎉 SETUP COMPLETE!")
    print("\n✅ Translation system is ready!")
    print("\nNext: python app.py")
    print("Test: http://localhost:5000")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
