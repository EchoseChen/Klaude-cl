#!/usr/bin/env python3
"""
File: test_edit_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for EditTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os
import tempfile

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import EditTool
from test_helpers import assert_schema_matches_expected


class TestEditTool:
    """Test EditTool implementation"""
    
    def setup_method(self):
        # Create a temporary file for editing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        self.temp_file.write("def old_function():\n    return 42\n")
        self.temp_file.close()
        
    def teardown_method(self):
        # Clean up
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
            
    def test_edit_tool_creation(self):
        tool = EditTool()
        assert tool.name == "Edit"
        assert "string replacements" in tool.description
        
    def test_edit_tool_parameters(self):
        tool = EditTool()
        schema = tool.get_parameters_schema()
        assert "file_path" in schema["properties"]
        assert "old_string" in schema["properties"]
        assert "new_string" in schema["properties"]
        assert "replace_all" in schema["properties"]
        assert schema["required"] == ["file_path", "old_string", "new_string"]
    
    def test_edit_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = EditTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Edit")
    
    def test_edit_tool_execution(self):
        tool = EditTool()
        result = tool.execute(
            self.temp_file.name,
            "old_function",
            "new_function"
        )
        assert "has been updated" in result
        
        # Verify the change
        with open(self.temp_file.name) as f:
            content = f.read()
        assert "new_function" in content
        assert "old_function" not in content
        
    def test_edit_tool_multiple_occurrences(self):
        # Write content with multiple occurrences
        with open(self.temp_file.name, 'w') as f:
            f.write("foo bar foo baz foo")
            
        tool = EditTool()
        result = tool.execute(self.temp_file.name, "foo", "replaced")
        assert "found 3 times" in result
        
    def test_edit_tool_replace_all(self):
        with open(self.temp_file.name, 'w') as f:
            f.write("foo bar foo baz foo")
            
        tool = EditTool()
        result = tool.execute(self.temp_file.name, "foo", "replaced", replace_all=True)
        assert "has been updated" in result
        
        with open(self.temp_file.name) as f:
            content = f.read()
        assert content == "replaced bar replaced baz replaced"
        
    def test_edit_tool_string_not_found(self):
        tool = EditTool()
        result = tool.execute(self.temp_file.name, "nonexistent", "new")
        assert "Error:" in result
        assert "not found" in result
        
    def test_edit_tool_same_strings(self):
        tool = EditTool()
        result = tool.execute(self.temp_file.name, "same", "same")
        assert "Error:" in result
        assert "must be different" in result
    
    def test_edit_tool_nonexistent_file(self):
        tool = EditTool()
        result = tool.execute("/nonexistent/file.txt", "old", "new")
        assert "Error:" in result
        assert "does not exist" in result or "No such file" in result
    
    def test_edit_tool_multiline_string(self):
        with open(self.temp_file.name, 'w') as f:
            f.write("Line 1\nLine 2\nLine 3")
        
        tool = EditTool()
        result = tool.execute(
            self.temp_file.name,
            "Line 1\nLine 2",
            "Modified Line 1\nModified Line 2"
        )
        assert "has been updated" in result
        
        with open(self.temp_file.name) as f:
            content = f.read()
        assert "Modified Line 1\nModified Line 2\nLine 3" == content
    
    def test_edit_tool_with_special_characters(self):
        with open(self.temp_file.name, 'w') as f:
            f.write('function test() { return "value"; }')
        
        tool = EditTool()
        result = tool.execute(
            self.temp_file.name,
            'return "value"',
            'return "new value"'
        )
        assert "has been updated" in result
        
        with open(self.temp_file.name) as f:
            content = f.read()
        assert 'return "new value"' in content
    
    def test_edit_tool_partial_match_warning(self):
        with open(self.temp_file.name, 'w') as f:
            f.write("foobar foobaz foo")
        
        tool = EditTool()
        # Trying to replace "foo" which appears as part of other words
        result = tool.execute(self.temp_file.name, "foo", "replaced")
        # Should warn about multiple occurrences
        assert "found 3 times" in result
    
    def test_edit_tool_preserve_indentation(self):
        with open(self.temp_file.name, 'w') as f:
            f.write("def func():\n    old_code\n    more_code")
        
        tool = EditTool()
        result = tool.execute(
            self.temp_file.name,
            "    old_code",
            "    new_code"
        )
        assert "has been updated" in result
        
        with open(self.temp_file.name) as f:
            content = f.read()
        # Indentation should be preserved
        assert "    new_code" in content
        assert content == "def func():\n    new_code\n    more_code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])