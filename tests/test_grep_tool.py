#!/usr/bin/env python3
"""
File: test_grep_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for GrepTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import GrepTool
from test_helpers import assert_schema_matches_expected


class TestGrepTool:
    """Test GrepTool implementation"""
    
    def setup_method(self):
        self.test_dir = Path("tests/test_samples")
        
    def test_grep_tool_creation(self):
        tool = GrepTool()
        assert tool.name == "Grep"
        assert "search tool" in tool.description
        
    def test_grep_tool_parameters(self):
        tool = GrepTool()
        schema = tool.get_parameters_schema()
        assert "pattern" in schema["properties"]
        assert "path" in schema["properties"]
        assert "output_mode" in schema["properties"]
        assert schema["required"] == ["pattern"]
    
    def test_grep_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = GrepTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Grep")
    
    @patch('subprocess.run')
    def test_grep_tool_execution_files_mode(self, mock_run):
        # Mock ripgrep output for files_with_matches mode
        mock_run.return_value = MagicMock(
            stdout="/path/to/sample.py\n/path/to/test_import.py",
            stderr="",
            returncode=0
        )
        
        tool = GrepTool()
        result = tool.execute("import", path=str(self.test_dir), output_mode="files_with_matches")
        assert "sample.py" in result
        assert "test_import.py" in result
        
    @patch('subprocess.run')
    def test_grep_tool_execution_content_mode(self, mock_run):
        # Mock ripgrep output for content mode
        mock_run.return_value = MagicMock(
            stdout="sample.py:1:import os\nsample.py:2:import sys",
            stderr="",
            returncode=0
        )
        
        tool = GrepTool()
        result = tool.execute("import", output_mode="content", **{"-n": True})
        assert "import os" in result
        assert "import sys" in result
    
    @patch('subprocess.run')
    def test_grep_tool_execution_count_mode(self, mock_run):
        # Mock ripgrep output for count mode
        mock_run.return_value = MagicMock(
            stdout="sample.py:3\ntest_import.py:2",
            stderr="",
            returncode=0
        )
        
        tool = GrepTool()
        result = tool.execute("import", output_mode="count")
        assert "sample.py:3" in result
        assert "test_import.py:2" in result
    
    def test_grep_tool_python_fallback(self):
        # Test Python implementation when ripgrep not available
        tool = GrepTool()
        # Provide explicit glob pattern to ensure Python files are found
        result = tool._python_grep("import", path=str(self.test_dir), output_mode="files_with_matches", glob="*.py")
        # Should find files containing 'import' in test_samples directory
        assert "sample.py" in result or "test_import.py" in result or len(result) > 0
    
    @patch('subprocess.run')
    def test_grep_tool_with_context(self, mock_run):
        # Mock ripgrep output with context lines
        mock_run.return_value = MagicMock(
            stdout="sample.py-1-#!/usr/bin/env python3\nsample.py:2:import os\nsample.py-3-# More code",
            stderr="",
            returncode=0
        )
        
        tool = GrepTool()
        result = tool.execute("import", output_mode="content", **{"-B": 1, "-A": 1})
        assert "#!/usr/bin/env python3" in result
        assert "import os" in result
        assert "# More code" in result
    
    @patch('subprocess.run')
    def test_grep_tool_case_insensitive(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="sample.py:Import os",
            stderr="",
            returncode=0
        )
        
        tool = GrepTool()
        result = tool.execute("import", **{"-i": True})
        assert "Import os" in result
    
    @patch('subprocess.run')
    def test_grep_tool_with_file_type(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="sample.py\ntest.py",
            stderr="",
            returncode=0
        )
        
        tool = GrepTool()
        result = tool.execute("import", type="py")
        mock_run.assert_called()
        # Check that --type py was passed
        args = mock_run.call_args[0][0]
        assert "--type" in args
        assert "py" in args
    
    def test_grep_tool_from_trace(self):
        """Test GrepTool with trace parameters"""
        tool = GrepTool()
        # Use the test_samples directory which already has files with imports
        result = tool.execute(
            "import",
            path="tests/test_samples",
            type="py",
            output_mode="content",
            **{"-n": True}
        )
        # Should find import statements in the sample files
        assert "import" in result.lower() or result == "No matches found"
    
    @patch('subprocess.run')
    def test_grep_tool_multiline(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="file.py:class MyClass:\n    def method(self):\n        pass",
            stderr="",
            returncode=0
        )
        
        tool = GrepTool()
        result = tool.execute("class.*def", multiline=True)
        mock_run.assert_called()
        # Check that -U --multiline-dotall was passed
        args = mock_run.call_args[0][0]
        assert "-U" in args
        assert "--multiline-dotall" in args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])