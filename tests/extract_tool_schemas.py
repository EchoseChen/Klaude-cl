#!/usr/bin/env python3
"""
Extract tool schemas from tool_defs.json for comparison
"""

import json
import os

def extract_tool_schemas():
    # Read the tool_defs.json file
    tool_defs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  'debug', 'traces', 'tool_defs.json')
    
    with open(tool_defs_path, 'r') as f:
        data = json.load(f)
    
    # Extract just the tools array
    tools = data.get('tools', [])
    
    # Create a dictionary mapping tool names to their schemas
    tool_schemas = {}
    for tool in tools:
        if tool['type'] == 'function' and 'function' in tool:
            name = tool['function']['name']
            tool_schemas[name] = tool
    
    # Save to a separate file for easier testing
    output_path = os.path.join(os.path.dirname(__file__), 'expected_tool_schemas.json')
    with open(output_path, 'w') as f:
        json.dump(tool_schemas, f, indent=2)
    
    print(f"Extracted {len(tool_schemas)} tool schemas to {output_path}")
    return tool_schemas

if __name__ == "__main__":
    extract_tool_schemas()