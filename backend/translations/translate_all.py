#!/usr/bin/env python3
"""
Translate ALL templates in BergNavn Maritime.
This script will process all HTML templates and add translation support.
"""
import os
import re
import json
import shutil
from datetime import datetime
from pathlib import Path
import sys

def get_all_templates():
    """Get all HTML template files that need translation."""
    template_dir = "backend/templates"
    templates = []
    
    # List of templates to process (exclude base.html which is already done)
    template_files = [
        "backend/templates/error.html",
        "backend/templates/home.html",
        "backend/templates/legal.html",
        "backend/templates/routes.html",
        "backend/templates/maritime/home.html",
        "backend/templates/maritime/ports.html",
        "backend/templates/maritime/vessels.html",
        "backend/templates/maritime_split/alerts_block.html",
        "backend/templates/maritime_split/dashboard_base.html",
        "backend/templates/maritime_split/realtime_simulation.html",
        "backend/templates/maritime_split/simulation_integration.html"
    ]
    
    # Verify files exist
    for template in template_files:
        if os.path.exists(template):
            templates.append(template)
        else:
            print(f"⚠️  Template not found: {template}")
    
    return templates

def load_translations():
    """Load existing translations."""
    translations_dir = "backend/translations/data"
    translations = {'en': {}, 'no': {}}
    
    for lang in ['en', 'no']:
        file_path = os.path.join(translations_dir, f"{lang}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    translations[lang] = json.load(f)
                print(f"✅ Loaded {lang} translations: {sum(len(cat) for cat in translations[lang].values())} keys")
            except Exception as e:
                print(f"❌ Error loading {lang}.json: {e}")
        else:
            print(f"⚠️  {file_path} not found")
    
    return translations

def backup_template(filepath):
    """Create a backup of the template."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    return backup_path

def extract_text_from_template(filepath):
    """Extract all translatable text from a template."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip JavaScript and CSS
    content_clean = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<style.*?</style>', '', content_clean, flags=re.DOTALL)
    content_clean = re.sub(r'<!--.*?-->', '', content_clean, flags=re.DOTALL)
    
    # Find text that should be translated
    text_matches = []
    
    # Pattern 1: Text between > and < (but not template variables)
    pattern1 = r'>\s*([^<{>\n][^{}<]*?[^<{>\n])\s*<'
    matches1 = re.findall(pattern1, content_clean)
    
    # Pattern 2: Text in title, alt, placeholder attributes
    pattern2 = r'(title|alt|placeholder|aria-label)="([^"{]+)"'
    matches2 = re.findall(pattern2, content_clean)
    
    # Pattern 3: Text in meta tags
    pattern3 = r'<meta[^>]*(name|property)="[^"]+"[^>]*content="([^"{]+)"'
    matches3 = re.findall(pattern3, content_clean)
    
    # Combine all matches
    all_matches = []
    
    for match in matches1:
        text = match.strip()
        if (len(text) > 2 and 
            not text.startswith('http') and
            not text.startswith('//') and
            not re.match(r'^[\d\s.,:;-]+$', text) and
            '{{' not in text and '}}' not in text):
            all_matches.append(('text', text))
    
    for attr, text in matches2:
        text = text.strip()
        if len(text) > 2:
            all_matches.append((f'attr_{attr}', text))
    
    for attr, text in matches3:
        text = text.strip()
        if len(text) > 2:
            all_matches.append((f'meta_{attr}', text))
    
    # Remove duplicates
    unique_texts = []
    seen = set()
    
    for text_type, text in all_matches:
        if text not in seen:
            seen.add(text)
            unique_texts.append((text_type, text))
    
    return unique_texts

def generate_translation_key(text, category="global"):
    """Generate a translation key from text."""
    # Clean text for key generation
    clean_text = text.lower()
    clean_text = re.sub(r'[^\w\s-]', '', clean_text)  # Remove special chars
    clean_text = re.sub(r'\s+', '_', clean_text)      # Spaces to underscores
    clean_text = clean_text.strip('_')
    
    # Limit length
    if len(clean_text) > 40:
        words = clean_text.split('_')
        if len(words) > 4:
            clean_text = '_'.join(words[:4])
    
    # Add hash for uniqueness
    import hashlib
    text_hash = hashlib.md5(text.encode()).hexdigest()[:6]
    
    return f"auto_{clean_text}_{text_hash}"

def add_translations_for_text(text, translations):
    """Add translations for a text if not already present."""
    # Check if text already exists in translations
    for lang in ['en', 'no']:
        for category, items in translations[lang].items():
            if text in items.values():
                return None  # Already exists
    
    # Generate key
    key = generate_translation_key(text)
    
    # Add to English
    if 'global' not in translations['en']:
        translations['en']['global'] = {}
    translations['en']['global'][key] = text
    
    # Add to Norwegian (mark for translation)
    if 'global' not in translations['no']:
        translations['no']['global'] = {}
    translations['no']['global'][key] = f"[TRANSLATE: {text}]"
    
    return key

def update_template_with_translations(filepath, translations):
    """Update a template file with translation calls."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # First, extract all texts
    text_items = extract_text_from_template(filepath)
    
    if not text_items:
        print(f"   No translatable text found in {os.path.basename(filepath)}")
        return 0
    
    # Create replacements dictionary
    replacements = {}
    for text_type, text in text_items:
        key = add_translations_for_text(text, translations)
        if key:
            replacements[text] = key
    
    # Apply replacements
    new_content = content
    replacements_made = 0
    
    for original_text, key in replacements.items():
        # Different replacement based on context
        if f'"{original_text}"' in new_content:
            # Attribute value
            new_content = new_content.replace(f'"{original_text}"', f'"{{{{ t("{key}", "global") }}}}"')
            replacements_made += 1
        elif f">{original_text}<" in new_content:
            # Text content
            new_content = new_content.replace(f">{original_text}<", f'>{{{{ t("{key}", "global") }}}}<')
            replacements_made += 1
        elif f"={original_text}" in new_content:
            # Attribute without quotes
            new_content = new_content.replace(f"={original_text}", f'="{{{{ t("{key}", "global") }}}}"')
            replacements_made += 1
    
    # Write back if changes were made
    if replacements_made > 0:
        backup_path = backup_template(filepath)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"   ✓ Updated: {replacements_made} translations added")
        print(f"   📦 Backup: {backup_path}")
        return replacements_made
    
    return 0

def save_translations(translations):
    """Save updated translations to JSON files."""
    translations_dir = "backend/translations/data"
    os.makedirs(translations_dir, exist_ok=True)
    
    for lang in ['en', 'no']:
        file_path = os.path.join(translations_dir, f"{lang}.json")
        
        # Sort for readability
        sorted_translations = {}
        for category in sorted(translations[lang].keys()):
            sorted_items = dict(sorted(translations[lang][category].items()))
            sorted_translations[category] = sorted_items
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_translations, f, ensure_ascii=False, indent=2)
        
        key_count = sum(len(items) for items in sorted_translations.values())
        print(f"💾 Saved {lang}.json: {key_count} keys")

def main():
    """Main function to translate all templates."""
    print("=" * 60)
    print("🌍 BERGNAVN MARITIME - TRANSLATE ALL TEMPLATES")
    print("=" * 60)
    
    # Load existing translations
    translations = load_translations()
    
    # Get all templates
    templates = get_all_templates()
    print(f"\n📋 Found {len(templates)} templates to process:")
    for template in templates:
        print(f"   • {os.path.basename(template)}")
    
    # Ask for confirmation
    response = input("\n⚠️  Proceed with translation? This will modify templates. (y/N): ")
    if response.lower() != 'y':
        print("Translation cancelled.")
        return
    
    total_replacements = 0
    processed_templates = []
    
    # Process each template
    for template in templates:
        print(f"\n🔧 Processing: {os.path.basename(template)}")
        
        try:
            replacements = update_template_with_translations(template, translations)
            total_replacements += replacements
            if replacements > 0:
                processed_templates.append(os.path.basename(template))
        except Exception as e:
            print(f"   ❌ Error processing {template}: {e}")
    
    # Save updated translations
    if total_replacements > 0:
        print(f"\n💾 Saving updated translations...")
        save_translations(translations)
        
        print(f"\n✅ TRANSLATION COMPLETE!")
        print(f"   Total replacements: {total_replacements}")
        print(f"   Templates updated: {len(processed_templates)}")
        print(f"   New translation keys added")
        
        print(f"\n📋 Updated templates:")
        for template in processed_templates:
            print(f"   ✓ {template}")
        
        print(f"\n🔧 Next steps:")
        print(f"   1. Review Norwegian translations in backend/translations/data/no.json")
        print(f"   2. Replace '[TRANSLATE: ...]' with actual Norwegian text")
        print(f"   3. Test all pages with language switching")
        print(f"   4. Run 'python app.py' to verify everything works")
    else:
        print(f"\nℹ️  No changes made. Templates may already be translated.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()