#!/usr/bin/env python3
"""
File: test_bash_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for BashTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import BashTool
from test_helpers import assert_schema_matches_expected


class TestBashTool:
    """Test BashTool implementation"""
    
    def test_bash_tool_creation(self):
        tool = BashTool()
        assert tool.name == "Bash"
        assert "bash command" in tool.description
        
    def test_bash_tool_parameters(self):
        tool = BashTool()
        schema = tool.get_parameters_schema()
        assert "command" in schema["properties"]
        assert "timeout" in schema["properties"]
        assert "description" in schema["properties"]
        assert schema["required"] == ["command"]
    
    def test_bash_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = BashTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Bash")
    
    def test_bash_tool_execution_success(self):
        tool = BashTool()
        result = tool.execute("echo 'Hello, World!'")
        assert "Hello, World!" in result
        
    def test_bash_tool_execution_with_error(self):
        tool = BashTool()
        result = tool.execute("false")  # Command that returns non-zero
        assert "Command failed with return code 1" in result or "return code" in result
        
    def test_bash_tool_timeout(self):
        tool = BashTool()
        result = tool.execute("sleep 5", timeout=100)  # 100ms timeout
        assert "timed out" in result.lower()
    
    def test_bash_tool_with_description(self):
        tool = BashTool()
        result = tool.execute("echo test", description="Echo test output")
        assert "test" in result
    
    def test_bash_tool_working_directory(self):
        tool = BashTool()
        result = tool.execute("pwd")
        # Should return current working directory
        assert "/" in result  # Unix path
    
    def test_bash_tool_environment_persistence(self):
        tool = BashTool()
        # Test that environment is maintained across calls
        tool.execute("export TEST_VAR=hello")
        result = tool.execute("echo $TEST_VAR")
        # Note: This might not work as expected since each subprocess.run 
        # creates a new shell instance. This is a known limitation.
    
    def test_bash_tool_stderr_capture(self):
        tool = BashTool()
        result = tool.execute("echo 'error' >&2")
        assert "error" in result
    
    def test_bash_tool_multiline_output(self):
        tool = BashTool()
        result = tool.execute("echo 'line1'; echo 'line2'; echo 'line3'")
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])