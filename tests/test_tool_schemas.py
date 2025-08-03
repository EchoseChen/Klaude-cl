#!/usr/bin/env python3
"""
File: test_tool_schemas.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Test that Tool.to_function_schema produces correct output matching tool_defs.json

This file is part of the klaude project.
"""

import pytest
import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import (
    TaskTool, BashTool, GlobTool, GrepTool, LSTool, ReadTool,
    EditTool, MultiEditTool, WriteTool, NotebookReadTool, 
    NotebookEditTool, WebFetchTool, TodoWriteTool, WebSearchTool
)
from test_helpers import assert_schema_matches_expected


class TestToolSchemas:
    """Test that to_function_schema produces correct output"""
    
    def test_task_tool_schema(self):
        tool = TaskTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Task")
    
    def test_bash_tool_schema(self):
        tool = BashTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Bash")
    
    def test_glob_tool_schema(self):
        tool = GlobTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Glob")
    
    def test_grep_tool_schema(self):
        tool = GrepTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Grep")
    
    def test_ls_tool_schema(self):
        tool = LSTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "LS")
    
    def test_read_tool_schema(self):
        tool = ReadTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Read")
    
    def test_edit_tool_schema(self):
        tool = EditTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Edit")
    
    def test_multiedit_tool_schema(self):
        tool = MultiEditTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "MultiEdit")
    
    def test_write_tool_schema(self):
        tool = WriteTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Write")
    
    def test_notebook_read_tool_schema(self):
        tool = NotebookReadTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "NotebookRead")
    
    def test_notebook_edit_tool_schema(self):
        tool = NotebookEditTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "NotebookEdit")
    
    def test_webfetch_tool_schema(self):
        tool = WebFetchTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "WebFetch")
    
    def test_todowrite_tool_schema(self):
        tool = TodoWriteTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "TodoWrite")
    
    def test_websearch_tool_schema(self):
        tool = WebSearchTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "WebSearch")


def test_all_tools_produce_valid_schemas():
    """Test that all tools produce valid schemas"""
    tools = [
        TaskTool(), BashTool(), GlobTool(), GrepTool(), LSTool(),
        ReadTool(), EditTool(), MultiEditTool(), WriteTool(),
        NotebookReadTool(), NotebookEditTool(), WebFetchTool(),
        TodoWriteTool(), WebSearchTool()
    ]
    
    for tool in tools:
        schema = tool.to_function_schema()
        
        # Basic structure validation
        assert schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]
        
        # Parameters validation
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "$schema" in params
        assert "properties" in params
        assert "required" in params
        assert "additionalProperties" in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])