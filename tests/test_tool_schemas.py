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


class TestToolSchemas:
    """Test that to_function_schema produces correct output"""
    
    def test_task_tool_schema(self):
        tool = TaskTool()
        schema = tool.to_function_schema()
        
        # Check structure
        assert schema["type"] == "function"
        assert "function" in schema
        assert schema["function"]["name"] == "Task"
        assert "Launch a new agent" in schema["function"]["description"]
        
        # Check parameters
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert params["additionalProperties"] == False
        assert params["$schema"] == "http://json-schema.org/draft-07/schema#"
        
        # Check properties
        props = params["properties"]
        assert "description" in props
        assert props["description"]["type"] == "string"
        assert props["description"]["description"] == "A short (3-5 word) description of the task"
        
        assert "prompt" in props
        assert props["prompt"]["type"] == "string"
        assert props["prompt"]["description"] == "The task for the agent to perform"
        
        assert "subagent_type" in props
        assert props["subagent_type"]["type"] == "string"
        assert props["subagent_type"]["description"] == "The type of specialized agent to use for this task"
        
        # Check required fields
        assert params["required"] == ["description", "prompt", "subagent_type"]
    
    def test_bash_tool_schema(self):
        tool = BashTool()
        schema = tool.to_function_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "Bash"
        assert "bash command" in schema["function"]["description"]
        
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert params["required"] == ["command"]
        
        props = params["properties"]
        assert props["command"]["type"] == "string"
        assert props["timeout"]["type"] == "number"
        assert props["description"]["type"] == "string"
    
    def test_glob_tool_schema(self):
        tool = GlobTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "Glob"
        params = schema["function"]["parameters"]
        assert params["required"] == ["pattern"]
        assert "pattern" in params["properties"]
        assert "path" in params["properties"]
    
    def test_grep_tool_schema(self):
        tool = GrepTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "Grep"
        params = schema["function"]["parameters"]
        assert params["required"] == ["pattern"]
        
        props = params["properties"]
        assert "pattern" in props
        assert "output_mode" in props
        assert props["output_mode"]["enum"] == ["content", "files_with_matches", "count"]
    
    def test_ls_tool_schema(self):
        tool = LSTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "LS"
        params = schema["function"]["parameters"]
        assert params["required"] == ["path"]
        assert "ignore" in params["properties"]
        assert params["properties"]["ignore"]["type"] == "array"
    
    def test_read_tool_schema(self):
        tool = ReadTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "Read"
        params = schema["function"]["parameters"]
        assert params["required"] == ["file_path"]
        assert "offset" in params["properties"]
        assert "limit" in params["properties"]
    
    def test_edit_tool_schema(self):
        tool = EditTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "Edit"
        params = schema["function"]["parameters"]
        assert params["required"] == ["file_path", "old_string", "new_string"]
        assert "replace_all" in params["properties"]
        assert params["properties"]["replace_all"]["type"] == "boolean"
        assert params["properties"]["replace_all"]["default"] == False
    
    def test_multiedit_tool_schema(self):
        tool = MultiEditTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "MultiEdit"
        params = schema["function"]["parameters"]
        assert params["required"] == ["file_path", "edits"]
        
        edits_prop = params["properties"]["edits"]
        assert edits_prop["type"] == "array"
        assert edits_prop["minItems"] == 1
        assert "items" in edits_prop
        
        item_schema = edits_prop["items"]
        assert item_schema["type"] == "object"
        assert item_schema["required"] == ["old_string", "new_string"]
    
    def test_write_tool_schema(self):
        tool = WriteTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "Write"
        params = schema["function"]["parameters"]
        assert params["required"] == ["file_path", "content"]
    
    def test_notebook_read_tool_schema(self):
        tool = NotebookReadTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "NotebookRead"
        params = schema["function"]["parameters"]
        assert params["required"] == ["notebook_path"]
        assert "cell_id" in params["properties"]
    
    def test_notebook_edit_tool_schema(self):
        tool = NotebookEditTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "NotebookEdit"
        params = schema["function"]["parameters"]
        assert params["required"] == ["notebook_path", "new_source"]
        
        props = params["properties"]
        assert props["cell_type"]["enum"] == ["code", "markdown"]
        assert props["edit_mode"]["enum"] == ["replace", "insert", "delete"]
    
    def test_webfetch_tool_schema(self):
        tool = WebFetchTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "WebFetch"
        params = schema["function"]["parameters"]
        assert params["required"] == ["url", "prompt"]
        assert params["properties"]["url"]["format"] == "uri"
    
    def test_todowrite_tool_schema(self):
        tool = TodoWriteTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "TodoWrite"
        params = schema["function"]["parameters"]
        assert params["required"] == ["todos"]
        
        todos_prop = params["properties"]["todos"]
        assert todos_prop["type"] == "array"
        item_props = todos_prop["items"]["properties"]
        assert item_props["status"]["enum"] == ["pending", "in_progress", "completed"]
        assert item_props["priority"]["enum"] == ["high", "medium", "low"]
        assert todos_prop["items"]["required"] == ["content", "status", "priority", "id"]
    
    def test_websearch_tool_schema(self):
        tool = WebSearchTool()
        schema = tool.to_function_schema()
        
        assert schema["function"]["name"] == "WebSearch"
        params = schema["function"]["parameters"]
        assert params["required"] == ["query"]
        assert params["properties"]["query"]["minLength"] == 2
        assert "allowed_domains" in params["properties"]
        assert "blocked_domains" in params["properties"]


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