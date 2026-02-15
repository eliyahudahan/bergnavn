#!/usr/bin/env python3
"""
Add base.html translations to the system.
This script adds the necessary translations for base.html template
that were not automatically discovered by the system.
"""
import json
import os
import sys

def add_base_translations():
    """Add base template translations to English and Norwegian JSON files."""
    
    # Read existing English translations
    en_file = "backend/translations/data/en.json"
    try:
        with open(en_file, "r", encoding="utf-8") as f:
            en_translations = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {en_file} not found")
        return False
    
    # Add base_template category if it doesn't exist
    if "base_template" not in en_translations:
        en_translations["base_template"] = {}
    
    # Base template translations for English
    base_en_translations = {
        # Navigation
        "dashboard": "Dashboard",
        "simulation": "Simulation", 
        "routes": "Routes",
        "home": "Home",
        "language": "Language",
        
        # Language selector
        "english": "English",
        "norsk": "Norsk",
        
        # Logo and branding
        "bergnavn": "BergNavn",
        "maritime_intelligence": "Maritime Intelligence",
        "bergnavn_maritime": "BergNavn Maritime",
        "intelligent_route_optimization": "Intelligent Route Optimization System",
        
        # Footer content
        "norwegian_ports": "Norwegian Ports: Ålesund, Andalsnes, Bergen, Drammen, Flekkefjord, Kristiansand, Oslo, Sandefjord, Stavanger, Trondheim",
        "system_status": "System Status",
        "all_systems_operational": "All Systems Operational",
        "data_updated": "Data updated",
        "api_status": "API Status",
        "active": "Active",
        "partial": "Partial",
        "offline": "Offline",
        "research_development": "Research & Development Platform",
        "copyright": "© 2025 BergNavn Maritime",
        "technology_stack": "Flask • PostgreSQL • BarentsWatch API • MET Norway",
        "data_sources": "Data sources: BarentsWatch AIS • MET Norway • Norwegian Coastal Admin",
        "service_degraded": "Service Degraded",
        "api_connection_failed": "API Connection Failed",
        
        # Footer links
        "about": "About",
        "contact": "Contact",
        "legal": "Legal",
    }
    
    # Add English translations
    added_count = 0
    for key, value in base_en_translations.items():
        if key not in en_translations["base_template"]:
            en_translations["base_template"][key] = value
            added_count += 1
    
    # Save English translations
    with open(en_file, "w", encoding="utf-8") as f:
        json.dump(en_translations, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Added {added_count} English translations to base_template")
    
    # Read existing Norwegian translations
    no_file = "backend/translations/data/no.json"
    try:
        with open(no_file, "r", encoding="utf-8") as f:
            no_translations = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {no_file} not found")
        # Create empty structure if file doesn't exist
        no_translations = {}
    
    # Add base_template category if it doesn't exist
    if "base_template" not in no_translations:
        no_translations["base_template"] = {}
    
    # Base template translations for Norwegian
    base_no_translations = {
        # Navigation
        "dashboard": "Dashbord",
        "simulation": "Simulering",
        "routes": "Ruter",
        "home": "Hjem",
        "language": "Språk",
        
        # Language selector
        "english": "Engelsk",
        "norsk": "Norsk",
        
        # Logo and branding
        "bergnavn": "BergNavn",
        "maritime_intelligence": "Maritim Intelligens",
        "bergnavn_maritime": "BergNavn Maritime",
        "intelligent_route_optimization": "Intelligent Ruteoptimaliseringssystem",
        
        # Footer content
        "norwegian_ports": "Norske havner: Ålesund, Andalsnes, Bergen, Drammen, Flekkefjord, Kristiansand, Oslo, Sandefjord, Stavanger, Trondheim",
        "system_status": "Systemstatus",
        "all_systems_operational": "Alle systemer operative",
        "data_updated": "Data oppdatert",
        "api_status": "API-status",
        "active": "Aktiv",
        "partial": "Delvis",
        "offline": "Frakoblet",
        "research_development": "Forskning og utviklingsplattform",
        "copyright": "© 2025 BergNavn Maritime",
        "technology_stack": "Flask • PostgreSQL • BarentsWatch API • MET Norge",
        "data_sources": "Datakilder: BarentsWatch AIS • MET Norge • Norsk kystadministrasjon",
        "service_degraded": "Tjenesten er forringet",
        "api_connection_failed": "API-tilkobling mislyktes",
        
        # Footer links
        "about": "Om",
        "contact": "Kontakt",
        "legal": "Juridisk",
    }
    
    # Add Norwegian translations
    added_no_count = 0
    for key, value in base_no_translations.items():
        if key not in no_translations["base_template"]:
            no_translations["base_template"][key] = value
            added_no_count += 1
    
    # Save Norwegian translations
    with open(no_file, "w", encoding="utf-8") as f:
        json.dump(no_translations, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Added {added_no_count} Norwegian translations to base_template")
    
    # Update metadata if it exists
    metadata_file = "backend/translations/data/metadata.json"
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Update statistics
            metadata["total_keys"] = sum(len(v) for v in en_translations.values())
            metadata["english_count"] = sum(len(v) for v in en_translations.values())
            metadata["norwegian_count"] = sum(len(v) for v in no_translations.values())
            
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print("✅ Updated metadata statistics")
        except Exception as e:
            print(f"⚠️  Could not update metadata: {e}")
    
    return True

def main():
    """Main function to run the script."""
    print("=" * 60)
    print("📝 Adding Base Template Translations")
    print("=" * 60)
    
    success = add_base_translations()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Successfully added base template translations!")
        print("\nNext steps:")
        print("1. Check the translations were added:")
        print("   grep -n 'dashboard\\|simulation' backend/translations/data/en.json")
        print("2. Update base.html with translation calls")
        print("3. Run the app to test translations")
        print("=" * 60)
    else:
        print("\n❌ Failed to add translations")

if __name__ == "__main__":
    main()