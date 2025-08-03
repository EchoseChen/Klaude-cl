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
    
    # Deep comparison
    assert actual_schema == expected_schema, (
        f"Schema for {tool_name} does not match expected.\n"
        f"Actual: {json.dumps(actual_schema, indent=2)}\n"
        f"Expected: {json.dumps(expected_schema, indent=2)}"
    )