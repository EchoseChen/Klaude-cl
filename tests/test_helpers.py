#!/usr/bin/env python3
"""
File: test_helpers.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Helper functions for tests

This file is part of the klaude project.
"""

import json
import os
from pathlib import Path


def load_expected_schema(tool_name: str) -> dict:
    """Load expected schema for a tool from expected_tool_schemas.json"""
    schemas_file = Path(__file__).parent / "expected_tool_schemas.json"
    with open(schemas_file, 'r') as f:
        schemas = json.load(f)
    
    if tool_name not in schemas:
        raise ValueError(f"No expected schema found for tool: {tool_name}")
    
    return schemas[tool_name]


def assert_schema_matches_expected(actual_schema: dict, tool_name: str):
    """Assert that actual schema matches expected schema"""
    expected_schema = load_expected_schema(tool_name)
    
    # Special handling for Task tool - only compare from "When using the Task tool" onwards
    if tool_name == "Task":
        # Make a copy to avoid modifying the original
        actual_copy = json.loads(json.dumps(actual_schema))
        expected_copy = json.loads(json.dumps(expected_schema))
        
        # Get the descriptions
        actual_desc = actual_copy["function"]["description"]
        expected_desc = expected_copy["function"]["description"]
        
        # Find the static part that starts with "When using the Task tool"
        static_marker = "When using the Task tool, you must specify a subagent_type parameter"
        
        actual_static_idx = actual_desc.find(static_marker)
        expected_static_idx = expected_desc.find(static_marker)
        
        if actual_static_idx != -1 and expected_static_idx != -1:
            # Compare only the static part
            actual_static = actual_desc[actual_static_idx:]
            expected_static = expected_desc[expected_static_idx:]
            
            # For comparison purposes, replace the description with just the static part
            actual_copy["function"]["description"] = actual_static
            expected_copy["function"]["description"] = expected_static
        else:
            # Fallback to comparing last 3177 characters
            if len(actual_desc) > 3177:
                actual_copy["function"]["description"] = actual_desc[-3177:]
            if len(expected_desc) > 3177:
                expected_copy["function"]["description"] = expected_desc[-3177:]
        
        # Now compare the modified schemas
        assert actual_copy == expected_copy, (
            f"Schema for {tool_name} does not match expected.\n"
            f"Actual (static part of description): {json.dumps(actual_copy, indent=2)}\n"
            f"Expected (static part of description): {json.dumps(expected_copy, indent=2)}"
        )
    else:
        # Deep comparison for other tools
        assert actual_schema == expected_schema, (
            f"Schema for {tool_name} does not match expected.\n"
            f"Actual: {json.dumps(actual_schema, indent=2)}\n"
            f"Expected: {json.dumps(expected_schema, indent=2)}"
        )