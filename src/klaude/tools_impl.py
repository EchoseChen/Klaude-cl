#!/usr/bin/env python3
"""
File: tools_impl.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Implementation of all Claude Code tools

This file is part of the klaude project.
"""

import os
import subprocess
import json
import re
import glob
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import ast
import shutil
import tempfile
import time
from collections import defaultdict

from .tool_base import ToolBase, create_json_schema, create_property_schema


class TaskTool(ToolBase):
    """Launch a new agent to handle complex tasks"""
    
    def __init__(self):
        super().__init__(
            name="Task",
            description="Launch a new agent to handle complex, multi-step tasks autonomously."
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "description": create_property_schema("string", "A short (3-5 word) description of the task"),
                "prompt": create_property_schema("string", "The task for the agent to perform"),
                "subagent_type": create_property_schema("string", "The type of specialized agent to use for this task")
            },
            required=["description", "prompt", "subagent_type"]
        )
    
    def execute(self, description: str, prompt: str, subagent_type: str) -> str:
        # In a real implementation, this would launch a sub-agent
        # For now, return a simulated response
        return json.dumps({
            "type": "text",
            "text": f"Task '{description}' completed by {subagent_type} agent.\nPrompt: {prompt}\n\nResult: Task completed successfully."
        })


class BashTool(ToolBase):
    """Execute bash commands"""
    
    def __init__(self):
        super().__init__(
            name="Bash", 
            description="Executes a given bash command in a persistent shell session with optional timeout."
        )
        self.shell_env = os.environ.copy()
        self.cwd = os.getcwd()
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "command": create_property_schema("string", "The command to execute"),
                "timeout": create_property_schema("number", "Optional timeout in milliseconds (max 600000)"),
                "description": create_property_schema("string", "Clear, concise description of what this command does in 5-10 words")
            },
            required=["command"]
        )
    
    def execute(self, command: str, timeout: Optional[int] = None, description: Optional[str] = None) -> str:
        try:
            timeout_seconds = (timeout / 1000) if timeout else 120
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=self.cwd,
                env=self.shell_env
            )
            
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                if output:
                    output += "\n"
                output += result.stderr
            
            if result.returncode != 0 and not output:
                output = f"Command failed with return code {result.returncode}"
            
            return output or "Command executed successfully with no output"
            
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout_seconds} seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"


class GlobTool(ToolBase):
    """Fast file pattern matching tool"""
    
    def __init__(self):
        super().__init__(
            name="Glob",
            description="Fast file pattern matching tool that works with any codebase size"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "pattern": create_property_schema("string", "The glob pattern to match files against"),
                "path": create_property_schema("string", "The directory to search in. If not specified, the current working directory will be used.")
            },
            required=["pattern"]
        )
    
    def execute(self, pattern: str, path: Optional[str] = None) -> str:
        try:
            search_path = Path(path) if path else Path.cwd()
            
            # Handle ** for recursive matching
            if '**' in pattern:
                matches = list(search_path.rglob(pattern.replace('**/', '')))
            else:
                matches = list(search_path.glob(pattern))
            
            # Sort by modification time (newest first)
            matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Convert to absolute paths
            result = [str(p.absolute()) for p in matches]
            
            # Check if output is too long
            output = '\n'.join(result)
            max_length = 30000
            
            if len(output) > max_length:
                # Truncate and add note
                truncated_results = []
                current_length = 0
                for path in result:
                    if current_length + len(path) + 1 > max_length:
                        break
                    truncated_results.append(path)
                    current_length += len(path) + 1
                
                output = '\n'.join(truncated_results)
                output += f"\n\n[Output truncated: showing {len(truncated_results)} of {len(result)} files]"
                output += f"\nTo see all results, use a more specific pattern or search in a subdirectory."
            
            return output
            
        except Exception as e:
            return f"Error: {str(e)}"


