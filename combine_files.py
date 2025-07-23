import os
import re

OUTPUT_FILE = "all_files_combined.txt"
ALLOWED_DIRS = [
    "EQUITR-coder",  # main package directory
    "src",           # source agents/api/etc.
]

# File extensions to include (focus on code)
ALLOWED_EXTENSIONS = {'.py', '.yaml', '.yml', '.md'}

# Skip these specific files/patterns
SKIP_FILES = {
    'requirements.txt',
    'setup.py', 
    '__pycache__',
    '.egg-info',
    'README.md'  # Skip READMEs to save space
}

# Skip these directories entirely
SKIP_DIRS = {
    '__pycache__',
    '.egg-info',
    'EQUITR_coder.egg-info'
}


def should_skip_file(filepath: str) -> bool:
    """Return True if file should be skipped."""
    filename = os.path.basename(filepath)
    _, ext = os.path.splitext(filename)
    
    # Skip if wrong extension
    if ext not in ALLOWED_EXTENSIONS:
        return True
        
    # Skip specific files
    if filename in SKIP_FILES:
        return True
        
    return False


def should_skip_dir(dirname: str) -> bool:
    """Return True if directory should be skipped."""
    return dirname in SKIP_DIRS or dirname.startswith('.')


def clean_content(content: str, filepath: str) -> str:
    """Clean content to reduce token count while preserving essential information."""
    # For Python files, remove excessive comments and docstrings
    if filepath.endswith('.py'):
        # Remove multi-line docstrings (but keep class/function signatures)
        content = re.sub(r'"""[\s\S]*?"""', '', content)
        content = re.sub(r"'''[\s\S]*?'''", '', content)
        
        # Remove single-line comments that are just explanatory
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Keep imports, class/function definitions, and code
            stripped = line.strip()
            if (not stripped.startswith('#') or 
                'TODO' in stripped or 
                'FIXME' in stripped or
                'NOTE' in stripped):
                cleaned_lines.append(line)
        content = '\n'.join(cleaned_lines)
    
    # For markdown files, keep only essential sections
    elif filepath.endswith('.md'):
        # Keep only headers and brief descriptions
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if (line.startswith('#') or 
                line.strip() == '' or
                len(line.strip()) < 100):  # Keep short lines
                cleaned_lines.append(line)
        content = '\n'.join(cleaned_lines[:50])  # Limit to first 50 lines
    
    return content


def is_hidden(path: str) -> bool:
    """Return True if any part of the path is a hidden file or directory (starts with a dot)."""
    for part in path.split(os.sep):
        if part.startswith('.'):
            return True
    return False


def main() -> None:
    repo_root = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(repo_root, OUTPUT_FILE), "w", encoding="utf-8") as out_f:
        # Walk only the directories we care about
        for base in ALLOWED_DIRS:
            base_path = os.path.join(repo_root, base)
            if not os.path.isdir(base_path):
                continue

            for dirpath, dirnames, filenames in os.walk(base_path):
                # Skip unwanted directories
                dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

                for filename in sorted(filenames):
                    file_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(file_path, repo_root)

                    # Skip the output file itself and unwanted files
                    if rel_path == OUTPUT_FILE or is_hidden(rel_path) or should_skip_file(file_path):
                        continue

                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as in_f:
                            content = in_f.read()
                        
                        # Clean content to reduce tokens
                        content = clean_content(content, file_path)
                        
                        # Skip if content is now empty or very small
                        if len(content.strip()) < 10:
                            continue
                            
                    except Exception as exc:
                        content = f"<Could not read file: {exc}>\n"

                    header = f"===== {rel_path} =====\n"
                    out_f.write(header)
                    out_f.write(content)
                    out_f.write("\n\n")


if __name__ == "__main__":
    main() 