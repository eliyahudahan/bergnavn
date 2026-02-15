#!/usr/bin/env python3
"""
AUTO TRANSLATE ALL - BergNavn Maritime
This script automatically translates all TODOs in no.json to Norwegian
using Google Translate (free) or manual translations.
"""

import json
import re
import os
import time
from typing import Dict, List, Tuple
import html

# ============================================================================
# CONFIGURATION - Choose your translation method
# ============================================================================

# METHOD 1: Use Google Translate (free but requires internet)
USE_GOOGLE_TRANSLATE = True  # Set to False for manual translations only

# METHOD 2: Manual translations dictionary (extend this for common terms)
MANUAL_TRANSLATIONS = {
    # Basic UI
    "Home": "Hjem",
    "Back to Home": "Tilbake til hjem",
    "Welcome to BergNavn": "Velkommen til BergNavn",
    "Legal": "Juridisk",
    "Routes": "Ruter",
    "N/A": "Ikke tilgjengelig",
    
    # Maritime terms
    "Maritime": "Maritim",
    "Maritime Dashboard": "Maritim dashbord",
    "Vessel Tracking": "Skipssporing",
    "Ports": "Havner",
    "Vessels": "Skip",
    "Cargo Volume": "Lastvolum",
    "Route ETA": "Rute ETA",
    "Fuel Optimization": "Drivstoffoptimalisering",
    "Real-time": "Sanntid",
    "Real-time maritime tracking platform": "Sanntid maritime sporing plattform",
    
    # Platform features
    "Dashboard": "Dashbord",
    "Tracking": "Sporing",
    "Analytics": "Analyser",
    "Forecasts": "Prognoser",
    "Optimization": "Optimalisering",
    "Platform": "Plattform",
    "System": "System",
    "Infrastructure": "Infrastruktur",
    
    # Error messages
    "System Error": "Systemfeil",
    "Error Type": "Feiltype",
    "Error Code": "Feilkode",
    "Error Details": "Feildetaljer",
    "Contact Support": "Kontakt kundestøtte",
    
    # Common phrases
    "Your real-time maritime platform": "Din sanntids maritime plattform",
    "Track, analyze and optimize": "Spor, analyser og optimaliser",
    "Monitor and optimize maritime traffic": "Overvåk og optimaliser maritime trafikk",
    "Based on real-time data": "Basert på sanntidsdata",
    "Robust and secure infrastructure": "Robust og sikker infrastruktur",
    
    # Copyright
    "© 2025 BergNavn Maritime": "© 2025 BergNavn Maritime",
    "All rights reserved": "Alle rettigheter forbeholdt",
    "Privacy Policy": "Personvernerklæring",
    "Terms of Service": "Tjenestevilkår",
}

# ============================================================================
# GOOGLE TRANSLATE FUNCTIONS (Free API)
# ============================================================================

def translate_with_google(text: str, source_lang: str = "en", target_lang: str = "no") -> str:
    """
    Translate text using Google Translate (free web version).
    Requires internet connection.
    """
    try:
        # Method 1: Use googletrans library (if installed)
        try:
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(text, src=source_lang, dest=target_lang)
            return result.text
            
        except ImportError:
            # Method 2: Use requests to call Google Translate web version
            import requests
            import urllib.parse
            
            # Simple web scraping approach
            url = f"https://translate.google.com/m?sl={source_lang}&tl={target_lang}&q={urllib.parse.quote(text)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Extract translation from HTML
                match = re.search(r'class="result-container">(.*?)</div>', response.text, re.DOTALL)
                if match:
                    translated = html.unescape(match.group(1).strip())
                    return translated
                    
        # Method 3: Fallback to manual translations
        for eng, nor in MANUAL_TRANSLATIONS.items():
            if eng.lower() in text.lower():
                return nor
                
        return f"[TRANSLATION NEEDED: {text}]"
        
    except Exception as e:
        print(f"   ⚠️  Google Translate failed: {str(e)[:50]}...")
        return f"[FAILED TO TRANSLATE: {text}]"

# ============================================================================
# CORE TRANSLATION FUNCTIONS
# ============================================================================

def extract_english_from_todo(todo_text: str) -> str:
    """Extract English text from [TODO: ...] pattern."""
    match = re.match(r'\[TODO:\s*(.*?)\]', todo_text)
    if match:
        return match.group(1).strip()
    return todo_text.replace('[TODO:', '').replace(']', '').strip()

def translate_text(text: str) -> str:
    """Translate English text to Norwegian."""
    # Check manual translations first
    text_lower = text.lower()
    for eng, nor in MANUAL_TRANSLATIONS.items():
        if eng.lower() == text_lower:
            return nor
    
    # Try partial matches
    for eng, nor in MANUAL_TRANSLATIONS.items():
        if eng in text:
            # Replace the matching part
            return text.replace(eng, nor)
    
    # Use Google Translate if enabled
    if USE_GOOGLE_TRANSLATE:
        print(f"   🌐 Translating: {text[:50]}...")
        try:
            translated = translate_with_google(text)
            # Avoid rate limiting
            time.sleep(0.5)
            return translated
        except Exception as e:
            print(f"   ❌ Translation error: {e}")
    
    # Fallback
    return f"[MUST TRANSLATE: {text}]"