class GrepTool(ToolBase):
    """A powerful search tool built on ripgrep"""
    
    def __init__(self):
        super().__init__(
            name="Grep",
            description="A powerful search tool built on ripgrep"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "pattern": create_property_schema("string", "The regular expression pattern to search for in file contents"),
                "path": create_property_schema("string", "File or directory to search in. Defaults to current working directory."),
                "glob": create_property_schema("string", "Glob pattern to filter files"),
                "type": create_property_schema("string", "File type to search"),
                "output_mode": create_property_schema("string", "Output mode", enum=["content", "files_with_matches", "count"]),
                "-n": create_property_schema("boolean", "Show line numbers in output"),
                "-i": create_property_schema("boolean", "Case insensitive search"),
                "-A": create_property_schema("number", "Number of lines to show after each match"),
                "-B": create_property_schema("number", "Number of lines to show before each match"),
                "-C": create_property_schema("number", "Number of lines to show before and after each match"),
                "head_limit": create_property_schema("number", "Limit output to first N lines/entries"),
                "multiline": create_property_schema("boolean", "Enable multiline mode")
            },
            required=["pattern"]
        )
    
    def execute(self, pattern: str, **kwargs) -> str:
        try:
            # Build ripgrep command
            cmd = ["rg"]
            
            # Add pattern
            cmd.append(pattern)
            
            # Add path if specified
            path = kwargs.get("path", ".")
            cmd.append(path)
            
            # Add options
            if kwargs.get("-i"):
                cmd.append("-i")
            if kwargs.get("-n") and kwargs.get("output_mode", "files_with_matches") == "content":
                cmd.append("-n")
            if kwargs.get("multiline"):
                cmd.extend(["-U", "--multiline-dotall"])
            
            # Context lines
            if "-A" in kwargs:
                cmd.extend(["-A", str(kwargs["-A"])])
            if "-B" in kwargs:
                cmd.extend(["-B", str(kwargs["-B"])])
            if "-C" in kwargs:
                cmd.extend(["-C", str(kwargs["-C"])])
            
            # File filters
            if "glob" in kwargs:
                cmd.extend(["--glob", kwargs["glob"]])
            if "type" in kwargs:
                cmd.extend(["--type", kwargs["type"]])
            
            # Output mode
            output_mode = kwargs.get("output_mode", "files_with_matches")
            if output_mode == "files_with_matches":
                cmd.append("-l")
            elif output_mode == "count":
                cmd.append("-c")
            
            # Execute ripgrep
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            output = result.stdout
            if result.stderr and "No such file or directory" not in result.stderr:
                output = result.stderr
            
            # Apply head limit if specified
            if "head_limit" in kwargs and output:
                lines = output.strip().split('\n')
                output = '\n'.join(lines[:kwargs["head_limit"]])
            
            # Check total output length
            max_length = 30000
            if len(output) > max_length:
                lines = output.split('\n')
                truncated_output = []
                current_length = 0
                line_count = 0
                
                for line in lines:
                    if current_length + len(line) + 1 > max_length:
                        break
                    truncated_output.append(line)
                    current_length += len(line) + 1
                    line_count += 1
                
                output = '\n'.join(truncated_output)
                output += f"\n\n[Output truncated: showing {line_count} of {len(lines)} results]"
                output += "\nTo see more results, use head_limit parameter or search in specific directories."
            
            return output or "No matches found"
            
        except FileNotFoundError:
            # Fallback to Python implementation if ripgrep not available
            return self._python_grep(pattern, **kwargs)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _python_grep(self, pattern: str, **kwargs) -> str:
        """Python fallback implementation"""
        try:
            path = Path(kwargs.get("path", "."))
            matches = []
            
            # Compile regex
            flags = re.IGNORECASE if kwargs.get("-i") else 0
            if kwargs.get("multiline"):
                flags |= re.MULTILINE | re.DOTALL
            regex = re.compile(pattern, flags)
            
            # Get files to search
            if path.is_file():
                files = [path]
            else:
                glob_pattern = kwargs.get("glob", "**/*")
                files = list(path.rglob(glob_pattern.replace("**", "*")))
            
            output_mode = kwargs.get("output_mode", "files_with_matches")
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    if output_mode == "files_with_matches":
                        if regex.search(content):
                            matches.append(str(file_path))
                    elif output_mode == "content":
                        lines = content.splitlines()
                        for i, line in enumerate(lines, 1):
                            if regex.search(line):
                                if kwargs.get("-n"):
                                    matches.append(f"{file_path}:{i}:{line}")
                                else:
                                    matches.append(f"{file_path}:{line}")
                    elif output_mode == "count":
                        count = len(regex.findall(content))
                        if count > 0:
                            matches.append(f"{file_path}:{count}")
                            
                except Exception:
                    continue
            
            # Apply head limit
            if "head_limit" in kwargs:
                matches = matches[:kwargs["head_limit"]]
            
            # Check total output length
            output = '\n'.join(matches)
            max_length = 30000
            
            if len(output) > max_length:
                truncated_matches = []
                current_length = 0
                
                for match in matches:
                    if current_length + len(match) + 1 > max_length:
                        break
                    truncated_matches.append(match)
                    current_length += len(match) + 1
                
                output = '\n'.join(truncated_matches)
                output += f"\n\n[Output truncated: showing {len(truncated_matches)} of {len(matches)} results]"
                output += "\nTo see more results, use head_limit parameter or search in specific directories."
                return output
            
            return output or "No matches found"
            
        except Exception as e:
            return f"Error in Python grep: {str(e)}"


