#!/usr/bin/env python3
"""
File: test_multiedit_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for MultiEditTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os
import tempfile

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import MultiEditTool
from test_helpers import assert_schema_matches_expected


class TestMultiEditTool:
    """Test MultiEditTool implementation"""
    
    def setup_method(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        self.temp_file.write("def func1():\n    pass\n\ndef func2():\n    pass\n")
        self.temp_file.close()
        
    def teardown_method(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
            
    def test_multiedit_tool_creation(self):
        tool = MultiEditTool()
        assert tool.name == "MultiEdit"
        assert "multiple edits" in tool.description
        
    def test_multiedit_tool_parameters(self):
        tool = MultiEditTool()
        schema = tool.get_parameters_schema()
        assert "file_path" in schema["properties"]
        assert "edits" in schema["properties"]
        assert schema["required"] == ["file_path", "edits"]
    
    def test_multiedit_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = MultiEditTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "MultiEdit")
        
    def test_multiedit_tool_execution(self):
        tool = MultiEditTool()
        edits = [
            {"old_string": "func1", "new_string": "function1"},
            {"old_string": "func2", "new_string": "function2"}
        ]
        result = tool.execute(self.temp_file.name, edits)
        assert "Applied 2 edit(s)" in result
        
        with open(self.temp_file.name) as f:
            content = f.read()
        assert "function1" in content
        assert "function2" in content
        assert "func1" not in content
        assert "func2" not in content
        
    def test_multiedit_tool_create_new_file(self):
        new_file = self.temp_file.name + ".new"
        try:
            tool = MultiEditTool()
            edits = [
                {"old_string": "", "new_string": "#!/usr/bin/env python3\n# New file\n"}
            ]
            result = tool.execute(new_file, edits)
            assert "Applied 1 edit(s)" in result
            assert "Created new file" in result
            
            with open(new_file) as f:
                content = f.read()
            assert "#!/usr/bin/env python3" in content
        finally:
            if os.path.exists(new_file):
                os.unlink(new_file)
                
    def test_multiedit_tool_sequential_edits(self):
        with open(self.temp_file.name, 'w') as f:
            f.write("original text here")
            
        tool = MultiEditTool()
        edits = [
            {"old_string": "original", "new_string": "modified"},
            {"old_string": "modified text", "new_string": "final text"}
        ]
        result = tool.execute(self.temp_file.name, edits)
        
        with open(self.temp_file.name) as f:
            content = f.read()
        assert content == "final text here"
    
    def test_multiedit_tool_with_replace_all(self):
        with open(self.temp_file.name, 'w') as f:
            f.write("foo bar foo baz foo")
        
        tool = MultiEditTool()
        edits = [
            {"old_string": "foo", "new_string": "replaced", "replace_all": True}
        ]
        result = tool.execute(self.temp_file.name, edits)
        assert "Applied 1 edit(s)" in result
        
        with open(self.temp_file.name) as f:
            content = f.read()
        assert content == "replaced bar replaced baz replaced"
    
    def test_multiedit_tool_mixed_replace_modes(self):
        with open(self.temp_file.name, 'w') as f:
            f.write("foo bar foo baz\ntest test test")
        
        tool = MultiEditTool()
        edits = [
            {"old_string": "foo", "new_string": "FOO"},  # First occurrence only
            {"old_string": "test", "new_string": "TEST", "replace_all": True}  # All occurrences
        ]
        result = tool.execute(self.temp_file.name, edits)
        
        with open(self.temp_file.name) as f:
            content = f.read()
        assert content == "FOO bar foo baz\nTEST TEST TEST"
    
    def test_multiedit_tool_failed_edit(self):
        tool = MultiEditTool()
        edits = [
            {"old_string": "func1", "new_string": "function1"},
            {"old_string": "nonexistent", "new_string": "new"}  # This will fail
        ]
        result = tool.execute(self.temp_file.name, edits)
        assert "Error:" in result
        assert "not found" in result
        
        # File should remain unchanged due to atomic operation
        with open(self.temp_file.name) as f:
            content = f.read()
        assert "func1" in content  # Original content preserved
    
    def test_multiedit_tool_empty_edits(self):
        tool = MultiEditTool()
        result = tool.execute(self.temp_file.name, [])
        assert "Error:" in result or "No edits" in result
    
    def test_multiedit_tool_complex_edits(self):
        with open(self.temp_file.name, 'w') as f:
            f.write('''class MyClass:
    def method1(self):
        return "result1"
    
    def method2(self):
        return "result2"
''')
        
        tool = MultiEditTool()
        edits = [
            {"old_string": "MyClass", "new_string": "UpdatedClass"},
            {"old_string": "method1", "new_string": "updated_method1"},
            {"old_string": "method2", "new_string": "updated_method2"},
            {"old_string": '"result1"', "new_string": '"updated_result1"'},
            {"old_string": '"result2"', "new_string": '"updated_result2"'}
        ]
        result = tool.execute(self.temp_file.name, edits)
        assert "Applied 5 edit(s)" in result
        
        with open(self.temp_file.name) as f:
            content = f.read()
        assert "UpdatedClass" in content
        assert "updated_method1" in content
        assert "updated_method2" in content
        assert '"updated_result1"' in content
        assert '"updated_result2"' in content
    
    def test_multiedit_tool_from_trace(self):
        """Test MultiEditTool with trace-like file header addition"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write("def main():")
        temp_file.close()
        
        try:
            tool = MultiEditTool()
            edits = [{
                "old_string": "def main():",
                "new_string": '#!/usr/bin/env python3\n"""\nFile: main.py\nAuthor: Claude Code Assistant\nCreated: 2025-08-03\nDescription: Main entry point for the claude-code-cli application\n\nThis file is part of the klaude project.\n"""\n\n\ndef main():'
            }]
            result = tool.execute(temp_file.name, edits)
            assert "Applied 1 edit(s)" in result
            
            with open(temp_file.name) as f:
                content = f.read()
            assert "#!/usr/bin/env python3" in content
            assert "Author: Claude Code Assistant" in content
            assert "def main():" in content
        finally:
            os.unlink(temp_file.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])