def fix_all_todos_in_file():
    """Fix all TODOs in no.json file."""
    print("🔧 Loading no.json file...")
    
    with open('backend/translations/data/no.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    todo_count = 0
    fixed_count = 0
    skipped_count = 0
    
    print("📊 Analyzing translation file...")
    
    # First, count all TODOs
    for category in data:
        if isinstance(data[category], dict):
            for key in data[category]:
                value = data[category][key]
                if isinstance(value, str) and '[TODO:' in value:
                    todo_count += 1
    
    print(f"📋 Found {todo_count} TODOs to translate")
    
    if todo_count == 0:
        print("✅ No TODOs found! File is already translated.")
        return 0, 0
    
    # Ask for confirmation
    if todo_count > 50:
        response = input(f"\n⚠️  Found {todo_count} TODOs. Proceed with translation? (y/N): ")
        if response.lower() != 'y':
            print("Translation cancelled.")
            return todo_count, 0
    
    # Translate all TODOs
    print("\n🚀 Starting translation process...")
    
    for category in data:
        if isinstance(data[category], dict):
            print(f"\n📁 Category: {category}")
            
            for key in data[category]:
                value = data[category][key]
                
                if isinstance(value, str) and '[TODO:' in value:
                    # Extract English text
                    english_text = extract_english_from_todo(value)
                    
                    # Check if it's already in manual translations
                    translated = None
                    for eng, nor in MANUAL_TRANSLATIONS.items():
                        if eng == english_text:
                            translated = nor
                            break
                    
                    # If not, translate it
                    if not translated:
                        translated = translate_text(english_text)
                    
                    # Update the value
                    data[category][key] = translated
                    fixed_count += 1
                    
                    # Progress indicator
                    if fixed_count % 10 == 0:
                        print(f"   ✓ Translated {fixed_count}/{todo_count}")
    
    # Save the file
    print(f"\n💾 Saving translated file...")
    
    # Create backup
    backup_path = 'backend/translations/data/no.json.backup'
    if os.path.exists('backend/translations/data/no.json'):
        import shutil
        shutil.copy2('backend/translations/data/no.json', backup_path)
        print(f"   📦 Backup created: {backup_path}")
    
    # Save new file
    with open('backend/translations/data/no.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ TRANSLATION COMPLETE!")
    print(f"   Total TODOs found: {todo_count}")
    print(f"   Successfully translated: {fixed_count}")
    
    if todo_count > fixed_count:
        print(f"   ⚠️  Some translations may need manual review")
    
    return todo_count, fixed_count

def verify_translations():
    """Verify that all TODOs are gone."""
    print("\n🔍 Verifying translations...")
    
    with open('backend/translations/data/no.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    remaining_todos = 0
    failed_translations = 0
    
    for category in data:
        if isinstance(data[category], dict):
            for key in data[category]:
                value = data[category][key]
                if isinstance(value, str):
                    if '[TODO:' in value:
                        remaining_todos += 1
                    elif '[MUST TRANSLATE:' in value or '[FAILED TO TRANSLATE:' in value or '[TRANSLATION NEEDED:' in value:
                        failed_translations += 1
    
    if remaining_todos == 0 and failed_translations == 0:
        print("✅ VERIFICATION PASSED!")
        print("   All TODOs have been translated successfully!")
        return True
    else:
        print("⚠️  VERIFICATION ISSUES FOUND:")
        if remaining_todos > 0:
            print(f"   • {remaining_todos} TODOs still remain")
        if failed_translations > 0:
            print(f"   • {failed_translations} failed translations need manual fix")
        
        # Show examples of issues
        print("\n🔧 To fix remaining issues:")
        print("   1. Run this script again (sometimes Google Translate works on second try)")
        print("   2. Add missing translations to MANUAL_TRANSLATIONS dictionary")
        print("   3. Check internet connection if using Google Translate")
        
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function to run the auto-translation."""
    print("=" * 70)
    print("🌍 BERGNAVN MARITIME - AUTO TRANSLATE ALL TODOs")
    print("=" * 70)
    print("This script will automatically translate all [TODO: ...] in no.json")
    print("from English to Norwegian using Google Translate (free).")
    print()
    
    # Check if file exists
    if not os.path.exists('backend/translations/data/no.json'):
        print("❌ ERROR: no.json file not found!")
        print("   Expected: backend/translations/data/no.json")
        return
    
    # Show current status
    with open('backend/translations/data/no.json', 'r', encoding='utf-8') as f:
        content = f.read()
        todo_count = content.count('[TODO:')
    
    print(f"📊 Current status: {todo_count} TODOs found in no.json")
    print(f"🔄 Translation method: {'Google Translate' if USE_GOOGLE_TRANSLATE else 'Manual only'}")
    print()
    
    # Run translation
    total_todos, fixed_todos = fix_all_todos_in_file()
    
    # Verify
    if fixed_todos > 0:
        verification_passed = verify_translations()
        
        print("\n" + "=" * 70)
        print("🎉 TRANSLATION PROCESS COMPLETE!")
        print("=" * 70)
        
        if verification_passed:
            print("\n✅ SUCCESS! You can now run translate_all.py")
            print("\n📝 Next steps:")
            print("   1. Run: python backend/translations/translate_all.py")
            print("   2. Press 'y' when prompted")
            print("   3. Your templates will be updated with Norwegian translations")
            print("   4. Start your app and test language switching")
        else:
            print("\n⚠️  Some issues remain. Please check above for details.")
            print("\n🔧 Run this script again or add manual translations.")
    
    print("\n💡 Tip: If Google Translate fails, you can:")
    print("   • Add more terms to MANUAL_TRANSLATIONS dictionary")
    print("   • Install googletrans: pip install googletrans==4.0.0-rc1")
    print("   • Use manual translation for remaining terms")

# ============================================================================
# RUN SCRIPT
# ============================================================================

if __name__ == "__main__":
    main()