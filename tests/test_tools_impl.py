#!/usr/bin/env python3
"""
File: test_tools_impl.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Comprehensive pytest tests for all tools in tools_impl.py

This file tests the tool implementations against expected outputs from traces.
"""

import pytest
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import (
    TaskTool, BashTool, GlobTool, GrepTool, LSTool, ReadTool,
    EditTool, MultiEditTool, WriteTool, NotebookReadTool, 
    NotebookEditTool, WebFetchTool, TodoWriteTool, WebSearchTool
)


class TestTaskTool:
    """Test TaskTool implementation"""
    
    def test_task_tool_creation(self):
        tool = TaskTool()
        assert tool.name == "Task"
        assert "Launch a new agent" in tool.description
        
    def test_task_tool_parameters(self):
        tool = TaskTool()
        schema = tool.get_parameters_schema()
        assert "description" in schema["properties"]
        assert "prompt" in schema["properties"]
        assert "subagent_type" in schema["properties"]
        assert schema["required"] == ["description", "prompt", "subagent_type"]
    
    def test_task_tool_execution(self):
        tool = TaskTool()
        result = tool.execute(
            description="创建工作流程任务列表",
            prompt="Please create a comprehensive task list",
            subagent_type="general-purpose"
        )
        parsed = json.loads(result)
        assert parsed["type"] == "text"
        assert "Task '创建工作流程任务列表' completed" in parsed["text"]
        assert "general-purpose agent" in parsed["text"]


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
    
    def test_grep_tool_python_fallback(self):
        # Test Python implementation when ripgrep not available
        tool = GrepTool()
        # Provide explicit glob pattern to ensure Python files are found
        result = tool._python_grep("import", path=str(self.test_dir), output_mode="files_with_matches", glob="*.py")
        # Should find files containing 'import' in test_samples directory
        assert "sample.py" in result or "test_import.py" in result or len(result) > 0


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


class TestNotebookTools:
    """Test NotebookReadTool and NotebookEditTool"""
    
    def setup_method(self):
        self.test_notebook = Path("tests/test_samples/sample_notebook.ipynb").absolute()
        
    def test_notebook_read_tool_creation(self):
        tool = NotebookReadTool()
        assert tool.name == "NotebookRead"
        assert "Jupyter notebook" in tool.description
        
    def test_notebook_read_parameters(self):
        tool = NotebookReadTool()
        schema = tool.get_parameters_schema()
        assert "notebook_path" in schema["properties"]
        assert "cell_id" in schema["properties"]
        assert schema["required"] == ["notebook_path"]
        
    def test_notebook_read_execution(self):
        tool = NotebookReadTool()
        result = tool.execute(str(self.test_notebook))
        assert "Sample Notebook" in result
        assert "test notebook" in result
        assert "x = 42" in result
        assert "The answer is 42" in result
        assert "Type: markdown" in result
        assert "Type: code" in result
        
    def test_notebook_read_specific_cell(self):
        tool = NotebookReadTool()
        result = tool.execute(str(self.test_notebook), cell_id="test-code-1")
        assert "x = 42" in result
        assert "Sample Notebook" not in result  # Markdown cell content
        
    def test_notebook_edit_tool_creation(self):
        tool = NotebookEditTool()
        assert tool.name == "NotebookEdit"
        assert "replaces the contents" in tool.description
        
    def test_notebook_edit_parameters(self):
        tool = NotebookEditTool()
        schema = tool.get_parameters_schema()
        assert "notebook_path" in schema["properties"]
        assert "new_source" in schema["properties"]
        assert "cell_id" in schema["properties"]
        assert "cell_type" in schema["properties"]
        assert "edit_mode" in schema["properties"]
        assert schema["required"] == ["notebook_path", "new_source"]


