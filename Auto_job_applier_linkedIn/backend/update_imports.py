"""
Script to update imports for backend reorganization.
Updates relative imports to use backend.* prefix.
"""
import os
import re
from pathlib import Path


def update_imports_in_file(filepath: Path) -> bool:
    """Update imports in a single file. Returns True if changes were made."""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ❌ Error reading {filepath}: {e}")
        return False
    
    original_content = content
    
    # For files inside backend/, use relative imports
    # from backend.core.X -> from backend.core.X (when running from project root)
    # OR keep as from backend.core.X (when running from backend/)
    
    # Since we want the backend to be self-contained, keep internal imports relative
    # Only update imports that reference the old structure
    
    replacements = [
        # Fix imports that might reference old paths
        (r'^from core\.', 'from backend.core.'),
        (r'^from api\.', 'from backend.api.'),
        (r'^from scripts\.', 'from backend.scripts.'),
        (r'^import core\.', 'import backend.core.'),
        (r'^import api\.', 'import backend.api.'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Updated: {filepath.name}")
            return True
        except Exception as e:
            print(f"  ❌ Error writing {filepath}: {e}")
            return False
    
    return False


def main():
    """Update imports in all Python files in backend/"""
    backend_path = Path(__file__).parent
    
    print("=" * 60)
    print("🔄 Updating imports in backend/")
    print("=" * 60)
    
    updated_count = 0
    total_count = 0
    
    for py_file in backend_path.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        if py_file.name == 'update_imports.py':
            continue
            
        total_count += 1
        if update_imports_in_file(py_file):
            updated_count += 1
    
    print()
    print(f"📊 Summary: Updated {updated_count}/{total_count} files")
    print("=" * 60)


if __name__ == '__main__':
    main()
