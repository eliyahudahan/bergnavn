import os

def print_dirs_only(root, level=0, max_level=3):
    if level > max_level:
        return
    indent = '  ' * level
    for name in sorted(os.listdir(root)):
        if name in ['__pycache__', '.git'] or name.endswith('.pyc') or os.path.isfile(os.path.join(root, name)):
            continue
        path = os.path.join(root, name)
        print(f"{indent}{name}")
        print_dirs_only(path, level + 1, max_level)

if __name__ == "__main__":
    print_dirs_only('.')
