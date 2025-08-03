#!/usr/bin/env python3
"""
File: test_read_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for ReadTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import ReadTool


class TestReadTool:
    """Test ReadTool implementation"""
    
    def setup_method(self):
        self.test_file = Path("tests/test_samples/sample.py").absolute()
        
    def test_read_tool_creation(self):
        tool = ReadTool()
        assert tool.name == "Read"
        assert "Reads a file" in tool.description
        
    def test_read_tool_parameters(self):
        tool = ReadTool()
        schema = tool.get_parameters_schema()
        assert "file_path" in schema["properties"]
        assert "offset" in schema["properties"]
        assert "limit" in schema["properties"]
        assert schema["required"] == ["file_path"]
    
    def test_read_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = ReadTool()
        schema = tool.to_function_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "Read"
        assert "Reads a file" in schema["function"]["description"]
        
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert params["required"] == ["file_path"]
        assert params["additionalProperties"] == False
        assert params["$schema"] == "http://json-schema.org/draft-07/schema#"
        
        props = params["properties"]
        assert props["file_path"]["type"] == "string"
        assert props["file_path"]["description"] == "The absolute path to the file to read"
        
        assert props["offset"]["type"] == "number"
        assert "line number to start reading from" in props["offset"]["description"]
        
        assert props["limit"]["type"] == "number"
        assert "number of lines to read" in props["limit"]["description"]
    
    def test_read_tool_execution(self):
        tool = ReadTool()
        result = tool.execute(str(self.test_file))
        assert "#!/usr/bin/env python3" in result
        assert "Sample Python file for testing tools" in result
        assert "def hello_world():" in result
        # Check for line numbers (cat -n format)
        assert "\t" in result  # Tab separator
        assert "<system-reminder>" in result
        
    def test_read_tool_with_offset_limit(self):
        tool = ReadTool()
        result = tool.execute(str(self.test_file), offset=5, limit=3)
        lines = result.split("\n")
        # Should start at line 5 - check for the line number format
        line_numbers = []
        for line in lines:
            if line.strip() and not line.startswith("<system-reminder>"):
                # Extract line number from format like "     5\t..."
                parts = line.split("\t", 1)
                if parts[0].strip().isdigit():
                    line_numbers.append(int(parts[0].strip()))
        
        # Should start at line 5 and have 3 consecutive lines
        if line_numbers:
            assert line_numbers[0] == 5
            assert len(line_numbers) <= 3
        
    def test_read_tool_nonexistent_file(self):
        tool = ReadTool()
        result = tool.execute("/nonexistent/file.txt")
        assert "Error:" in result
        assert "does not exist" in result
        
    def test_read_tool_directory(self):
        tool = ReadTool()
        result = tool.execute(str(Path("tests/test_samples").absolute()))
        assert "EISDIR" in result
    
    def test_read_tool_empty_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            tool = ReadTool()
            result = tool.execute(temp_path)
            assert "<system-reminder>" in result
            assert "empty file" in result.lower()
        finally:
            os.unlink(temp_path)
    
    def test_read_tool_large_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Write more than 2000 lines
            for i in range(2500):
                f.write(f"Line {i+1}\n")
            temp_path = f.name
        
        try:
            tool = ReadTool()
            result = tool.execute(temp_path)
            # Should only read first 2000 lines by default
            lines = result.split("\n")
            content_lines = [l for l in lines if l.strip() and not l.startswith("<system-reminder>")]
            assert len(content_lines) <= 2000
        finally:
            os.unlink(temp_path)
    
    def test_read_tool_line_truncation(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Write a very long line (>2000 chars)
            long_line = "x" * 2500
            f.write(f"Short line\n{long_line}\nAnother short line")
            temp_path = f.name
        
        try:
            tool = ReadTool()
            result = tool.execute(temp_path)
            # Long line should be truncated
            assert "x" * 2000 in result
            assert "x" * 2001 not in result
            assert "Another short line" in result
        finally:
            os.unlink(temp_path)
    
    def test_read_tool_binary_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(b'\x00\x01\x02\x03\x04')
            temp_path = f.name
        
        try:
            tool = ReadTool()
            result = tool.execute(temp_path)
            # Should handle binary file (might show error or warning)
            assert "Error:" in result or "binary" in result.lower()
        finally:
            os.unlink(temp_path)
    
    def test_read_tool_with_permissions_error(self):
        import tempfile
        import stat
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Secret content")
            temp_path = f.name
        
        # Remove read permissions
        os.chmod(temp_path, 0o000)
        
        try:
            tool = ReadTool()
            result = tool.execute(temp_path)
            assert "Error:" in result or "Permission" in result
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])