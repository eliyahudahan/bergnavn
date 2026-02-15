# translation_setup.py
"""
Simple setup script for BergNavn translation system.
"""

import os
import subprocess
import sys

def run_command(cmd, desc):
    print(f"\n{desc}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Success")
            if result.stdout.strip():
                # Show first 3 lines of output
                lines = result.stdout.strip().split('\n')[:3]
                for line in lines:
                    print(f"  {line}")
        else:
            print("❌ Failed")
            if result.stderr.strip():
                print(f"Error: {result.stderr[:200]}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    print("=" * 60)
    print("BergNavn Translation System Setup")
    print("=" * 60)
    
    # Step 1: Initialize
    print("\n📝 Step 1: Initializing translation system...")
    run_command("python -m backend.translations init", "Initialize translations")
    
    # Step 2: Backup
    print("\n💾 Step 2: Creating backup...")
    run_command("python -m backend.translations backup", "Create backup")
    
    # Step 3: Preview
    print("\n👀 Step 3: Previewing changes...")
    run_command("python -m backend.translations transform --dry-run", "Preview changes")
    
    # Step 4: Ask about transformation
    print("\n🔄 Step 4: Apply transformations")
    print("Options:")
    print("  1. Transform only base.html")
    print("  2. Transform all templates")
    print("  3. Skip transformation")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        run_command("python -m backend.translations transform --template base.html", "Transform base.html")
    elif choice == "2":
        run_command("python -m backend.translations transform", "Transform all templates")
    else:
        print("Skipping transformation.")
    
    # Step 5: Show stats
    print("\n📊 Step 5: Showing statistics...")
    run_command("python -m backend.translations stats", "Show statistics")
    
    print("\n" + "=" * 60)
    print("Setup complete! 🎉")
    print("\nNext steps:")
    print("  1. Run: python app.py")
    print("  2. Open: http://localhost:5000")
    print("  3. Test language switching")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\nError during setup: {e}")