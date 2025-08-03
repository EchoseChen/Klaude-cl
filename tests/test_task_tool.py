#!/usr/bin/env python3
"""
File: test_task_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for TaskTool implementation

This file is part of the klaude project.
"""

import pytest
import json
import sys
import os

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import TaskTool
from test_helpers import assert_schema_matches_expected


class TestTaskTool:
    """Test TaskTool implementation"""
    
    def test_task_tool_creation(self):
        tool = TaskTool()
        assert tool.name == "Task"
        assert "Launch a new agent" in tool.description
        
    def test_task_tool_with_custom_agents(self):
        """Test that custom agents are loaded and included in description"""
        tool = TaskTool()
        
        # Check if any custom agents were loaded from .claude/agents
        # The code-reviewer agent should be loaded if the test is run from project root
        if tool.custom_agents:
            assert "general-purpose" in tool.description
            # Check that custom agents are in the description
            for agent_name, agent_config in tool.custom_agents.items():
                assert agent_name in tool.description
                assert agent_config.description in tool.description
        
    def test_task_tool_parameters(self):
        tool = TaskTool()
        schema = tool.get_parameters_schema()
        assert "description" in schema["properties"]
        assert "prompt" in schema["properties"]
        assert "subagent_type" in schema["properties"]
        assert schema["required"] == ["description", "prompt", "subagent_type"]
    
    def test_task_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = TaskTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "Task")
    
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
    
    def test_task_tool_execution_with_trace_input(self):
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
        assert "general-purpose" in parsed["text"]
    
    def test_task_tool_with_custom_agent_execution(self):
        """Test executing a custom agent"""
        tool = TaskTool()
        
        # Only run this test if custom agents are loaded
        if "code-reviewer" in tool.custom_agents:
            result = tool.execute(
                description="Review the code",
                prompt="Review the following function for best practices:\n\ndef add(a, b):\n    return a + b",
                subagent_type="code-reviewer"
            )
            parsed = json.loads(result)
            assert parsed["type"] == "text"
            assert "code-reviewer" in parsed["text"].lower()
            assert "Review the code" in parsed["text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])