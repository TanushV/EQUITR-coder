#!/usr/bin/env python3
"""
Audit script to verify hello world project requirements
"""
import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(filepath):
    """Check if a file exists"""
    return os.path.isfile(filepath)

def check_directory_exists(dirpath):
    """Check if a directory exists"""
    return os.path.isdir(dirpath)

def check_function_in_file(filepath, function_name):
    """Check if a function exists in a Python file"""
    if not os.path.isfile(filepath):
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            return f'def {function_name}(' in content
    except Exception:
        return False

def run_audit():
    """Run the complete audit"""
    print("🔍 Starting Hello World Project Audit...")
    print("=" * 50)
    
    failures = []
    
    # Check 1: main.py with hello_world() function
    print("1. Checking main.py with hello_world() function...")
    if not check_file_exists('main.py'):
        failures.append("❌ main.py file is missing")
    elif not check_function_in_file('main.py', 'hello_world'):
        failures.append("❌ hello_world() function not found in main.py")
    else:
        print("   ✅ main.py with hello_world() function found")
    
    # Check 2: requirements.txt file
    print("2. Checking requirements.txt file...")
    if not check_file_exists('requirements.txt'):
        failures.append("❌ requirements.txt file is missing")
    else:
        print("   ✅ requirements.txt file found")
    
    # Check 3: README.md file
    print("3. Checking README.md file...")
    if not check_file_exists('README.md'):
        failures.append("❌ README.md file is missing")
    else:
        print("   ✅ README.md file found")
    
    # Check 4: tests/ directory
    print("4. Checking tests/ directory...")
    if not check_directory_exists('tests'):
        failures.append("❌ tests/ directory is missing")
    else:
        print("   ✅ tests/ directory found")
    
    # Check 5: Error handling in functions
    print("5. Checking for proper error handling...")
    if check_file_exists('main.py'):
        try:
            with open('main.py', 'r') as f:
                content = f.read()
                if 'try:' not in content and 'except' not in content:
                    failures.append("❌ No error handling found in main.py")
                else:
                    print("   ✅ Error handling found")
        except Exception:
            failures.append("❌ Could not check error handling in main.py")
    
    print("\n" + "=" * 50)
    
    if failures:
        print("🚨 AUDIT FAILED!")
        print("The following requirements are not met:")
        for failure in failures:
            print(f"  {failure}")
        print(f"\nTotal failures: {len(failures)}")
        return 1
    else:
        print("✅ AUDIT PASSED! All requirements are met.")
        return 0

if __name__ == "__main__":
    sys.exit(run_audit())