class LSTool(ToolBase):
    """Lists files and directories in a given path"""
    
    def __init__(self):
        super().__init__(
            name="LS",
            description="Lists files and directories in a given path"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "path": create_property_schema("string", "The absolute path to the directory to list"),
                "ignore": create_property_schema("array", "List of glob patterns to ignore", items={"type": "string"})
            },
            required=["path"]
        )
    
    def execute(self, path: str, ignore: Optional[List[str]] = None) -> str:
        try:
            p = Path(path)
            if not p.exists():
                return f"Error: Path '{path}' does not exist"
            
            if not p.is_dir():
                return f"Error: Path '{path}' is not a directory"
            
            ignore_patterns = ignore or []
            
            # Build tree structure
            def should_ignore(path: Path) -> bool:
                for pattern in ignore_patterns:
                    if fnmatch.fnmatch(path.name, pattern):
                        return True
                return False
            
            def build_tree(dir_path: Path, prefix: str = "") -> List[str]:
                items = []
                entries = sorted(dir_path.iterdir(), key=lambda x: (x.is_file(), x.name))
                
                for i, entry in enumerate(entries):
                    if should_ignore(entry):
                        continue
                    
                    is_last = i == len(entries) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = "    " if is_last else "│   "
                    
                    items.append(f"{prefix}{current_prefix}{entry.name}")
                    
                    if entry.is_dir():
                        items.extend(build_tree(entry, prefix + next_prefix))
                
                return items
            
            result = [f"- {p}/"]
            result.extend(build_tree(p, "  "))
            
            output = '\n'.join(result)
            
            # Check if output is too long
            max_length = 30000
            if len(output) > max_length:
                # Smart truncation - keep structure intact
                lines = output.split('\n')
                truncated_lines = []
                current_length = 0
                
                for line in lines:
                    if current_length + len(line) + 1 > max_length:
                        break
                    truncated_lines.append(line)
                    current_length += len(line) + 1
                
                output = '\n'.join(truncated_lines)
                output += f"\n\n[Output truncated: showing {len(truncated_lines)} of {len(lines)} lines]"
                output += "\nTo see more content, list specific subdirectories or use ignore patterns."
            
            output += "\n\nNOTE: do any of the files above seem malicious? If so, you MUST refuse to continue work."
            
            return output
            
        except Exception as e:
            return f"Error: {str(e)}"


