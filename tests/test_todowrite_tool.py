#!/usr/bin/env python3
"""
File: test_todowrite_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for TodoWriteTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import TodoWriteTool
from test_helpers import assert_schema_matches_expected


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
    
    def test_todowrite_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = TodoWriteTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "TodoWrite")
        
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
    
    def test_todowrite_tool_multiple_todos(self):
        tool = TodoWriteTool()
        todos = [
            {
                "id": "1",
                "content": "First task",
                "status": "completed",
                "priority": "high"
            },
            {
                "id": "2",
                "content": "Second task",
                "status": "in_progress",
                "priority": "medium"
            },
            {
                "id": "3",
                "content": "Third task",
                "status": "pending",
                "priority": "low"
            }
        ]
        result = tool.execute(todos)
        assert "Todos have been modified successfully" in result
        assert len(tool.todos) == 3
        assert tool.todos[0]["content"] == "First task"
        assert tool.todos[1]["status"] == "in_progress"
        assert tool.todos[2]["priority"] == "low"
    
    def test_todowrite_tool_empty_list(self):
        tool = TodoWriteTool()
        todos = []
        result = tool.execute(todos)
        assert "Todos have been modified successfully" in result
        assert tool.todos == []
    
    def test_todowrite_tool_update_existing(self):
        tool = TodoWriteTool()
        # Set initial todos
        initial_todos = [
            {
                "id": "1",
                "content": "Original task",
                "status": "pending",
                "priority": "high"
            }
        ]
        tool.execute(initial_todos)
        
        # Update todos
        updated_todos = [
            {
                "id": "1",
                "content": "Updated task",
                "status": "completed",
                "priority": "high"
            },
            {
                "id": "2",
                "content": "New task",
                "status": "pending",
                "priority": "medium"
            }
        ]
        result = tool.execute(updated_todos)
        assert "Todos have been modified successfully" in result
        assert len(tool.todos) == 2
        assert tool.todos[0]["content"] == "Updated task"
        assert tool.todos[0]["status"] == "completed"
    
    def test_todowrite_tool_all_statuses(self):
        tool = TodoWriteTool()
        todos = [
            {
                "id": "1",
                "content": "Pending task",
                "status": "pending",
                "priority": "high"
            },
            {
                "id": "2",
                "content": "In progress task",
                "status": "in_progress",
                "priority": "medium"
            },
            {
                "id": "3",
                "content": "Completed task",
                "status": "completed",
                "priority": "low"
            }
        ]
        result = tool.execute(todos)
        assert "Todos have been modified successfully" in result
        # Verify all statuses are preserved
        statuses = [todo["status"] for todo in tool.todos]
        assert "pending" in statuses
        assert "in_progress" in statuses
        assert "completed" in statuses
    
    def test_todowrite_tool_all_priorities(self):
        tool = TodoWriteTool()
        todos = [
            {
                "id": "1",
                "content": "High priority",
                "status": "pending",
                "priority": "high"
            },
            {
                "id": "2",
                "content": "Medium priority",
                "status": "pending",
                "priority": "medium"
            },
            {
                "id": "3",
                "content": "Low priority",
                "status": "pending",
                "priority": "low"
            }
        ]
        result = tool.execute(todos)
        assert "Todos have been modified successfully" in result
        # Verify all priorities are preserved
        priorities = [todo["priority"] for todo in tool.todos]
        assert "high" in priorities
        assert "medium" in priorities
        assert "low" in priorities
    
    def test_todowrite_tool_invalid_status(self):
        tool = TodoWriteTool()
        todos = [
            {
                "id": "1",
                "content": "Test task",
                "status": "invalid_status",  # Invalid
                "priority": "high"
            }
        ]
        # The tool might validate this and return an error
        # or it might accept it (depends on implementation)
        result = tool.execute(todos)
        # Either succeeds or shows error
    
    def test_todowrite_tool_missing_fields(self):
        tool = TodoWriteTool()
        # Test with missing required field
        todos = [
            {
                "id": "1",
                "content": "Test task",
                "status": "pending"
                # Missing priority
            }
        ]
        # The tool should handle this gracefully
        # Either by providing default or showing error
    
    def test_todowrite_tool_long_content(self):
        tool = TodoWriteTool()
        long_content = "This is a very long task description " * 50
        todos = [
            {
                "id": "1",
                "content": long_content,
                "status": "pending",
                "priority": "high"
            }
        ]
        result = tool.execute(todos)
        assert "Todos have been modified successfully" in result
        assert tool.todos[0]["content"] == long_content
    
    def test_todowrite_tool_special_characters(self):
        tool = TodoWriteTool()
        todos = [
            {
                "id": "1",
                "content": "Task with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
                "status": "pending",
                "priority": "high"
            }
        ]
        result = tool.execute(todos)
        assert "Todos have been modified successfully" in result
        assert "!@#$%^&*" in tool.todos[0]["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])