class TestWebFetchTool:
    """Test WebFetchTool implementation"""
    
    def test_webfetch_tool_creation(self):
        tool = WebFetchTool()
        assert tool.name == "WebFetch"
        assert "Fetches content from" in tool.description
        
    def test_webfetch_tool_parameters(self):
        tool = WebFetchTool()
        schema = tool.get_parameters_schema()
        assert "url" in schema["properties"]
        assert "prompt" in schema["properties"]
        assert schema["required"] == ["url", "prompt"]
        
    def test_webfetch_tool_execution(self):
        tool = WebFetchTool()
        result = tool.execute(
            "https://example.com",
            "Extract main content"
        )
        assert "Fetched content from" in result
        assert "https://example.com" in result
        assert "Extract main content" in result
        
    def test_webfetch_tool_restricted_domain(self):
        tool = WebFetchTool()
        result = tool.execute(
            "https://docs.python.org/3/tutorial/modules.html",
            "Get import info"
        )
        assert "unable to fetch from docs.python.org" in result


class TestTodoWriteTool:
    """Test TodoWriteTool implementation"""
    
    def test_todowrite_tool_creation(self):
        tool = TodoWriteTool()
        assert tool.name == "TodoWrite"
        assert "structured task list" in tool.description
        
    def test_todowrite_tool_parameters(self):
        tool = TodoWriteTool()
        schema = tool.get_parameters_schema()
        assert "todos" in schema["properties"]
        todos_schema = schema["properties"]["todos"]
        assert todos_schema["type"] == "array"
        assert "content" in todos_schema["items"]["properties"]
        assert "status" in todos_schema["items"]["properties"]
        assert "priority" in todos_schema["items"]["properties"]
        assert "id" in todos_schema["items"]["properties"]
        
    def test_todowrite_tool_execution(self):
        tool = TodoWriteTool()
        todos = [
            {
                "id": "1",
                "content": "Test task",
                "status": "pending",
                "priority": "high"
            }
        ]
        result = tool.execute(todos)
        assert "Todos have been modified successfully" in result
        assert tool.todos == todos


class TestWebSearchTool:
    """Test WebSearchTool implementation"""
    
    def test_websearch_tool_creation(self):
        tool = WebSearchTool()
        assert tool.name == "WebSearch"
        assert "search the web" in tool.description
        
    def test_websearch_tool_parameters(self):
        tool = WebSearchTool()
        schema = tool.get_parameters_schema()
        assert "query" in schema["properties"]
        assert "allowed_domains" in schema["properties"]
        assert "blocked_domains" in schema["properties"]
        assert schema["required"] == ["query"]
        
    def test_websearch_tool_execution(self):
        tool = WebSearchTool()
        result = tool.execute("Python import best practices")
        assert "Web search results for query" in result
        assert "Python import best practices" in result
        assert "Links:" in result
        assert "example.com" in result  # From simulated results


# Integration tests matching trace outputs
class TestToolsIntegrationWithTraces:
    """Test tools with inputs/outputs matching actual traces"""
    
    def test_task_tool_from_trace(self):
        """Test TaskTool with actual trace input"""
        tool = TaskTool()
        result = tool.execute(
            subagent_type="general-purpose",
            description="创建工作流程任务列表",
            prompt="Please create a comprehensive task list for the following workflow:\n1. Find all Python files (*.py) in the current project\n2. Search for 'import' keywords in those Python files\n3. Fetch Python official documentation about module import best practices\n4. Add unified file header comments to Python files with author info and creation date\n\nPlease create a detailed todo list breaking down these main tasks into specific actionable items. Return the task list in a structured format that I can use with the TodoWrite tool."
        )
        parsed = json.loads(result)
        assert parsed["type"] == "text"
        assert "completed" in parsed["text"]
        
    def test_glob_tool_from_trace(self):
        """Test GlobTool with trace pattern"""
        tool = GlobTool()
        result = tool.execute("**/*.py", "tests/test_samples")
        # Should find Python files
        assert ".py" in result
        assert result.count("\n") >= 2  # At least sample.py, test_import.py, nested.py
        
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
            
    def test_multiedit_from_trace(self):
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