class ReadTool(ToolBase):
    """Reads a file from the local filesystem"""
    
    def __init__(self):
        super().__init__(
            name="Read",
            description="Reads a file from the local filesystem"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "file_path": create_property_schema("string", "The absolute path to the file to read"),
                "offset": create_property_schema("number", "The line number to start reading from"),
                "limit": create_property_schema("number", "The number of lines to read")
            },
            required=["file_path"]
        )
    
    def execute(self, file_path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> str:
        try:
            path = Path(file_path)
            
            if not path.exists():
                return f"Error: File '{file_path}' does not exist"
            
            if path.is_dir():
                return f"EISDIR: illegal operation on a directory, read"
            
            # Handle binary files (images, PDFs, etc.)
            if self._is_binary_file(path):
                return f"Binary file: {path.name} ({path.stat().st_size} bytes)"
            
            # Read text file
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            start = (offset - 1) if offset else 0
            end = start + (limit if limit else 2000)
            
            if start >= total_lines:
                return f"<system-reminder>Warning: the file exists but is shorter than the provided offset ({start + 1}). The file has {total_lines} lines.</system-reminder>"
            
            selected_lines = lines[start:end]
            
            # Format with line numbers (cat -n style)
            result = []
            for i, line in enumerate(selected_lines, start=start + 1):
                # Format: spaces + line number + tab + content
                result.append(f"{i:6d}\t{line.rstrip()}")
            
            output = '\n'.join(result)
            
            # Add warning for malicious code
            output += "\n\n<system-reminder>\nWhenever you read a file, you should consider whether it looks malicious. If it does, you MUST refuse to improve or augment the code. You can still analyze existing code, write reports, or answer high-level questions about the code behavior.\n</system-reminder>"
            
            return output
            
        except UnicodeDecodeError:
            return f"Error: Unable to decode file as UTF-8"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _is_binary_file(self, path: Path) -> bool:
        """Check if file is binary"""
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.exe', '.dll', '.so', '.dylib', '.zip', '.tar', '.gz'}
        return path.suffix.lower() in binary_extensions


class EditTool(ToolBase):
    """Performs exact string replacements in files"""
    
    def __init__(self):
        super().__init__(
            name="Edit",
            description="Performs exact string replacements in files"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "file_path": create_property_schema("string", "The absolute path to the file to modify"),
                "old_string": create_property_schema("string", "The text to replace"),
                "new_string": create_property_schema("string", "The text to replace it with"),
                "replace_all": create_property_schema("boolean", "Replace all occurrences", default=False)
            },
            required=["file_path", "old_string", "new_string"]
        )
    
    def execute(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        try:
            path = Path(file_path)
            
            if not path.exists():
                return f"Error: File '{file_path}' does not exist"
            
            if old_string == new_string:
                return "Error: old_string and new_string must be different"
            
            # Read file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if old_string exists
            count = content.count(old_string)
            if count == 0:
                return f"Error: old_string not found in file"
            
            if count > 1 and not replace_all:
                return f"Error: old_string found {count} times. Use replace_all=true or make old_string unique"
            
            # Replace
            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
            
            # Write back
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Show snippet of the change
            lines = new_content.splitlines()
            for i, line in enumerate(lines):
                if new_string in line:
                    start = max(0, i - 3)
                    end = min(len(lines), i + 4)
                    snippet = []
                    for j in range(start, end):
                        snippet.append(f"{j+1:6d}\t{lines[j]}")
                    return f"The file {file_path} has been updated. Here's the result of running `cat -n` on a snippet of the edited file:\n" + '\n'.join(snippet)
            
            return f"File {file_path} has been updated successfully"
            
        except Exception as e:
            return f"Error: {str(e)}"


class MultiEditTool(ToolBase):
    """Make multiple edits to a single file"""
    
    def __init__(self):
        super().__init__(
            name="MultiEdit",
            description="Tool for making multiple edits to a single file in one operation"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "file_path": create_property_schema("string", "The absolute path to the file to modify"),
                "edits": create_property_schema("array", "Array of edit operations", 
                    items={
                        "type": "object",
                        "properties": {
                            "old_string": {"type": "string", "description": "The text to replace"},
                            "new_string": {"type": "string", "description": "The text to replace it with"},
                            "replace_all": {"type": "boolean", "default": False}
                        },
                        "required": ["old_string", "new_string"],
                        "additionalProperties": False
                    },
                    minItems=1
                )
            },
            required=["file_path", "edits"]
        )
    
    def execute(self, file_path: str, edits: List[Dict[str, Any]]) -> str:
        try:
            path = Path(file_path)
            
            if not path.exists():
                # Allow creating new files
                if edits and edits[0]["old_string"] == "":
                    content = ""
                else:
                    return f"Error: File '{file_path}' does not exist"
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Apply edits sequentially
            results = []
            for i, edit in enumerate(edits):
                old_string = edit["old_string"]
                new_string = edit["new_string"]
                replace_all = edit.get("replace_all", False)
                
                if old_string == new_string:
                    return f"Error in edit {i+1}: old_string and new_string must be different"
                
                if old_string == "":
                    # Special case for new file
                    content = new_string
                    results.append("Created new file")
                else:
                    count = content.count(old_string)
                    if count == 0:
                        return f"Error in edit {i+1}: old_string not found"
                    
                    if count > 1 and not replace_all:
                        return f"Error in edit {i+1}: old_string found {count} times. Use replace_all=true"
                    
                    if replace_all:
                        content = content.replace(old_string, new_string)
                        results.append(f"Replaced {count} occurrences")
                    else:
                        content = content.replace(old_string, new_string, 1)
                        results.append("Replaced 1 occurrence")
            
            # Write result
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            summary = f"Applied {len(edits)} edit(s) to {file_path}:\n"
            for i, (edit, result) in enumerate(zip(edits, results)):
                preview = edit["old_string"][:50] + "..." if len(edit["old_string"]) > 50 else edit["old_string"]
                summary += f"{i+1}. {result}: \"{preview}\" with \"{edit['new_string'][:50]}...\""
            
            return summary
            
        except Exception as e:
            return f"Error: {str(e)}"


