#!/usr/bin/env python3
"""
Script to update all test files to use assert_schema_matches_expected
"""

import os
import re

# Mapping of test files to tool names
test_file_mappings = {
    "test_bash_tool.py": "Bash",
    "test_edit_tool.py": "Edit",
    "test_glob_tool.py": "Glob",
    "test_grep_tool.py": "Grep",
    "test_ls_tool.py": "LS",
    "test_multiedit_tool.py": "MultiEdit",
    "test_notebook_tools.py": ["NotebookRead", "NotebookEdit"],
    "test_read_tool.py": "Read",
    "test_task_tool.py": "Task",
    "test_todowrite_tool.py": "TodoWrite",
    "test_webfetch_tool.py": "WebFetch",
    "test_websearch_tool.py": "WebSearch",
    "test_write_tool.py": "Write"
}

def update_imports(content):
    """Add import for assert_schema_matches_expected if not present"""
    if "from test_helpers import assert_schema_matches_expected" not in content:
        # Find the last import line
        import_lines = []
        lines = content.split('\n')
        last_import_idx = -1
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                last_import_idx = i
        
        if last_import_idx >= 0:
            lines.insert(last_import_idx + 1, "from test_helpers import assert_schema_matches_expected")
            content = '\n'.join(lines)
    
    return content

def update_schema_test(content, tool_name):
    """Update schema test method to use assert_schema_matches_expected"""
    # Pattern to find schema test methods
    pattern = r'def test_\w+_schema_format\(self\):\s*"""[^"]*"""\s*tool = \w+\(\)\s*schema = tool\.to_function_schema\(\)\s*(?:.*?(?=def|\Z))'
    
    def replace_schema_test(match):
        # Extract the method signature and docstring
        method_text = match.group(0)
        lines = method_text.split('\n')
        
        # Find where schema = tool.to_function_schema() is
        new_lines = []
        found_schema = False
        for line in lines:
            new_lines.append(line)
            if 'schema = tool.to_function_schema()' in line:
                found_schema = True
                # Add the assertion on the next line
                indent = len(line) - len(line.lstrip())
                new_lines.append(' ' * indent + f'assert_schema_matches_expected(schema, "{tool_name}")')
                # Skip remaining lines until next method or end
                break
        
        if found_schema:
            return '\n'.join(new_lines)
        return method_text
    
    content = re.sub(pattern, replace_schema_test, content, flags=re.DOTALL)
    return content

def process_file(filepath, tool_names):
    """Process a single test file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Update imports
    content = update_imports(content)
    
    # Update schema tests
    if isinstance(tool_names, list):
        for tool_name in tool_names:
            content = update_schema_test(content, tool_name)
    else:
        content = update_schema_test(content, tool_names)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Updated {filepath}")

def main():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename, tool_names in test_file_mappings.items():
        filepath = os.path.join(test_dir, filename)
        if os.path.exists(filepath):
            process_file(filepath, tool_names)

if __name__ == "__main__":
    main()