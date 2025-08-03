#!/usr/bin/env python3
"""
File: test_write_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for WriteTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os
import tempfile
import shutil

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import WriteTool
from test_helpers import assert_schema_matches_expected


class TestWriteTool:
    """Test WriteTool implementation"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
        
    def test_write_tool_creation(self):
        tool = WriteTool()
        assert tool.name == "Write"
        assert "Writes a file" in tool.description
        
    def test_write_tool_parameters(self):
        tool = WriteTool()
        schema = tool.get_parameters_schema()
        assert "file_path" in schema["properties"]
        assert "content" in schema["properties"]
        assert schema["required"] == ["file_path", "content"]
    
    def test_write_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = WriteTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Write")
        
    def test_write_tool_execution(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "test.txt")
        content = "Hello, World!"
        
        result = tool.execute(test_file, content)
        assert "File created successfully" in result
        assert test_file in result
        
        with open(test_file) as f:
            assert f.read() == content
            
    def test_write_tool_create_directories(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "subdir", "nested", "test.txt")
        
        result = tool.execute(test_file, "content")
        assert "File created successfully" in result
        assert os.path.exists(test_file)
        
    def test_write_tool_overwrite(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        # Write initial content
        tool.execute(test_file, "initial")
        
        # Overwrite
        result = tool.execute(test_file, "overwritten")
        assert "File created successfully" in result
        
        with open(test_file) as f:
            assert f.read() == "overwritten"
    
    def test_write_tool_empty_content(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "empty.txt")
        
        result = tool.execute(test_file, "")
        assert "File created successfully" in result
        
        assert os.path.exists(test_file)
        with open(test_file) as f:
            assert f.read() == ""
    
    def test_write_tool_multiline_content(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "multiline.txt")
        content = "Line 1\nLine 2\nLine 3"
        
        result = tool.execute(test_file, content)
        assert "File created successfully" in result
        
        with open(test_file) as f:
            assert f.read() == content
    
    def test_write_tool_special_characters(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "special.txt")
        content = 'Special chars: "quotes", \'apostrophes\', \ttabs, \nnewlines'
        
        result = tool.execute(test_file, content)
        assert "File created successfully" in result
        
        with open(test_file) as f:
            assert f.read() == content
    
    def test_write_tool_unicode_content(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "unicode.txt")
        content = "Unicode: 你好世界 🌍 émojis"
        
        result = tool.execute(test_file, content)
        assert "File created successfully" in result
        
        with open(test_file, encoding='utf-8') as f:
            assert f.read() == content
    
    def test_write_tool_permissions_error(self):
        # Try to write to a read-only directory
        import stat
        readonly_dir = os.path.join(self.temp_dir, "readonly")
        os.mkdir(readonly_dir)
        os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)  # Read-only
        
        tool = WriteTool()
        test_file = os.path.join(readonly_dir, "test.txt")
        
        result = tool.execute(test_file, "content")
        
        # Restore permissions for cleanup
        os.chmod(readonly_dir, stat.S_IRWXU)
        
        assert "Error:" in result or "Permission" in result
    
    def test_write_tool_invalid_path(self):
        tool = WriteTool()
        # Try to write with invalid characters in path (null byte)
        result = tool.execute("/tmp/test\x00.txt", "content")
        assert "Error:" in result
    
    def test_write_tool_python_file(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "script.py")
        content = '''#!/usr/bin/env python3
"""Test Python script"""

def main():
    print("Hello from Python!")

if __name__ == "__main__":
    main()
'''
        
        result = tool.execute(test_file, content)
        assert "File created successfully" in result
        
        with open(test_file) as f:
            written_content = f.read()
        assert written_content == content
        assert "#!/usr/bin/env python3" in written_content
    
    def test_write_tool_json_content(self):
        tool = WriteTool()
        test_file = os.path.join(self.temp_dir, "data.json")
        content = '''{
    "name": "test",
    "version": "1.0.0",
    "items": [1, 2, 3]
}'''
        
        result = tool.execute(test_file, content)
        assert "File created successfully" in result
        
        # Verify it's valid JSON
        import json
        with open(test_file) as f:
            data = json.load(f)
        assert data["name"] == "test"
        assert data["items"] == [1, 2, 3]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])