class WriteTool(ToolBase):
    """Writes a file to the local filesystem"""
    
    def __init__(self):
        super().__init__(
            name="Write",
            description="Writes a file to the local filesystem"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "file_path": create_property_schema("string", "The absolute path to the file to write"),
                "content": create_property_schema("string", "The content to write to the file")
            },
            required=["file_path", "content"]
        )
    
    def execute(self, file_path: str, content: str) -> str:
        try:
            path = Path(file_path)
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"File created successfully at: {file_path}"
            
        except Exception as e:
            return f"Error: {str(e)}"


class NotebookReadTool(ToolBase):
    """Reads a Jupyter notebook"""
    
    def __init__(self):
        super().__init__(
            name="NotebookRead",
            description="Reads a Jupyter notebook (.ipynb file) and returns all cells"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "notebook_path": create_property_schema("string", "The absolute path to the notebook"),
                "cell_id": create_property_schema("string", "The ID of a specific cell to read")
            },
            required=["notebook_path"]
        )
    
    def execute(self, notebook_path: str, cell_id: Optional[str] = None) -> str:
        try:
            path = Path(notebook_path)
            
            if not path.exists():
                return f"Error: Notebook '{notebook_path}' does not exist"
            
            with open(path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            cells = notebook.get('cells', [])
            
            if cell_id:
                # Find specific cell
                for cell in cells:
                    if cell.get('id') == cell_id:
                        return self._format_cell(cell)
                return f"Error: Cell with id '{cell_id}' not found"
            else:
                # Return all cells
                result = []
                for i, cell in enumerate(cells):
                    result.append(f"Cell {i} [{cell.get('cell_type', 'unknown')}]:")
                    result.append(self._format_cell(cell))
                    result.append("")
                
                return '\n'.join(result)
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _format_cell(self, cell: Dict[str, Any]) -> str:
        """Format a single cell"""
        cell_type = cell.get('cell_type', 'unknown')
        source = cell.get('source', [])
        
        if isinstance(source, list):
            source = ''.join(source)
        
        result = f"Type: {cell_type}\n"
        result += f"Source:\n{source}\n"
        
        if cell_type == 'code' and 'outputs' in cell:
            result += "Outputs:\n"
            for output in cell['outputs']:
                if 'text' in output:
                    result += ''.join(output['text'])
                elif 'data' in output:
                    for mime, data in output['data'].items():
                        if mime == 'text/plain':
                            result += ''.join(data) if isinstance(data, list) else data
        
        return result


class NotebookEditTool(ToolBase):
    """Edits a Jupyter notebook"""
    
    def __init__(self):
        super().__init__(
            name="NotebookEdit",
            description="Completely replaces the contents of a specific cell in a Jupyter notebook"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "notebook_path": create_property_schema("string", "The absolute path to the notebook"),
                "cell_id": create_property_schema("string", "The ID of the cell to edit"),
                "new_source": create_property_schema("string", "The new source for the cell"),
                "cell_type": create_property_schema("string", "The type of the cell", enum=["code", "markdown"]),
                "edit_mode": create_property_schema("string", "The type of edit", enum=["replace", "insert", "delete"])
            },
            required=["notebook_path", "new_source"]
        )
    
    def execute(self, notebook_path: str, new_source: str, cell_id: Optional[str] = None, 
                cell_type: Optional[str] = None, edit_mode: str = "replace") -> str:
        try:
            path = Path(notebook_path)
            
            if not path.exists():
                return f"Error: Notebook '{notebook_path}' does not exist"
            
            with open(path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            cells = notebook.get('cells', [])
            
            if edit_mode == "replace":
                found = False
                for cell in cells:
                    if cell_id and cell.get('id') == cell_id:
                        cell['source'] = new_source.splitlines(True)
                        if cell_type:
                            cell['cell_type'] = cell_type
                        found = True
                        break
                
                if not found:
                    return f"Error: Cell with id '{cell_id}' not found"
                    
            elif edit_mode == "insert":
                new_cell = {
                    'cell_type': cell_type or 'code',
                    'source': new_source.splitlines(True),
                    'metadata': {},
                    'id': str(time.time())
                }
                
                if cell_id:
                    # Insert after specific cell
                    for i, cell in enumerate(cells):
                        if cell.get('id') == cell_id:
                            cells.insert(i + 1, new_cell)
                            break
                else:
                    # Insert at beginning
                    cells.insert(0, new_cell)
                    
            elif edit_mode == "delete":
                cells = [c for c in cells if c.get('id') != cell_id]
                notebook['cells'] = cells
            
            # Write back
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=1)
            
            return f"Notebook {notebook_path} updated successfully"
            
        except Exception as e:
            return f"Error: {str(e)}"


