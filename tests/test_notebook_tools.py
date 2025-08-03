#!/usr/bin/env python3
"""
File: test_notebook_tools.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for NotebookReadTool and NotebookEditTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import NotebookReadTool, NotebookEditTool


class TestNotebookReadTool:
    """Test NotebookReadTool implementation"""
    
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
    
    def test_notebook_read_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = NotebookReadTool()
        schema = tool.to_function_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "NotebookRead"
        assert "Jupyter notebook" in schema["function"]["description"]
        
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert params["required"] == ["notebook_path"]
        assert params["additionalProperties"] == False
        assert params["$schema"] == "http://json-schema.org/draft-07/schema#"
        
        props = params["properties"]
        assert props["notebook_path"]["type"] == "string"
        assert props["notebook_path"]["description"] == "The absolute path to the Jupyter notebook file to read (must be absolute, not relative)"
        
        assert props["cell_id"]["type"] == "string"
        assert "ID of a specific cell" in props["cell_id"]["description"]
        
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
    
    def test_notebook_read_nonexistent_file(self):
        tool = NotebookReadTool()
        result = tool.execute("/nonexistent/notebook.ipynb")
        assert "Error:" in result
        assert "does not exist" in result or "No such file" in result
    
    def test_notebook_read_invalid_cell_id(self):
        tool = NotebookReadTool()
        result = tool.execute(str(self.test_notebook), cell_id="nonexistent-id")
        assert "Error:" in result or "not found" in result.lower()
    
    def test_notebook_read_malformed_notebook(self):
        import tempfile
        import json
        
        # Create a malformed notebook file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            f.write("{invalid json}")
            temp_path = f.name
        
        try:
            tool = NotebookReadTool()
            result = tool.execute(temp_path)
            assert "Error:" in result
        finally:
            os.unlink(temp_path)
    
    def test_notebook_read_empty_notebook(self):
        import tempfile
        import json
        
        # Create an empty but valid notebook
        empty_notebook = {
            "cells": [],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 2
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(empty_notebook, f)
            temp_path = f.name
        
        try:
            tool = NotebookReadTool()
            result = tool.execute(temp_path)
            assert "cells" not in result or "empty" in result.lower()
        finally:
            os.unlink(temp_path)


class TestNotebookEditTool:
    """Test NotebookEditTool implementation"""
    
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
    
    def test_notebook_edit_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = NotebookEditTool()
        schema = tool.to_function_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "NotebookEdit"
        assert "replaces the contents" in schema["function"]["description"]
        
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert params["required"] == ["notebook_path", "new_source"]
        assert params["additionalProperties"] == False
        assert params["$schema"] == "http://json-schema.org/draft-07/schema#"
        
        props = params["properties"]
        assert props["notebook_path"]["type"] == "string"
        assert props["new_source"]["type"] == "string"
        assert props["cell_id"]["type"] == "string"
        
        assert props["cell_type"]["type"] == "string"
        assert props["cell_type"]["enum"] == ["code", "markdown"]
        
        assert props["edit_mode"]["type"] == "string"
        assert props["edit_mode"]["enum"] == ["replace", "insert", "delete"]
    
    def test_notebook_edit_replace_mode(self):
        import tempfile
        import json
        
        # Create a test notebook
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {"id": "cell1"},
                    "source": ["print('old')\n"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 2
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook, f)
            temp_path = f.name
        
        try:
            tool = NotebookEditTool()
            result = tool.execute(
                temp_path,
                new_source="print('new')",
                cell_id="cell1",
                edit_mode="replace"
            )
            assert "successfully" in result.lower()
            
            # Verify the change
            with open(temp_path) as f:
                updated = json.load(f)
            assert updated["cells"][0]["source"] == ["print('new')"]
        finally:
            os.unlink(temp_path)
    
    def test_notebook_edit_insert_mode(self):
        import tempfile
        import json
        
        # Create a test notebook
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {"id": "cell1"},
                    "source": ["print('existing')\n"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 2
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook, f)
            temp_path = f.name
        
        try:
            tool = NotebookEditTool()
            result = tool.execute(
                temp_path,
                new_source="# New markdown cell",
                cell_type="markdown",
                edit_mode="insert"
            )
            assert "successfully" in result.lower()
            
            # Verify the insertion
            with open(temp_path) as f:
                updated = json.load(f)
            assert len(updated["cells"]) == 2
        finally:
            os.unlink(temp_path)
    
    def test_notebook_edit_delete_mode(self):
        import tempfile
        import json
        
        # Create a test notebook with multiple cells
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {"id": "cell1"},
                    "source": ["print('cell1')\n"]
                },
                {
                    "cell_type": "code",
                    "metadata": {"id": "cell2"},
                    "source": ["print('cell2')\n"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 2
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook, f)
            temp_path = f.name
        
        try:
            tool = NotebookEditTool()
            result = tool.execute(
                temp_path,
                new_source="",  # Required but not used in delete mode
                cell_id="cell1",
                edit_mode="delete"
            )
            assert "successfully" in result.lower()
            
            # Verify the deletion
            with open(temp_path) as f:
                updated = json.load(f)
            assert len(updated["cells"]) == 1
            assert updated["cells"][0]["source"] == ["print('cell2')\n"]
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])