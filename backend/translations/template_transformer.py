"""
Automatically transforms templates to use the translation system.
Replaces hardcoded text with dynamic translation calls.
"""
import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .core import get_registry

class TemplateTransformer:
    """
    Automatically replaces hardcoded text with translation calls.
    Handles HTML templates and preserves structure while enabling i18n.
    """
    
    def __init__(self, templates_dir: str = "backend/templates"):
        """
        Initialize the transformer.
        
        Args:
            templates_dir: Path to templates directory
        """
        self.templates_dir = templates_dir
        self.registry = get_registry()
        self.backup_dir = os.path.join(templates_dir, "backups")
    
    def create_backup(self) -> Optional[str]:
        """
        Create a backup of all templates before transformation.
        
        Returns:
            Path to backup directory or None if failed
        """
        try:
            # Create backup directory if it doesn't exist
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Generate timestamp for backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f"pre_translation_{timestamp}")
            
            # Check if templates directory exists
            if not os.path.exists(self.templates_dir):
                print(f"❌ Templates directory not found: {self.templates_dir}")
                return None
            
            # Create backup
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            
            # Copy all templates to backup
            shutil.copytree(self.templates_dir, backup_path, 
                          ignore=shutil.ignore_patterns('backups', '*.backup*'),
                          dirs_exist_ok=True)
            
            print(f"📦 Created backup at: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return None
    
    def transform_all_templates(self, dry_run: bool = True) -> Dict[str, List[str]]:
        """
        Transform ALL templates to use translation system.
        
        Args:
            dry_run: If True, only show changes without applying
            
        Returns:
            Dictionary mapping template files to list of changes made
        """
        changes = {}
        
        # Check if templates directory exists
        if not os.path.exists(self.templates_dir):
            print(f"❌ Templates directory not found: {self.templates_dir}")
            return changes
        
        # Walk through all template files
        for root, dirs, files in os.walk(self.templates_dir):
            # Skip backup directory
            if 'backups' in root:
                continue
            
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    file_changes = self._transform_template(filepath, dry_run)
                    if file_changes:
                        rel_path = os.path.relpath(filepath, self.templates_dir)
                        changes[rel_path] = file_changes
        
        return changes
    
    def _transform_template(self, filepath: str, dry_run: bool) -> List[str]:
        """
        Transform a single template file.
        
        Args:
            filepath: Path to template file
            dry_run: If True, only show changes without applying
            
        Returns:
            List of changes made
        """
        changes = []
        
        # Check if file exists
        if not os.path.exists(filepath):
            return changes
        
        # Get relative path for context
        rel_path = os.path.relpath(filepath, self.templates_dir)
        
        # Read template content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            print(f"❌ Failed to read {filepath}: {e}")
            return changes
        
        # Start with original content
        new_content = original_content
        
        # Find all translation keys relevant to this template
        template_keys = self._get_template_keys(rel_path)
        
        # Apply replacements for each key
        for full_key, trans_key in template_keys:
            change = self._apply_replacement(
                full_key, trans_key, new_content, rel_path
            )
            
            if change:
                new_content = change['new_content']
                changes.append(change['description'])
        
        # Only write if there are changes and not in dry run
        if changes and not dry_run:
            try:
                # Create backup of this specific file
                backup_file = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(filepath, backup_file)
                
                # Write transformed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
            except Exception as e:
                print(f"❌ Failed to write {filepath}: {e}")
                return []
        
        return changes
    
    def _get_template_keys(self, rel_path: str) -> List[Tuple[str, any]]:
        """
        Get translation keys relevant to a specific template.
        
        Args:
            rel_path: Relative path of template
            
        Returns:
            List of (full_key, translation_key) tuples
        """
        template_keys = []
        
        for full_key, trans_key in self.registry.translation_keys.items():
            # Check if this key comes from this template
            if trans_key.source_file == rel_path:
                template_keys.append((full_key, trans_key))
        
        return template_keys
    
    def _apply_replacement(self, full_key: str, trans_key: any, 
                          content: str, rel_path: str) -> Optional[Dict]:
        """
        Apply a single replacement in template content.
        
        Args:
            full_key: Full translation key (category.subkey)
            trans_key: TranslationKey object
            content: Current template content
            rel_path: Relative path of template
            
        Returns:
            Dictionary with new_content and description, or None
        """
        english_text = trans_key.english_text
        
        # Skip if text not in content
        if english_text not in content:
            return None
        
        # Split key into category and subkey
        if '.' in full_key:
            category, subkey = full_key.split('.', 1)
        else:
            category = 'global'
            subkey = full_key
        
        # Create replacement string
        replacement = f"{{{{ t('{subkey}', '{category}') }}}}"
        
        # Create regex pattern with word boundaries for exact match
        # Escape special regex characters in the text
        escaped_text = re.escape(english_text)
        
        # Use word boundaries but be careful with punctuation
        pattern = r'(?<![\\w\\-/>])({})(?![\\w\\-/<])'.format(escaped_text)
        
        # Try replacement
        new_content, count = re.subn(pattern, replacement, content)
        
        if count > 0:
            return {
                'new_content': new_content,
                'description': f"Replaced '{english_text[:50]}{'...' if len(english_text) > 50 else ''}' with {{ t('{subkey}', '{category}') }}"
            }
        
        return None
    
    def smart_transform_base_html(self, dry_run: bool = True) -> List[str]:
        """
        Smart transformation for base.html with special handling.
        
        Args:
            dry_run: If True, only show changes without applying
            
        Returns:
            List of changes made
        """
        base_path = os.path.join(self.templates_dir, "base.html")
        
        if not os.path.exists(base_path):
            print("❌ base.html not found!")
            return []
        
        print(f"🎯 Performing smart transformation on base.html")
        
        # Read the file
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Define smart patterns for common base.html elements
        smart_patterns = [
            # Navigation items: <span>Text</span> inside nav links
            (r'(<span[^>]*class="[^"]*fw-semibold[^"]*"[^>]*>)([^<{]+)(?<!})(</span>)',
             r'\1{{ t("\2", "navigation") }}\3'),
            
            # Buttons with text
            (r'(<button[^>]*>)([^<{]+)(?<!})(</button>)',
             r'\1{{ t("\2", "buttons") }}\3'),
            
            # Footer text in small tags
            (r'(<small[^>]*>)([^<{]+)(?<!})(</small>)',
             r'\1{{ t("\2", "footer") }}\3'),
            
            # Logo/subtitle text
            (r'(<small[^>]*class="[^"]*text-muted[^"]*"[^>]*>)([^<{]+)(?<!})(</small>)',
             r'\1{{ t("\2", "base_template") }}\3'),
        ]
        
        changes = []
        new_content = content
        
        for pattern, replacement in smart_patterns:
            try:
                # Count replacements
                matches_before = len(re.findall(pattern, new_content))
                new_content = re.sub(pattern, replacement, new_content)
                matches_after = len(re.findall(pattern, new_content))
                
                if matches_before != matches_after:
                    changes.append(f"Applied pattern: {pattern[:60]}...")
                    
            except Exception as e:
                print(f"⚠️  Error applying pattern: {e}")
        
        # Create a more detailed report
        if changes:
            if not dry_run:
                # Create backup
                backup_path = base_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(base_path, backup_path)
                
                # Write changes
                with open(base_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ Transformed base.html (backup: {backup_path})")
            else:
                print(f"📝 Would transform base.html ({len(changes)} changes)")
        
        return changes

# Helper function for direct use
def transform_template(template_path: str, dry_run: bool = True) -> List[str]:
    """
    Helper function to transform a single template.
    
    Args:
        template_path: Full path to template
        dry_run: If True, only show changes
        
    Returns:
        List of changes made
    """
    # Determine templates directory from template path
    templates_dir = os.path.dirname(template_path)
    while 'templates' not in os.path.basename(templates_dir) and templates_dir != '/':
        templates_dir = os.path.dirname(templates_dir)
    
    transformer = TemplateTransformer(templates_dir)
    return transformer._transform_template(template_path, dry_run)