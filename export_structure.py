import os

def print_dirs_only(root, level=0, max_level=3):
    """Print directory structure, excluding cache folders and .pyc files"""
    if level > max_level:
        return
    
    indent = '  ' * level
    
    # Get all items and sort them
    items = sorted(os.listdir(root))
    
    for name in items:
        path = os.path.join(root, name)
        
        # Skip cache folders and .pyc files
        if name in ['__pycache__', '.git', '.venv', 'venv', 'node_modules']:
            continue
        
        if name.endswith('.pyc'):
            continue
        
        # Check if it's a directory
        if os.path.isdir(path):
            print(f"{indent}📁 {name}/")
            print_dirs_only(path, level + 1, max_level)
        else:
            # Optional: show important files
            if any(ext in name for ext in ['.py', '.js', '.html', '.css', '.json', '.env']):
                print(f"{indent}📄 {name}")

def export_to_file(root, output_file='project_structure.txt'):
    """Export structure to a text file"""
    original_stdout = sys.stdout
    
    with open(output_file, 'w', encoding='utf-8') as f:
        sys.stdout = f
        print("=" * 60)
        print("PROJECT STRUCTURE")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        print_dirs_only(root, max_level=4)
        print()
        print("=" * 60)
        print("END OF STRUCTURE")
        print("=" * 60)
    
    sys.stdout = original_stdout
    print(f"✅ Structure exported to: {output_file}")

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    print("🌊 BergNavn Project Structure Exporter")
    print("=" * 40)
    
    # Export to file
    export_to_file('.')
    
    # Also print to console
    print("\n📋 Structure preview:")
    print_dirs_only('.', max_level=2)