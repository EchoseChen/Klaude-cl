#!/usr/bin/env python3
"""
File: tool_base.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Base classes and infrastructure for Claude Code tools

This file is part of the klaude project.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json


class ToolBase(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for tool parameters"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters"""
        pass
    
    def to_function_schema(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema()
            }
        }


class ToolRegistry:
    """Registry for managing tools"""
    
    def __init__(self):
        self.tools: Dict[str, ToolBase] = {}
    
    def register(self, tool: ToolBase):
        """Register a tool"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[ToolBase]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools"""
        return [tool.to_function_schema() for tool in self.tools.values()]
    
    def execute_tool(self, name: str, **kwargs) -> str:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return tool.execute(**kwargs)


def create_json_schema(schema_type: str = "object", properties: Dict[str, Any] = None, 
                      required: List[str] = None, additional_properties: bool = False) -> Dict[str, Any]:
    """Helper function to create JSON schema"""
    schema = {
        "type": schema_type
    }
    
    if properties:
        schema["properties"] = properties
    
    if required:
        schema["required"] = required
    
    schema["additionalProperties"] = additional_properties
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    
    return schema


def create_property_schema(prop_type: str, description: str, **kwargs) -> Dict[str, Any]:
    """Helper function to create property schema"""
    prop = {
        "type": prop_type,
        "description": description
    }
    prop.update(kwargs)
    return prop