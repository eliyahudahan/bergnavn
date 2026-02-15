"""
Core translation system for BergNavn Maritime.
Automatically handles ALL text in templates.
"""
import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TranslationKey:
    """Represents a translatable text item."""
    key: str
    english_text: str
    norwegian_text: str = ""
    context: str = ""
    source_file: str = ""
    line_number: int = 0
    is_html: bool = False
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def to_dict(self):
        return {
            'key': self.key,
            'en': self.english_text,
            'no': self.norwegian_text or self.english_text,  # Fallback to English
            'context': self.context,
            'source': self.source_file,
            'line': self.line_number,
            'html': self.is_html,
            'updated': self.last_updated.isoformat()
        }

class TranslationRegistry:
    """
    Central registry for ALL translations in the application.
    Automatically discovers, registers, and manages translations.
    """
    
    def __init__(self, templates_dir: str = "backend/templates"):
        self.templates_dir = templates_dir
        self.translations: Dict[str, Dict[str, str]] = {
            'en': {},
            'no': {}
        }
        self.translation_keys: Dict[str, TranslationKey] = {}
        self.reverse_lookup: Dict[str, str] = {}  # English text -> key
        self.load_existing()
    
    def load_existing(self):
        """Load existing translations from your translations.py."""
        from backend.utils.translations import translations as existing
        
        # Convert existing translations to our format
        for lang in ['en', 'no']:
            for category, items in existing[lang].items():
                for key, text in items.items():
                    full_key = f"{category}.{key}"
                    self.translations[lang][full_key] = text
                    
                    # Create translation key if not exists
                    if full_key not in self.translation_keys:
                        self.translation_keys[full_key] = TranslationKey(
                            key=full_key,
                            english_text=text if lang == 'en' else "",
                            norwegian_text=text if lang == 'no' else "",
                            context=category,
                            source_file="translations.py"
                        )
                    
                    # Update reverse lookup
                    if lang == 'en':
                        self.reverse_lookup[text] = full_key
    
    def generate_key(self, text: str, context: str = "") -> str:
        """Generate a unique key for a text string."""
        # Create hash-based key for uniqueness
        text_hash = hashlib.md5(f"{context}:{text}".encode()).hexdigest()[:8]
        
        # Create readable key from text
        readable_part = text.lower()[:20]
        readable_part = re.sub(r'[^a-z0-9]', '_', readable_part)
        readable_part = readable_part.strip('_')
        
        return f"auto_{readable_part}_{text_hash}"
    
    def discover_all_texts(self) -> List[Tuple[str, str, int, bool]]:
        """
        Discover ALL hardcoded texts in ALL templates.
        Returns: [(text, file_path, line_number, is_html)]
        """
        all_texts = []
        
        for root, dirs, files in os.walk(self.templates_dir):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    texts = self._extract_texts_from_file(filepath)
                    all_texts.extend(texts)
        
        return all_texts
    
    def _extract_texts_from_file(self, filepath: str) -> List[Tuple[str, str, int, bool]]:
        """Extract all text content from a template file."""
        texts = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_script = False
        in_style = False
        
        for i, line in enumerate(lines, 1):
            # Skip script and style blocks
            if '<script' in line.lower():
                in_script = True
            if '</script' in line.lower():
                in_script = False
            if '<style' in line.lower():
                in_style = True
            if '</style' in line.lower():
                in_style = False
            
            if in_script or in_style:
                continue
            
            # Extract text from HTML
            # Remove template variables {{ ... }}
            clean_line = re.sub(r'{{.*?}}', '', line)
            clean_line = re.sub(r'{%.*?%}', '', clean_line)
            
            # Find text between > and < (but not inside tags)
            matches = re.finditer(r'>([^<>{}\n]+(?:\s+[^<>{}\n]+)*)<', clean_line)
            
            for match in matches:
                text = match.group(1).strip()
                if (text and 
                    len(text) > 1 and 
                    not text.isspace() and
                    not text.startswith('http') and
                    not text.startswith('//') and
                    not re.match(r'^[\d\s:.-]+$', text)):
                    
                    # Check if it's HTML with tags
                    is_html = '<' in text and '>' in text
                    
                    # Clean HTML tags if needed
                    if is_html:
                        # Extract only text from HTML
                        text_clean = re.sub(r'<[^>]+>', '', text).strip()
                        if text_clean:
                            texts.append((text_clean, filepath, i, False))
                    else:
                        texts.append((text, filepath, i, False))
        
        return texts
    
    def auto_register_all(self):
        """Automatically register ALL discovered texts."""
        discovered = self.discover_all_texts()
        
        for text, filepath, line_num, is_html in discovered:
            # Skip if already registered
            if text in self.reverse_lookup:
                continue
            
            # Generate key and register
            rel_path = os.path.relpath(filepath, self.templates_dir)
            context = os.path.dirname(rel_path) or "global"
            
            key = self.generate_key(text, context)
            full_key = f"{context}.{key}" if context != "global" else f"global.{key}"
            
            # Register translation
            self.translations['en'][full_key] = text
            self.translation_keys[full_key] = TranslationKey(
                key=full_key,
                english_text=text,
                context=context,
                source_file=rel_path,
                line_number=line_num,
                is_html=is_html
            )
            self.reverse_lookup[text] = full_key
            
            print(f"📝 Registered: {full_key} = '{text[:50]}...'")
    
    def auto_translate_to_norwegian(self):
        """
        Auto-translate English texts to Norwegian.
        In production, you'd use an API like Google Translate, DeepL, etc.
        For now, we'll use a simple dictionary and mark for manual review.
        """
        simple_dict = {
            # Add common maritime terms
            'Dashboard': 'Dashbord',
            'Simulation': 'Simulering',
            'Routes': 'Ruter',
            'Home': 'Hjem',
            'Language': 'Språk',
            'English': 'Engelsk',
            'Norsk': 'Norsk',
            'Maritime Intelligence': 'Maritim Intelligens',
            'System Status': 'Systemstatus',
            'Data updated': 'Data oppdatert',
            'API Status': 'API-status',
            'Active': 'Aktiv',
            'About': 'Om',
            'Contact': 'Kontakt',
            'Legal': 'Juridisk',
            'Norwegian Ports': 'Norske havner',
            'Intelligent Route Optimization System': 'Intelligent ruteoptimaliseringssystem',
            'Research & Development Platform': 'Forskning og utviklingsplattform',
            # Add more as needed
        }
        
        for key, trans_key in self.translation_keys.items():
            if not trans_key.norwegian_text:
                english = trans_key.english_text
                
                # Try simple dictionary first
                if english in simple_dict:
                    norwegian = simple_dict[english]
                else:
                    # Mark for manual translation
                    norwegian = f"[TODO: {english}]"
                
                trans_key.norwegian_text = norwegian
                self.translations['no'][key] = norwegian
    
    def export_to_json(self, output_dir: str = "backend/translations/data"):
        """Export all translations to JSON files."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export by language
        for lang in ['en', 'no']:
            output = {}
            for key, text in self.translations[lang].items():
                # Group by context
                context, _, subkey = key.partition('.')
                if context not in output:
                    output[context] = {}
                output[context][subkey] = text
            
            with open(os.path.join(output_dir, f"{lang}.json"), 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
        
        # Export metadata
        metadata = {
            'total_keys': len(self.translation_keys),
            'english_count': len(self.translations['en']),
            'norwegian_count': len(self.translations['no']),
            'generated_at': datetime.now().isoformat(),
            'keys': {k: v.to_dict() for k, v in self.translation_keys.items()}
        }
        
        with open(os.path.join(output_dir, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported {len(self.translation_keys)} translations to {output_dir}")
    
    def generate_template_updates(self) -> Dict[str, List[str]]:
        """
        Generate code to update templates with translation calls.
        Returns: {template_file: [update_commands]}
        """
        updates = {}
        
        for key, trans_key in self.translation_keys.items():
            if trans_key.source_file != "translations.py":
                template_file = os.path.join(self.templates_dir, trans_key.source_file)
                
                if template_file not in updates:
                    updates[template_file] = []
                
                update_cmd = self._create_update_command(
                    template_file,
                    trans_key.line_number,
                    trans_key.english_text,
                    key
                )
                
                if update_cmd:
                    updates[template_file].append(update_cmd)
        
        return updates
    
    def _create_update_command(self, filepath: str, line_num: int, old_text: str, new_key: str) -> Optional[str]:
        """Create a sed/string replacement command."""
        # Escape special characters for regex
        escaped_text = re.escape(old_text)
        
        # Create replacement
        context, _, subkey = new_key.partition('.')
        replacement = f"{{{{ t('{subkey}', '{context}') }}}}"
        
        return f"Line {line_num}: Replace '{old_text[:50]}...' with {replacement}"

# Global registry instance
_registry = None

def get_registry() -> TranslationRegistry:
    """Get or create the global translation registry."""
    global _registry
    if _registry is None:
        _registry = TranslationRegistry()
    return _registry

def initialize_translations():
    """Initialize the translation system - run this once."""
    registry = get_registry()
    print("🔍 Discovering all texts in templates...")
    registry.auto_register_all()
    print(f"📊 Registered {len(registry.translation_keys)} texts")
    
    print("🌍 Auto-translating to Norwegian...")
    registry.auto_translate_to_norwegian()
    
    print("💾 Exporting translations...")
    registry.export_to_json()
    
    return registry