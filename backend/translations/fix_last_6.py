#!/usr/bin/env python3
"""
FIX LAST 6 TRANSLATE TAGS - BergNavn Maritime
Fixes the remaining 6 [TRANSLATE: ...] tags with proper Norwegian translations.
"""

import json
import re
import shutil
import datetime

print("🎯 FIXING LAST 6 TRANSLATE TAGS")
print("=" * 60)

# Make one more backup
backup_file = f"backend/translations/data/no.json.backup.FINAL.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2('backend/translations/data/no.json', backup_file)
print(f"📦 Backup created: {backup_file}")

# Load the file
with open('backend/translations/data/no.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# EXACT translations for the 6 remaining tags
EXACT_TRANSLATIONS = {
    # 1. Comprehensive information about Norwegian ports...
    "Comprehensive information about Norwegian ports including \n                    facilities, services, location data, and operational details.": 
        "Omfattende informasjon om norske havner inkludert fasiliteter, tjenester, lokasjonsdata og operasjonelle detaljer.",
    
    # 2. Monitor vessels in real-time...
    "Monitor vessels in real-time with detailed information including \n                    position, speed, course, destination, and vessel type.":
        "Overvåk skip i sanntid med detaljert informasjon inkludert posisjon, fart, kurs, destinasjon og skipstype.",
    
    # 3. Real-time maritime dashboard...
    "Real-time maritime dashboard with integrated AIS vessel tracking, \n                    MET Norway weather data, and interactive maps of Norwegian waters.":
        "Sanntids maritim dashbord med integrert AIS skipssporing, MET Norge værdata og interaktive kart over norske farvann.",
    
    # 4. The maritime dashboard encountered an issue...
    "The maritime dashboard encountered an issue while processing your request. \n                            This could be due to temporary service unavailability, data processing errors, \n                            or configuration issues.":
        "Det maritime dashbordet opplevde et problem under behandling av forespørselen din. Dette kan skyldes midlertidig tjenesteutilgjengelighet, databehandlingsfeil eller konfigurasjonsproblemer.",
    
    # 5. This platform was developed...
    "This platform was developed using modern development tools and methodologies, \n              including AI-assisted programming for rapid prototyping and optimization, \n              while maintaining full technical oversight and professional software engineering standards.\n              The implementation focuses on real-world maritime operational requirements.":
        "Denne plattformen ble utviklet ved bruk av moderne utviklingsverktøy og metodologier, inkludert AI-assistert programmering for rask prototypering og optimalisering, samtidig som full teknisk kontroll og profesjonelle programvareutviklingsstandarder ble opprettholdt. Implementeringen fokuserer på virkelige maritime operasjonelle krav.",
    
    # 6. | Updates:
    "| \n                            Updates:":
        "| Oppdateringer:"
}

# Fix the remaining 6
print("\n🔧 Fixing the 6 remaining translations:")

if 'global' in data and isinstance(data['global'], dict):
    fixed_count = 0
    
    for key in list(data['global'].keys()):
        value = data['global'][key]
        
        if isinstance(value, str) and '[TRANSLATE:' in value:
            # Extract English text
            match = re.search(r'\[TRANSLATE:\s*(.*?)\]', value, re.DOTALL)
            if match:
                english_text = match.group(1).strip()
                
                # Clean up newlines and extra spaces
                english_text = re.sub(r'\s+', ' ', english_text).strip()
                
                # Try to find exact translation
                if english_text in EXACT_TRANSLATIONS:
                    data['global'][key] = EXACT_TRANSLATIONS[english_text]
                    fixed_count += 1
                    print(f"   ✓ Fixed: {key}")
                else:
                    # Try partial match
                    for eng, nor in EXACT_TRANSLATIONS.items():
                        # Clean the key for comparison
                        clean_eng = re.sub(r'\s+', ' ', eng).strip()
                        if clean_eng in english_text:
                            data['global'][key] = nor
                            fixed_count += 1
                            print(f"   ✓ Fixed (partial): {key}")
                            break
    
    print(f"\n✅ Fixed {fixed_count} remaining translations")

# Save the file
with open('backend/translations/data/no.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n💾 Saved updated no.json")

# Final verification
print("\n🔍 FINAL VERIFICATION:")
with open('backend/translations/data/no.json', 'r', encoding='utf-8') as f:
    content = f.read()
    remaining = content.count('[TRANSLATE:')
    
    if remaining == 0:
        print("🎉🎉🎉 PERFECT! ALL TRANSLATE TAGS HAVE BEEN FIXED! 🎉🎉🎉")
        print("\n" + "=" * 60)
        print("🚀 YOUR WEBSITE IS NOW FULLY BILINGUAL!")
        print("=" * 60)
        print("\nTo launch and test:")
        print("   1. Start the server: python app.py")
        print("   2. Open in browser:")
        print("      • English: http://localhost:5000?lang=en")
        print("      • Norwegian: http://localhost:5000?lang=no")
        print("   3. Or click the language switcher in the navbar")
        print("\n📊 Statistics:")
        print("   • 119 TRANSLATE tags → 0 TRANSLATE tags")
        print("   • Completion: 100% ✓")
    else:
        print(f"⚠️  Still {remaining} TRANSLATE tags remaining.")
        print("   Showing remaining tags:")
        # Find remaining
        for line in content.split('\n'):
            if '[TRANSLATE:' in line:
                print(f"   • {line.strip()[:80]}...")