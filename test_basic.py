#!/usr/bin/env python3
"""Basic test to check file system operations."""

import os
import json
from pathlib import Path

def test_basic():
    print("=== BASIC FILE SYSTEM TEST ===")
    
    # Test 1: Check current directory
    cwd = Path.cwd()
    print(f"1. Current directory: {cwd}")
    print(f"   Write access: {os.access(cwd, os.W_OK)}")
    
    # Test 2: Create a test file
    test_file = Path("test_file.txt")
    try:
        test_file.write_text("test content")
        print(f"2. ✅ Successfully created {test_file}")
        
        # Read it back
        content = test_file.read_text()
        print(f"   Content: '{content}'")
        
        # Delete it
        test_file.unlink()
        print("   ✅ Successfully deleted test file")
    except Exception as e:
        print(f"2. ❌ Failed to create test file: {e}")
    
    # Test 3: Create downloads directory
    downloads_dir = Path("downloads")
    try:
        downloads_dir.mkdir(exist_ok=True)
        print(f"3. ✅ Downloads directory: {downloads_dir.absolute()}")
        
        # Test creating a subdirectory
        test_subdir = downloads_dir / "test_domain"
        test_subdir.mkdir(exist_ok=True)
        print(f"   ✅ Created subdirectory: {test_subdir}")
        
        # Test creating a file in subdirectory
        test_file = test_subdir / "test.txt"
        test_file.write_text("test content")
        print(f"   ✅ Created file in subdirectory: {test_file}")
        
        # Cleanup
        test_file.unlink()
        test_subdir.rmdir()
        print("   ✅ Cleanup completed")
        
    except Exception as e:
        print(f"3. ❌ Downloads directory operations failed: {e}")
    
    # Test 4: JSON file operations
    json_file = Path("test.json")
    try:
        test_data = {"test": "data", "array": [1, 2, 3]}
        json_file.write_text(json.dumps(test_data, indent=2))
        print(f"4. ✅ Created JSON file: {json_file}")
        
        # Read it back
        loaded_data = json.loads(json_file.read_text())
        print(f"   Loaded data: {loaded_data}")
        
        # Delete it
        json_file.unlink()
        print("   ✅ Deleted JSON file")
    except Exception as e:
        print(f"4. ❌ JSON operations failed: {e}")
    
    print("=== BASIC TEST COMPLETED ===")

if __name__ == "__main__":
    test_basic()