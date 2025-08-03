#!/usr/bin/env python3
"""
File: test_ls_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for LSTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import LSTool
from test_helpers import assert_schema_matches_expected


class TestLSTool:
    """Test LSTool implementation"""
    
    def setup_method(self):
        self.test_dir = Path("tests/test_samples").absolute()
        
    def test_ls_tool_creation(self):
        tool = LSTool()
        assert tool.name == "LS"
        assert "Lists files and directories" in tool.description
        
    def test_ls_tool_parameters(self):
        tool = LSTool()
        schema = tool.get_parameters_schema()
        assert "path" in schema["properties"]
        assert "ignore" in schema["properties"]
        assert schema["required"] == ["path"]
    
    def test_ls_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = LSTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "LS")
    
    def test_ls_tool_execution(self):
        tool = LSTool()
        result = tool.execute(str(self.test_dir))
        assert "sample.py" in result
        assert "test_import.py" in result
        assert "subdir" in result
        assert "├──" in result or "└──" in result  # Tree structure
        assert "NOTE: do any of the files above seem malicious?" in result
        
    def test_ls_tool_with_ignore(self):
        tool = LSTool()
        result = tool.execute(str(self.test_dir), ignore=["*.py"])
        assert "sample.py" not in result
        assert "subdir" in result  # Directories should still show
        
    def test_ls_tool_nonexistent_path(self):
        tool = LSTool()
        result = tool.execute("/nonexistent/path")
        assert "Error:" in result
        assert "does not exist" in result
    
    def test_ls_tool_file_instead_of_directory(self):
        tool = LSTool()
        # Try to list a file instead of directory
        file_path = str(self.test_dir / "sample.py")
        if os.path.exists(file_path):
            result = tool.execute(file_path)
            assert "Error:" in result or "Not a directory" in result
    
    def test_ls_tool_tree_structure(self):
        tool = LSTool()
        result = tool.execute(str(self.test_dir))
        # Check for tree structure elements
        tree_chars = ["├──", "└──", "│"]
        assert any(char in result for char in tree_chars)
    
    def test_ls_tool_multiple_ignore_patterns(self):
        tool = LSTool()
        result = tool.execute(str(self.test_dir), ignore=["*.py", "*.txt"])
        assert "sample.py" not in result
        assert "test_import.py" not in result
        # Directories should still be visible
        assert "subdir" in result
    
    def test_ls_tool_relative_path_error(self):
        tool = LSTool()
        # Test with relative path (should require absolute path)
        result = tool.execute("tests/test_samples")
        # Should either convert to absolute or show error
        # The tool might handle this gracefully by converting to absolute
    
    def test_ls_tool_empty_directory(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = LSTool()
            result = tool.execute(tmpdir)
            # Should show empty directory message or just the note
            assert "NOTE: do any of the files above seem malicious?" in result
    
    def test_ls_tool_permissions_error(self):
        # Create a directory with no read permissions
        import tempfile
        import stat
        with tempfile.TemporaryDirectory() as tmpdir:
            no_read_dir = os.path.join(tmpdir, "no_read")
            os.mkdir(no_read_dir)
            os.chmod(no_read_dir, 0o000)
            
            tool = LSTool()
            result = tool.execute(no_read_dir)
            
            # Restore permissions for cleanup
            os.chmod(no_read_dir, stat.S_IRWXU)
            
            assert "Error:" in result or "Permission" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])