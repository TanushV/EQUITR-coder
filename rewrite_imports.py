#!/usr/bin/env python3
"""
Script to rewrite imports from EQUITR_coder and src to equitrcoder
"""
import os
import re
from pathlib import Path


def rewrite_imports_in_file(file_path: Path):
    """Rewrite imports in a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace EQUITR_coder imports
        content = re.sub(r'from EQUITR_coder\.', 'from equitrcoder.', content)
        content = re.sub(r'import EQUITR_coder\.', 'import equitrcoder.', content)
        content = re.sub(r'from EQUITR_coder import', 'from equitrcoder import', content)
        content = re.sub(r'import EQUITR_coder', 'import equitrcoder', content)
        
        # Replace src imports
        content = re.sub(r'from src\.', 'from equitrcoder.', content)
        content = re.sub(r'import src\.', 'import equitrcoder.', content)
        
        # Handle relative imports that might be broken
        content = re.sub(r'from \.\.EQUITR_coder\.', 'from ..equitrcoder.', content)
        content = re.sub(r'from \.\.src\.', 'from ..equitrcoder.', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated imports in: {file_path}")
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def main():
    """Main function to rewrite imports in all Python files."""
    # Process equitrcoder directory
    equitrcoder_path = Path("equitrcoder")
    if equitrcoder_path.exists():
        for py_file in equitrcoder_path.rglob("*.py"):
            rewrite_imports_in_file(py_file)
    
    # Process root level Python files
    for py_file in Path(".").glob("*.py"):
        if py_file.name != "rewrite_imports.py":  # Skip this script
            rewrite_imports_in_file(py_file)
    
    # Process examples and other directories
    for directory in ["examples", "testing"]:
        dir_path = Path(directory)
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                rewrite_imports_in_file(py_file)


if __name__ == "__main__":
    main() 