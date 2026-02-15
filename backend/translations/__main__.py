"""
Main script to run the complete translation system.
Run with: python -m backend.translations
"""
import sys
import argparse
from datetime import datetime
from .core import initialize_translations, get_registry
from .template_transformer import TemplateTransformer

def main():
    """Main entry point for translation system."""
    parser = argparse.ArgumentParser(description="BergNavn Maritime Translation System")
    parser.add_argument('command', choices=['init', 'discover', 'transform', 'backup', 'stats'],
                       help='Command to execute')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show changes without applying (for transform)')
    parser.add_argument('--template', type=str,
                       help='Specific template to transform')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        print("🚀 Initializing complete translation system...")
        registry = initialize_translations()
        
        print("\n📊 Statistics:")
        print(f"  Total texts discovered: {len(registry.translation_keys)}")
        print(f"  English translations: {len(registry.translations['en'])}")
        print(f"  Norwegian translations: {len(registry.translations['no'])}")
        
        # Generate update suggestions
        print("\n🔧 Template updates needed:")
        updates = registry.generate_template_updates()
        for template, changes in updates.items():
            print(f"\n  {template}:")
            for change in changes[:5]:  # Show first 5
                print(f"    • {change}")
            if len(changes) > 5:
                print(f"    • ... and {len(changes) - 5} more")
    
    elif args.command == 'discover':
        print("🔍 Discovering texts in templates...")
        registry = get_registry()
        texts = registry.discover_all_texts()
        
        print(f"\nFound {len(texts)} text strings:")
        for i, (text, filepath, line_num, is_html) in enumerate(texts[:20], 1):
            print(f"{i:3}. {text[:60]}... (in {filepath}:{line_num})")
        
        if len(texts) > 20:
            print(f"... and {len(texts) - 20} more")
    
    elif args.command == 'transform':
        print("🔄 Transforming templates to use translation system...")
        transformer = TemplateTransformer()
        
        if args.template:
            # Transform specific template
            template_path = f"backend/templates/{args.template}"
            if not template_path.endswith('.html'):
                template_path += '.html'
            
            print(f"Transforming: {template_path}")
            if args.dry_run:
                print("DRY RUN - no changes will be made")
            
            changes = transformer._transform_template(template_path, args.dry_run)
            
            if changes:
                print(f"\nChanges for {args.template}:")
                for change in changes:
                    print(f"  • {change}")
            else:
                print("No changes needed")
        
        else:
            # Transform all templates
            if args.dry_run:
                print("DRY RUN - showing what would be changed")
            
            transformer.create_backup()
            changes = transformer.transform_all_templates(dry_run=args.dry_run)
            
            total_changes = sum(len(c) for c in changes.values())
            print(f"\n📝 Total changes: {total_changes}")
            
            for template, template_changes in changes.items():
                print(f"\n{template}:")
                for change in template_changes[:3]:
                    print(f"  • {change}")
                if len(template_changes) > 3:
                    print(f"  • ... and {len(template_changes) - 3} more")
    
    elif args.command == 'backup':
        print("📦 Creating backup of all templates...")
        transformer = TemplateTransformer()
        backup_path = transformer.create_backup()
        print(f"✅ Backup created at: {backup_path}")
    
    elif args.command == 'stats':
        print("📊 Translation system statistics")
        print("=" * 50)
        
        registry = get_registry()
        
        print(f"\nTotal registered texts: {len(registry.translation_keys)}")
        print(f"English translations: {len(registry.translations['en'])}")
        print(f"Norwegian translations: {len(registry.translations['no'])}")
        
        # Count by context
        contexts = {}
        for key in registry.translation_keys:
            context = key.split('.')[0]
            contexts[context] = contexts.get(context, 0) + 1
        
        print("\nBy context:")
        for context, count in sorted(contexts.items()):
            print(f"  {context}: {count}")
        
        # Count TODOs in Norwegian
        todo_count = sum(1 for t in registry.translations['no'].values() 
                        if isinstance(t, str) and '[TODO:' in t)
        print(f"\n⚠️  Norwegian translations needing review: {todo_count}")
    
    print("\n✅ Done!")

if __name__ == '__main__':
    main()