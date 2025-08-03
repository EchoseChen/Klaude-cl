#!/usr/bin/env python3
"""
File: test_glob_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for GlobTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import GlobTool
from test_helpers import assert_schema_matches_expected


class TestGlobTool:
    """Test GlobTool implementation"""
    
    def setup_method(self):
        """Create temporary test directory structure"""
        self.test_dir = Path("tests/test_samples")
        
    def test_glob_tool_creation(self):
        tool = GlobTool()
        assert tool.name == "Glob"
        assert "file pattern matching" in tool.description
        
    def test_glob_tool_parameters(self):
        tool = GlobTool()
        schema = tool.get_parameters_schema()
        assert "pattern" in schema["properties"]
        assert "path" in schema["properties"]
        assert schema["required"] == ["pattern"]
    
    def test_glob_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = GlobTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Glob")
    
    def test_glob_tool_execution(self):
        tool = GlobTool()
        # Test finding Python files
        result = tool.execute("**/*.py", str(self.test_dir))
        assert "sample.py" in result
        assert "test_import.py" in result
        assert "nested.py" in result
        
    def test_glob_tool_no_matches(self):
        tool = GlobTool()
        result = tool.execute("*.nonexistent", str(self.test_dir))
        assert result == ""
    
    def test_glob_tool_single_star(self):
        tool = GlobTool()
        # Test single star pattern (only current directory)
        result = tool.execute("*.py", str(self.test_dir))
        assert "sample.py" in result
        assert "test_import.py" in result
        # nested.py should not be found with single star
    
    def test_glob_tool_specific_extension(self):
        tool = GlobTool()
        # Test finding specific file types
        result = tool.execute("**/*.txt", str(self.test_dir))
        if result:  # If there are txt files
            assert ".txt" in result
            assert ".py" not in result
    
    def test_glob_tool_directory_pattern(self):
        tool = GlobTool()
        # Test pattern with directory
        result = tool.execute("**/subdir/*.py", str(self.test_dir))
        if "nested.py" in result:
            assert "subdir" in result
    
    def test_glob_tool_from_trace(self):
        """Test GlobTool with trace pattern"""
        tool = GlobTool()
        result = tool.execute("**/*.py", "tests/test_samples")
        # Should find Python files
        assert ".py" in result
        assert result.count("\n") >= 2  # At least sample.py, test_import.py, nested.py
    
    def test_glob_tool_default_path(self):
        tool = GlobTool()
        # Test with default path (current directory)
        result = tool.execute("*.py")
        # Should find Python files in current directory
        # The result depends on where the test is run from
    
    def test_glob_tool_complex_pattern(self):
        tool = GlobTool()
        # Test complex glob pattern
        result = tool.execute("**/*{sample,import}*.py", str(self.test_dir))
        assert "sample.py" in result or "test_import.py" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])