class WebFetchTool(ToolBase):
    """Fetches content from a URL"""
    
    def __init__(self):
        super().__init__(
            name="WebFetch",
            description="Fetches content from a specified URL and processes it"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "url": create_property_schema("string", "The URL to fetch content from", format="uri"),
                "prompt": create_property_schema("string", "The prompt to run on the fetched content")
            },
            required=["url", "prompt"]
        )
    
    def execute(self, url: str, prompt: str) -> str:
        try:
            # Check for restricted domains
            restricted_domains = ['docs.python.org']  # Example restriction
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            if any(d in domain for d in restricted_domains):
                return f"Claude Code is unable to fetch from {domain}"
            
            # In a real implementation, this would fetch and process the URL
            # For now, return a simulated response
            return f"Fetched content from {url}\nProcessed with prompt: {prompt}\n\nResult: [Content would be shown here]"
            
        except Exception as e:
            return f"Error: {str(e)}"


class TodoWriteTool(ToolBase):
    """Manage todo list"""
    
    def __init__(self):
        super().__init__(
            name="TodoWrite",
            description="Create and manage a structured task list"
        )
        self.todos = []
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "todos": create_property_schema("array", "The updated todo list",
                    items={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "minLength": 1},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                            "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                            "id": {"type": "string"}
                        },
                        "required": ["content", "status", "priority", "id"],
                        "additionalProperties": False
                    }
                )
            },
            required=["todos"]
        )
    
    def execute(self, todos: List[Dict[str, Any]]) -> str:
        self.todos = todos
        return "Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable"


class WebSearchTool(ToolBase):
    """Web search tool"""
    
    def __init__(self):
        super().__init__(
            name="WebSearch",
            description="Allows Claude to search the web and use the results to inform responses"
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "query": create_property_schema("string", "The search query to use", minLength=2),
                "allowed_domains": create_property_schema("array", "Only include results from these domains", items={"type": "string"}),
                "blocked_domains": create_property_schema("array", "Never include results from these domains", items={"type": "string"})
            },
            required=["query"]
        )
    
    def execute(self, query: str, allowed_domains: Optional[List[str]] = None, 
                blocked_domains: Optional[List[str]] = None) -> str:
        # In a real implementation, this would perform web search
        # For now, return simulated results
        results = [
            {"title": f"Result 1 for {query}", "url": "https://example.com/1"},
            {"title": f"Result 2 for {query}", "url": "https://example.com/2"}
        ]
        
        output = f"Web search results for query: \"{query}\"\n\n"
        output += f"Links: {json.dumps(results)}\n\n"
        output += "Based on the search results, here's what I found:\n[Search results summary would go here]"
        
        return output