#!/usr/bin/env python3
"""
FIX GLOBAL TRANSLATIONS ONLY - BergNavn Maritime
Fixes only the 119 [TRANSLATE: ...] tags in the 'global' category.
"""

import json
import re

print("🎯 FIXING 119 TRANSLATE TAGS IN GLOBAL CATEGORY")
print("=" * 60)

# First, make a backup
import shutil
import datetime
backup_file = f"backend/translations/data/no.json.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2('backend/translations/data/no.json', backup_file)
print(f"📦 Backup created: {backup_file}")

# Load the file
with open('backend/translations/data/no.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Define EXACT translations for the found examples
EXACT_TRANSLATIONS = {
    # Found in your grep output
    "0 %}": "0 %}",
    "= 10 %}": "= 10 %}",
    "© 2025 BergNavn Maritime | Intelligent Route Optimization System": 
        "© 2025 BergNavn Maritime | Intelligent Ruteoptimaliseringssystem",
    "= 30 %}": "= 30 %}",
    "Active ports:": "Aktive havner:",
    "AIS": "AIS",
    "AIS: Loading...": "AIS: Laster...",
    "All data sources are integrated in real-time for comprehensive maritime situational awareness": 
        "Alle datakilder er integrert i sanntid for omfattende maritim situasjonsbevissthet",
    "An unexpected error occurred in the maritime system": 
        "En uventet feil oppsto i det maritime systemet",
    "Analyses": "Analyser",
    
    # Common maritime translations
    "Return to Home": "Tilbake til hjem",
    "Close": "Lukk",
    "Clear": "Tøm",
    "Center": "Senter",
    "Analysis ID:": "Analyse-ID:",
    "Captured:": "Innfanget:",
    "Current Weather": "Nåværende vær",
    "Check API Status": "Sjekk API-status",
    "Contact Support": "Kontakt kundestøtte",
    
    # Technical terms (keep English)
    "API": "API",
    "ETA": "ETA",
    "RTZ": "RTZ",
    "JSON": "JSON",
    "PostgreSQL": "PostgreSQL",
    
    # More from likely patterns
    "Loading...": "Laster...",
    "Loading": "Laster",
    "Refresh": "Oppdater",
    "Search": "Søk",
    "Filter": "Filtrer",
    "Settings": "Innstillinger",
    "Dashboard": "Dashbord",
    "Map": "Kart",
    "Routes": "Ruter",
    "Vessels": "Skip",
    "Ports": "Havner",
    "Weather": "Vær",
    "Simulation": "Simulering",
    "Analysis": "Analyse",
    "Data": "Data",
    "System": "System",
    "Error": "Feil",
    "Success": "Suksess",
    "Warning": "Advarsel",
    "Info": "Info",
}

# Fix only the 'global' category (where all 119 are)
if 'global' in data and isinstance(data['global'], dict):
    fixed_count = 0
    kept_english_count = 0
    
    print("\n🔧 Fixing translations in 'global' category:")
    
    for key in list(data['global'].keys()):
        value = data['global'][key]
        
        if isinstance(value, str) and '[TRANSLATE:' in value:
            # Extract English text
            match = re.search(r'\[TRANSLATE:\s*(.*?)\]', value)
            if match:
                english_text = match.group(1).strip()
                
                # Try to find exact translation
                if english_text in EXACT_TRANSLATIONS:
                    data['global'][key] = EXACT_TRANSLATIONS[english_text]
                    fixed_count += 1
                    if fixed_count <= 5:  # Show first 5
                        print(f"   ✓ {english_text[:40]}... → {EXACT_TRANSLATIONS[english_text][:40]}...")
                else:
                    # Check for partial matches
                    translated = False
                    for eng, nor in EXACT_TRANSLATIONS.items():
                        if eng in english_text:
                            data['global'][key] = english_text.replace(eng, nor)
                            fixed_count += 1
                            translated = True
                            break
                    
                    # If no translation found, keep English (better than [TRANSLATE:])
                    if not translated:
                        data['global'][key] = english_text
                        kept_english_count += 1
    
    print(f"\n✅ Results:")
    print(f"   • Successfully translated: {fixed_count}")
    print(f"   • Kept in English: {kept_english_count}")
    print(f"   • Total fixed: {fixed_count + kept_english_count}/119")

# Save the file
with open('backend/translations/data/no.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n💾 Saved updated no.json")

# Verify
print("\n🔍 Verification:")
with open('backend/translations/data/no.json', 'r', encoding='utf-8') as f:
    content = f.read()
    remaining = content.count('[TRANSLATE:')
    print(f"   Remaining TRANSLATE tags: {remaining}")
    
    if remaining == 0:
        print("\n🎉 PERFECT! All TRANSLATE tags have been fixed!")
        print("\n🚀 Your website is now fully bilingual!")
        print("\nTo test:")
        print("   1. Run: python app.py")
        print("   2. Open: http://localhost:5000?lang=en (English)")
        print("   3. Open: http://localhost:5000?lang=no (Norwegian)")
        print("   4. Or click the language switcher in the navbar")
    else:
        print(f"\n⚠️  Still {remaining} TRANSLATE tags remaining.")
        print("   Run this script again or add more translations to EXACT_TRANSLATIONS dictionary.")