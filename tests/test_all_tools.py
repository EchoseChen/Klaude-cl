#!/usr/bin/env python3
"""
File: test_all_tools.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Main test runner that runs all individual tool tests

This file is part of the klaude project.
"""

import pytest
import sys
import os

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    """Run all tool tests"""
    test_files = [
        "test_task_tool.py",
        "test_bash_tool.py",
        "test_glob_tool.py",
        "test_grep_tool.py",
        "test_ls_tool.py",
        "test_read_tool.py",
        "test_edit_tool.py",
        "test_multiedit_tool.py",
        "test_write_tool.py",
        "test_notebook_tools.py",
        "test_webfetch_tool.py",
        "test_todowrite_tool.py",
        "test_websearch_tool.py",
        "test_tool_schemas.py"
    ]
    
    # Run pytest with all test files
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_paths = [os.path.join(test_dir, f) for f in test_files]
    
    # Add verbose flag and coverage if needed
    args = test_paths + ["-v", "--tb=short"]
    
    return pytest.main(args)


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)