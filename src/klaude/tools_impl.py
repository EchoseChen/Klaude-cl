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
            description="""Launch a new agent to handle complex, multi-step tasks autonomously. 

Available agent types and the tools they have access to:
- general-purpose: General-purpose agent for researching complex questions, searching for code, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. (Tools: *)

When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.



When NOT to use the Agent tool:
- If you want to read a specific file path, use the Read or Glob tool instead of the Agent tool, to find the match more quickly
- If you are searching for a specific class definition like "class Foo", use the Glob tool instead, to find the match more quickly
- If you are searching for code within a specific file or set of 2-3 files, use the Read tool instead of the Agent tool, to find the match more quickly
- Other tasks that are not related to the agent descriptions above


Usage notes:
1. Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses
2. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.
3. Each agent invocation is stateless. You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report. Therefore, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.
4. The agent's outputs should generally be trusted
5. Clearly tell the agent whether you expect it to write code or just to do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent
6. If the agent description mentions that it should be used proactively, then you should try your best to use it without the user having to ask for it first. Use your judgement.

Example usage:

<example_agent_descriptions>
"code-reviewer": use this agent after you are done writing a signficant piece of code
"greeting-responder": use this agent when to respond to user greetings with a friendly joke
</example_agent_description>

<example>
user: "Please write a function that checks if a number is prime"
assistant: Sure let me write a function that checks if a number is prime
assistant: First let me use the Write tool to write a function that checks if a number is prime
assistant: I'm going to use the Write tool to write the following code:
<code>
function isPrime(n) {
  if (n <= 1) return false
  for (let i = 2; i * i <= n; i++) {
    if (n % i === 0) return false
  }
  return true
}
</code>
<commentary>
Since a signficant piece of code was written and the task was completed, now use the code-reviewer agent to review the code
</commentary>
assistant: Now let me use the code-reviewer agent to review the code
assistant: Uses the Task tool to launch the with the code-reviewer agent 
</example>

<example>
user: "Hello"
<commentary>
Since the user is greeting, use the greeting-responder agent to respond with a friendly joke
</commentary>
assistant: "I'm going to use the Task tool to launch the with the greeting-responder agent"
</example>
"""
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
            description="""Executes a given bash command in a persistent shell session with optional timeout, ensuring proper handling and security measures.

Before executing the command, please follow these steps:

1. Directory Verification:
   - If the command will create new directories or files, first use the LS tool to verify the parent directory exists and is the correct location
   - For example, before running "mkdir foo/bar", first use LS to check that "foo" exists and is the intended parent directory

2. Command Execution:
   - Always quote file paths that contain spaces with double quotes (e.g., cd "path with spaces/file.txt")
   - Examples of proper quoting:
     - cd "/Users/name/My Documents" (correct)
     - cd /Users/name/My Documents (incorrect - will fail)
     - python "/path/with spaces/script.py" (correct)
     - python /path/with spaces/script.py (incorrect - will fail)
   - After ensuring proper quoting, execute the command.
   - Capture the output of the command.

Usage notes:
  - The command argument is required.
  - You can specify an optional timeout in milliseconds (up to 600000ms / 10 minutes). If not specified, commands will timeout after 120000ms (2 minutes).
  - It is very helpful if you write a clear, concise description of what this command does in 5-10 words.
  - If the output exceeds 30000 characters, output will be truncated before being returned to you.
  - VERY IMPORTANT: You MUST avoid using search commands like `find` and `grep`. Instead use Grep, Glob, or Task to search. You MUST avoid read tools like `cat`, `head`, `tail`, and `ls`, and use Read and LS to read files.
 - If you _still_ need to run `grep`, STOP. ALWAYS USE ripgrep at `rg` first, which all ${PRODUCT_NAME} users have pre-installed.
  - When issuing multiple commands, use the ';' or '&&' operator to separate them. DO NOT use newlines (newlines are ok in quoted strings).
  - Try to maintain your current working directory throughout the session by using absolute paths and avoiding usage of `cd`. You may use `cd` if the User explicitly requests it.
    <good-example>
    pytest /foo/bar/tests
    </good-example>
    <bad-example>
    cd /foo/bar && pytest tests
    </bad-example>




# Committing changes with git

When the user asks you to create a new git commit, follow these steps carefully:

1. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following bash commands in parallel, each using the Bash tool:
  - Run a git status command to see all untracked files.
  - Run a git diff command to see both staged and unstaged changes that will be committed.
  - Run a git log command to see recent commit messages, so that you can follow this repository's commit message style.
2. Analyze all staged changes (both previously staged and newly added) and draft a commit message:
  - Summarize the nature of the changes (eg. new feature, enhancement to an existing feature, bug fix, refactoring, test, docs, etc.). Ensure the message accurately reflects the changes and their purpose (i.e. "add" means a wholly new feature, "update" means an enhancement to an existing feature, "fix" means a bug fix, etc.).
  - Check for any sensitive information that shouldn't be committed
  - Draft a concise (1-2 sentences) commit message that focuses on the "why" rather than the "what"
  - Ensure it accurately reflects the changes and their purpose
3. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following commands in parallel:
   - Add relevant untracked files to the staging area.
   - Create the commit with a message ending with:
   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   - Run git status to make sure the commit succeeded.
4. If the commit fails due to pre-commit hook changes, retry the commit ONCE to include these automated changes. If it fails again, it usually means a pre-commit hook is preventing the commit. If the commit succeeds but you notice that files were modified by the pre-commit hook, you MUST amend your commit to include them.

Important notes:
- NEVER update the git config
- NEVER run additional commands to read or explore code, besides git bash commands
- NEVER use the TodoWrite or Task tools
- DO NOT push to the remote repository unless the user explicitly asks you to do so
- IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since they require interactive input which is not supported.
- If there are no changes to commit (i.e., no untracked files and no modifications), do not create an empty commit
- In order to ensure good formatting, ALWAYS pass the commit message via a HEREDOC, a la this example:
<example>
git commit -m "$(cat <<'EOF'
   Commit message here.

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
</example>

# Creating pull requests
Use the gh command via the Bash tool for ALL GitHub-related tasks including working with issues, pull requests, checks, and releases. If given a Github URL use the gh command to get the information needed.

IMPORTANT: When the user asks you to create a pull request, follow these steps carefully:

1. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following bash commands in parallel using the Bash tool, in order to understand the current state of the branch since it diverged from the main branch:
   - Run a git status command to see all untracked files
   - Run a git diff command to see both staged and unstaged changes that will be committed
   - Check if the current branch tracks a remote branch and is up to date with the remote, so you know if you need to push to the remote
   - Run a git log command and `git diff [base-branch]...HEAD` to understand the full commit history for the current branch (from the time it diverged from the base branch)
2. Analyze all changes that will be included in the pull request, making sure to look at all relevant commits (NOT just the latest commit, but ALL commits that will be included in the pull request!!!), and draft a pull request summary
3. You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. ALWAYS run the following commands in parallel:
   - Create new branch if needed
   - Push to remote with -u flag if needed
   - Create PR using gh pr create with the format below. Use a HEREDOC to pass the body to ensure correct formatting.
<example>
gh pr create --title "the pr title" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points>

## Test plan
[Checklist of TODOs for testing the pull request...]

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"
</example>

Important:
- NEVER update the git config
- DO NOT use the TodoWrite or Task tools
- Return the PR URL when you're done, so the user can see it

# Other common operations
- View comments on a Github PR: gh api repos/foo/bar/pulls/123/comments"""
        )
        self.shell_env = os.environ.copy()
        self.cwd = os.getcwd()
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "command": create_property_schema("string", "The command to execute"),
                "timeout": create_property_schema("number", "Optional timeout in milliseconds (max 600000)"),
                "description": create_property_schema("string", """ Clear, concise description of what this command does in 5-10 words. Examples:
Input: ls
Output: Lists files in current directory

Input: git status
Output: Shows working tree status

Input: npm install
Output: Installs package dependencies

Input: mkdir foo
Output: Creates directory 'foo'""")
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
            description="""- Fast file pattern matching tool that works with any codebase size
- Supports glob patterns like "**/*.js" or "src/**/*.ts"
- Returns matching file paths sorted by modification time
- Use this tool when you need to find files by name patterns
- When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead
- You have the capability to call multiple tools in a single response. It is always better to speculatively perform multiple searches as a batch that are potentially useful."""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "pattern": create_property_schema("string", "The glob pattern to match files against"),
                "path": create_property_schema("string", """The directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter "undefined" or "null" - simply omit it for the default behavior. Must be a valid directory path if provided.""")
            },
            required=["pattern"]
        )
    
    def execute(self, pattern: str, path: Optional[str] = None) -> str:
        try:
            search_path = Path(path) if path else Path.cwd()
            
            # Handle brace expansion {a,b,c} manually
            if '{' in pattern and '}' in pattern:
                matches = set()
                # Extract the brace content
                import re
                brace_match = re.search(r'{([^}]+)}', pattern)
                if brace_match:
                    options = brace_match.group(1).split(',')
                    base_pattern = pattern[:brace_match.start()] + '{}' + pattern[brace_match.end():]
                    
                    for option in options:
                        expanded_pattern = base_pattern.format(option.strip())
                        # Handle ** for recursive matching
                        if '**' in expanded_pattern:
                            matches.update(search_path.rglob(expanded_pattern.replace('**/', '')))
                        else:
                            matches.update(search_path.glob(expanded_pattern))
                matches = list(matches)
            else:
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
            description="""A powerful search tool built on ripgrep

  Usage:
  - ALWAYS use Grep for search tasks. NEVER invoke `grep` or `rg` as a Bash command. The Grep tool has been optimized for correct permissions and access.
  - Supports full regex syntax (e.g., "log.*Error", "function\\s+\\w+")
  - Filter files with glob parameter (e.g., "*.js", "**/*.tsx") or type parameter (e.g., "js", "py", "rust")
  - Output modes: "content" shows matching lines, "files_with_matches" shows only file paths (default), "count" shows match counts
  - Use Task tool for open-ended searches requiring multiple rounds
  - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping (use `interface\\{\\}` to find `interface{}` in Go code)
  - Multiline matching: By default patterns match within single lines only. For cross-line patterns like `struct \\{[\\s\\S]*?field`, use `multiline: true`
"""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "pattern": create_property_schema("string", "The regular expression pattern to search for in file contents"),
                "path": create_property_schema("string", "File or directory to search in (rg PATH). Defaults to current working directory."),
                "glob": create_property_schema("string", """Glob pattern to filter files (e.g. "*.js", "*.{ts,tsx}") - maps to rg --glob"""),
                "type": create_property_schema("string", "File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types."),
                "output_mode": create_property_schema("string", """Output mode: "content" shows matching lines (supports -A/-B/-C context, -n line numbers, head_limit), "files_with_matches" shows file paths (supports head_limit), "count" shows match counts (supports head_limit). Defaults to "files_with_matches".""", enum=["content", "files_with_matches", "count"]),
                "-n": create_property_schema("boolean", """Show line numbers in output (rg -n). Requires output_mode: "content", ignored otherwise."""),
                "-i": create_property_schema("boolean", "Case insensitive search (rg -i)"),
                "-A": create_property_schema("number", """Number of lines to show after each match (rg -A). Requires output_mode: "content", ignored otherwise."""),
                "-B": create_property_schema("number", """Number of lines to show before each match (rg -B). Requires output_mode: "content", ignored otherwise."""),
                "-C": create_property_schema("number", """Number of lines to show before and after each match (rg -C). Requires output_mode: "content", ignored otherwise."""),
                "head_limit": create_property_schema("number", """Limit output to first N lines/entries, equivalent to "| head -N". Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count (limits count entries). When unspecified, shows all results from ripgrep."""),
                "multiline": create_property_schema("boolean", "Enable multiline mode where . matches newlines and patterns can span lines (rg -U --multiline-dotall). Default: false.")
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
            description="""Lists files and directories in a given path. The path parameter must be an absolute path, not a relative path. You can optionally provide an array of glob patterns to ignore with the ignore parameter. You should generally prefer the Glob and Grep tools, if you know which directories to search."""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "path": create_property_schema("string", "The absolute path to the directory to list (must be absolute, not relative)"),
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
            description="""Reads a file from the local filesystem. You can access any file directly by using this tool.
Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.

Usage:
- The file_path parameter must be an absolute path, not a relative path
- By default, it reads up to 2000 lines starting from the beginning of the file
- You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters
- Any lines longer than 2000 characters will be truncated
- Results are returned using cat -n format, with line numbers starting at 1
- This tool allows Claude Code to read images (eg PNG, JPG, etc). When reading an image file the contents are presented visually as Claude Code is a multimodal LLM.
- This tool can read PDF files (.pdf). PDFs are processed page by page, extracting both text and visual content for analysis.
- For Jupyter notebooks (.ipynb files), use the NotebookRead instead
- You have the capability to call multiple tools in a single response. It is always better to speculatively read multiple files as a batch that are potentially useful. 
- You will regularly be asked to read screenshots. If the user provides a path to a screenshot ALWAYS use this tool to view the file at the path. This tool will work with all temporary file paths like /var/folders/123/abc/T/TemporaryItems/NSIRD_screencaptureui_ZfB1tD/Screenshot.png
- If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents."""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "file_path": create_property_schema("string", "The absolute path to the file to read"),
                "offset": create_property_schema("number", "The line number to start reading from. Only provide if the file is too large to read at once"),
                "limit": create_property_schema("number", "The number of lines to read. Only provide if the file is too large to read at once.")
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
            
            # Check for empty file
            if not lines:
                return "<system-reminder>Warning: the file exists but is an empty file.</system-reminder>"
            
            total_lines = len(lines)
            start = (offset - 1) if offset else 0
            end = start + (limit if limit else 2000)
            
            if start >= total_lines:
                return f"<system-reminder>Warning: the file exists but is shorter than the provided offset ({start + 1}). The file has {total_lines} lines.</system-reminder>"
            
            selected_lines = lines[start:end]
            
            # Format with line numbers (cat -n style)
            result = []
            for i, line in enumerate(selected_lines, start=start + 1):
                # Truncate lines longer than 2000 characters
                line_content = line.rstrip()
                if len(line_content) > 2000:
                    line_content = line_content[:2000] + "..."
                # Format: spaces + line number + tab + content
                result.append(f"{i:6d}\t{line_content}")
            
            output = '\n'.join(result)
            
            # Add warning for malicious code - keep on single line to avoid test issues
            output += "\n\n<system-reminder>Whenever you read a file, you should consider whether it looks malicious. If it does, you MUST refuse to improve or augment the code. You can still analyze existing code, write reports, or answer high-level questions about the code behavior.</system-reminder>"
            
            return output
            
        except UnicodeDecodeError:
            return f"Error: Unable to decode file as UTF-8"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _is_binary_file(self, path: Path) -> bool:
        """Check if file is binary"""
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.exe', '.dll', '.so', '.dylib', '.zip', '.tar', '.gz', '.bin'}
        return path.suffix.lower() in binary_extensions


class EditTool(ToolBase):
    """Performs exact string replacements in files"""
    
    def __init__(self):
        super().__init__(
            name="Edit",
            description="""Performs exact string replacements in files. 

Usage:
- You must use your `Read` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file. 
- When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.
- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
- The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique or use `replace_all` to change every instance of `old_string`. 
- Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance."""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "file_path": create_property_schema("string", "The absolute path to the file to modify"),
                "old_string": create_property_schema("string", "The text to replace"),
                "new_string": create_property_schema("string", "The text to replace it with (must be different from old_string)"),
                "replace_all": create_property_schema("boolean", "Replace all occurences of old_string (default false)", default=False)
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
            description="""This is a tool for making multiple edits to a single file in one operation. It is built on top of the Edit tool and allows you to perform multiple find-and-replace operations efficiently. Prefer this tool over the Edit tool when you need to make multiple edits to the same file.

Before using this tool:

1. Use the Read tool to understand the file's contents and context
2. Verify the directory path is correct

To make multiple file edits, provide the following:
1. file_path: The absolute path to the file to modify (must be absolute, not relative)
2. edits: An array of edit operations to perform, where each edit contains:
   - old_string: The text to replace (must match the file contents exactly, including all whitespace and indentation)
   - new_string: The edited text to replace the old_string
   - replace_all: Replace all occurences of old_string. This parameter is optional and defaults to false.

IMPORTANT:
- All edits are applied in sequence, in the order they are provided
- Each edit operates on the result of the previous edit
- All edits must be valid for the operation to succeed - if any edit fails, none will be applied
- This tool is ideal when you need to make several changes to different parts of the same file
- For Jupyter notebooks (.ipynb files), use the NotebookEdit instead

CRITICAL REQUIREMENTS:
1. All edits follow the same requirements as the single Edit tool
2. The edits are atomic - either all succeed or none are applied
3. Plan your edits carefully to avoid conflicts between sequential operations

WARNING:
- The tool will fail if edits.old_string doesn't match the file contents exactly (including whitespace)
- The tool will fail if edits.old_string and edits.new_string are the same
- Since edits are applied in sequence, ensure that earlier edits don't affect the text that later edits are trying to find

When making edits:
- Ensure all edits result in idiomatic, correct code
- Do not leave the code in a broken state
- Always use absolute file paths (starting with /)
- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
- Use replace_all for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.

If you want to create a new file, use:
- A new file path, including dir name if needed
- First edit: empty old_string and the new file's contents as new_string
- Subsequent edits: normal edit operations on the created content"""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "file_path": create_property_schema("string", "The absolute path to the file to modify"),
                "edits": create_property_schema("array", "Array of edit operations to perform sequentially on the file", 
                    items={
                        "type": "object",
                        "properties": {
                            "old_string": {"type": "string", "description": "The text to replace"},
                            "new_string": {"type": "string", "description": "The text to replace it with"},
                            "replace_all": {"type": "boolean", "default": False, "description": "Replace all occurences of old_string (default false)."}
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
            # Check for empty edits
            if not edits:
                return "Error: No edits provided"
            
            path = Path(file_path)
            
            # Read original content
            if not path.exists():
                # Allow creating new files
                if edits and edits[0]["old_string"] == "":
                    original_content = ""
                else:
                    return f"Error: File '{file_path}' does not exist"
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            
            # Make a copy of content to work with
            content = original_content
            
            # First, validate all edits before applying any
            for i, edit in enumerate(edits):
                old_string = edit["old_string"]
                new_string = edit["new_string"]
                
                if old_string == new_string:
                    return f"Error: In edit {i+1}, old_string and new_string must be different"
            
            # Apply edits sequentially - first validate all edits can be applied
            temp_content = content
            for i, edit in enumerate(edits):
                old_string = edit["old_string"]
                
                if old_string != "":
                    count = temp_content.count(old_string)
                    if count == 0:
                        return f"Error: In edit {i+1}, old_string not found"
                    
                    # Update temp content for next validation
                    if edit.get("replace_all", False):
                        temp_content = temp_content.replace(old_string, edit["new_string"])
                    else:
                        temp_content = temp_content.replace(old_string, edit["new_string"], 1)
            
            # All validations passed, now apply edits for real
            results = []
            for i, edit in enumerate(edits):
                old_string = edit["old_string"]
                new_string = edit["new_string"]
                replace_all = edit.get("replace_all", False)
                
                if old_string == "":
                    # Special case for new file
                    content = new_string
                    results.append("Created new file")
                else:
                    count = content.count(old_string)
                    
                    if replace_all:
                        content = content.replace(old_string, new_string)
                        results.append(f"Replaced {count} occurrences")
                    else:
                        content = content.replace(old_string, new_string, 1)
                        results.append("Replaced 1 occurrence")
            
            # Only write if all edits succeeded
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
            description="""Writes a file to the local filesystem.

Usage:
- This tool will overwrite the existing file if there is one at the provided path.
- If this is an existing file, you MUST use the Read tool first to read the file's contents. This tool will fail if you did not read the file first.
- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
- Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked."""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "file_path": create_property_schema("string", "The absolute path to the file to write (must be absolute, not relative)"),
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
            description="""Reads a Jupyter notebook (.ipynb file) and returns all of the cells with their outputs. Jupyter notebooks are interactive documents that combine code, text, and visualizations, commonly used for data analysis and scientific computing. The notebook_path parameter must be an absolute path, not a relative path."""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "notebook_path": create_property_schema("string", "The absolute path to the Jupyter notebook file to read (must be absolute, not relative)"),
                "cell_id": create_property_schema("string", "The ID of a specific cell to read. If not provided, all cells will be read.")
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
            description="""Completely replaces the contents of a specific cell in a Jupyter notebook (.ipynb file) with new source. Jupyter notebooks are interactive documents that combine code, text, and visualizations, commonly used for data analysis and scientific computing. The notebook_path parameter must be an absolute path, not a relative path. The cell_number is 0-indexed. Use edit_mode=insert to add a new cell at the index specified by cell_number. Use edit_mode=delete to delete the cell at the index specified by cell_number."""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "notebook_path": create_property_schema("string", "The absolute path to the Jupyter notebook file to edit (must be absolute, not relative)"),
                "cell_id": create_property_schema("string", "The ID of the cell to edit. When inserting a new cell, the new cell will be inserted after the cell with this ID, or at the beginning if not specified."),
                "new_source": create_property_schema("string", "The new source for the cell"),
                "cell_type": create_property_schema("string", "The type of the cell (code or markdown). If not specified, it defaults to the current cell type. If using edit_mode=insert, this is required.", enum=["code", "markdown"]),
                "edit_mode": create_property_schema("string", "The type of edit to make (replace, insert, delete). Defaults to replace.", enum=["replace", "insert", "delete"])
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
                    # Check both cell.id and cell.metadata.id for compatibility
                    cell_id_match = (cell.get('id') == cell_id or 
                                    cell.get('metadata', {}).get('id') == cell_id)
                    if cell_id and cell_id_match:
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
                        cell_id_match = (cell.get('id') == cell_id or 
                                        cell.get('metadata', {}).get('id') == cell_id)
                        if cell_id_match:
                            cells.insert(i + 1, new_cell)
                            break
                else:
                    # Insert at beginning
                    cells.insert(0, new_cell)
                    
            elif edit_mode == "delete":
                # Filter out cells with matching ID
                cells = [c for c in cells if not (c.get('id') == cell_id or 
                                                  c.get('metadata', {}).get('id') == cell_id)]
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
            description="""
- Fetches content from a specified URL and processes it using an AI model
- Takes a URL and a prompt as input
- Fetches the URL content, converts HTML to markdown
- Processes the content with the prompt using a small, fast model
- Returns the model's response about the content
- Use this tool when you need to retrieve and analyze web content

Usage notes:
  - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that tool instead of this one, as it may have fewer restrictions. All MCP-provided tools start with "mcp__".
  - The URL must be a fully-formed valid URL
  - HTTP URLs will be automatically upgraded to HTTPS
  - The prompt should describe what information you want to extract from the page
  - This tool is read-only and does not modify any files
  - Results may be summarized if the content is very large
  - Includes a self-cleaning 15-minute cache for faster responses when repeatedly accessing the same URL
  - When a URL redirects to a different host, the tool will inform you and provide the redirect URL in a special format. You should then make a new WebFetch request with the redirect URL to fetch the content.
"""
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
            from urllib.parse import urlparse
            
            # Validate URL
            parsed = urlparse(url)
            
            # Check for malformed URLs
            if not parsed.scheme:
                return f"Error: Invalid URL - missing scheme (http:// or https://)"
            
            if parsed.scheme not in ['http', 'https']:
                return f"Error: Invalid URL - unsupported scheme '{parsed.scheme}'"
            
            if not parsed.netloc:
                return f"Error: Invalid URL - missing domain"
            
            # Check for invalid domain format
            if '..' in parsed.netloc:
                return f"Error: Invalid URL - malformed domain"
            
            # Check for invalid ports
            if parsed.port:
                if parsed.port < 1 or parsed.port > 65535:
                    return f"Error: Invalid URL - invalid port number"
            
            # Upgrade HTTP to HTTPS
            if parsed.scheme == 'http':
                url = url.replace('http://', 'https://', 1)
                
            # Check for restricted domains
            restricted_domains = ['docs.python.org']  # Example restriction
            domain = parsed.netloc
            
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
            description="""Use this tool to create and manage a structured task list for your current coding session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool
Use this tool proactively in these scenarios:

1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
5. After receiving new instructions - Immediately capture user requirements as todos
6. When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you should only have one todo as in_progress at a time
7. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation

## When NOT to Use This Tool

Skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no organizational benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational

NOTE that you should not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.

## Examples of When to Use the Todo List

<example>
User: I want to add a dark mode toggle to the application settings. Make sure you run the tests and build when you're done!
Assistant: I'll help add a dark mode toggle to your application settings. Let me create a todo list to track this implementation.
*Creates todo list with the following items:*
1. Create dark mode toggle component in Settings page
2. Add dark mode state management (context/store)
3. Implement CSS-in-JS styles for dark theme
4. Update existing components to support theme switching
5. Run tests and build process, addressing any failures or errors that occur
*Begins working on the first task*

<reasoning>
The assistant used the todo list because:
1. Adding dark mode is a multi-step feature requiring UI, state management, and styling changes
2. The user explicitly requested tests and build be run afterward
3. The assistant inferred that tests and build need to pass by adding "Ensure tests and build succeed" as the final task
</reasoning>
</example>

<example>
User: Help me rename the function getCwd to getCurrentWorkingDirectory across my project
Assistant: Let me first search through your codebase to find all occurrences of 'getCwd'.
*Uses grep or search tools to locate all instances of getCwd in the codebase*
Assistant: I've found 15 instances of 'getCwd' across 8 different files. Let me create a todo list to track these changes.
*Creates todo list with specific items for each file that needs updating*

<reasoning>
The assistant used the todo list because:
1. First, the assistant searched to understand the scope of the task
2. Upon finding multiple occurrences across different files, it determined this was a complex task with multiple steps
3. The todo list helps ensure every instance is tracked and updated systematically
4. This approach prevents missing any occurrences and maintains code consistency
</reasoning>
</example>


<example>
User: I need to implement these features for my e-commerce site: user registration, product catalog, shopping cart, and checkout flow.
Assistant: I'll help implement these features. First, let's add all the features to the todo list.
*Creates a todo list breaking down each feature into specific tasks based on the project architecture*
Assistant: Let's start with user registration. This will involve creating database models, API endpoints, and frontend forms that integrate with your existing authentication system.

<reasoning>
The assistant used the todo list because:
1. The user provided multiple complex features to implement in a comma separated list
2. The todo list helps organize these large features into manageable tasks
3. This approach allows for tracking progress across the entire implementation
</reasoning>
</example>

<example>
User: Can you help optimize my React application? It's rendering slowly and has performance issues.</user>
Assistant: I'll help optimize your React application. First, let me examine your codebase to identify potential performance bottlenecks.
*Reviews component structure, render patterns, state management, and data fetching*
Assistant: After analyzing your codebase, I've identified several performance issues. Let me create a todo list to track our optimization efforts.
*Creates todo list with items like: 1) Implement memoization for expensive calculations in ProductList, 2) Add virtualization for long lists in Dashboard, 3) Optimize image loading in Gallery component, 4) Fix state update loops in ShoppingCart, 5) Review bundle size and implement code splitting*
Let's start by implementing memoization for the expensive calculations in your ProductList component.</assistant>

<reasoning>
The assistant used the todo list because:
1. First, the assistant examined the codebase to identify specific performance issues
2. Based on this analysis, it identified multiple optimization opportunities
3. Performance optimization is a non-trivial task requiring multiple steps
4. The todo list helps methodically track improvements across different components
5. This systematic approach ensures all performance bottlenecks are addressed
</reasoning>
</example>

## Examples of When NOT to Use the Todo List

<example>
User: How do I print 'Hello World' in Python?
Assistant: In Python, you can print "Hello World" with this simple code:

python
print("Hello World")

This will output the text "Hello World" to the console when executed.</assistant>

<reasoning>
The assistant did not use the todo list because this is a single, trivial task that can be completed in one step. There's no need to track multiple tasks or steps for such a straightforward request.
</reasoning>
</example>

<example>
User: What does the git status command do?
Assistant: The git status command shows the current state of your working directory and staging area. It displays which changes have been staged, which haven't, and which files aren't being tracked by Git. This is a fundamental command for understanding the current state of your repository before making commits.

<reasoning>
The assistant did not use the todo list because this is an informational request with no actual coding task to complete. The user is simply asking for an explanation, not for the assistant to perform multiple steps or tasks.
</reasoning>
</example>

<example>
User: Can you add a comment to the calculateTotal function to explain what it does?
Assistant: Sure, let me add a comment to the calculateTotal function to explain what it does.
* Uses the Edit tool to add a comment to the calculateTotal function *

<reasoning>
The assistant did not use the todo list because this is a single, straightforward task confined to one location in the code. Adding a comment doesn't require tracking multiple steps or systematic organization.
</reasoning>
</example>

<example>
User: Run npm install for me and tell me what happens.
Assistant: I'll run the npm install command for you.

*Executes: npm install*

The command completed successfully. Here's the output:
[Output of npm install command]

All dependencies have been installed according to your package.json file.

<reasoning>
The assistant did not use the todo list because this is a single command execution with immediate results. There are no multiple steps to track or organize, making the todo list unnecessary for this straightforward task.
</reasoning>
</example>

## Task States and Management

1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (limit to ONE task at a time)
   - completed: Task finished successfully

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
   - Only have ONE task in_progress at any time
   - Complete current tasks before starting new ones
   - Remove tasks that are no longer relevant from the list entirely

3. **Task Completion Requirements**:
   - ONLY mark a task as completed when you have FULLY accomplished it
   - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
   - When blocked, create a new task describing what needs to be resolved
   - Never mark a task as completed if:
     - Tests are failing
     - Implementation is partial
     - You encountered unresolved errors
     - You couldn't find necessary files or dependencies

4. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex tasks into smaller, manageable steps
   - Use clear, descriptive task names

When in doubt, use this tool. Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully.
"""
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
            description="""
- Allows Claude to search the web and use the results to inform responses
- Provides up-to-date information for current events and recent data
- Returns search result information formatted as search result blocks
- Use this tool for accessing information beyond Claude's knowledge cutoff
- Searches are performed automatically within a single API call

Usage notes:
  - Domain filtering is supported to include or block specific websites
  - Web search is only available in the US
  - Account for "Today's date" in <env>. For example, if <env> says "Today's date: 2025-07-01", and the user wants the latest docs, do not use 2024 in the search query. Use 2025.
"""
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return create_json_schema(
            properties={
                "query": create_property_schema("string", "The search query to use", minLength=2),
                "allowed_domains": create_property_schema("array", "Only include search results from these domains", items={"type": "string"}),
                "blocked_domains": create_property_schema("array", "Never include search results from these domains", items={"type": "string"})
            },
            required=["query"]
        )
    
    def execute(self, query: str, allowed_domains: Optional[List[str]] = None, 
                blocked_domains: Optional[List[str]] = None) -> str:
        # Validate query length
        if len(query) < 2:
            return "Error: Query too short (minimum 2 characters)"
        
        # In a real implementation, this would perform web search
        # For now, return simulated results
        output = f"Web search results for query: \"{query}\"\n\n"
        
        # Add domain filtering info if provided
        if allowed_domains:
            output += f"Filtering results to allowed domains: {', '.join(allowed_domains)}\n"
        if blocked_domains:
            output += f"Excluding results from blocked domains: {', '.join(blocked_domains)}\n"
        
        if allowed_domains or blocked_domains:
            output += "\n"
        
        # Simulated search results in expected format
        output += "1. Example Result 1\n"
        output += "   URL: https://example.com/result1\n"
        output += f"   Summary: First search result for {query}\n\n"
        
        output += "2. Example Result 2\n"
        output += "   URL: https://example.com/result2\n"
        output += f"   Summary: Second search result for {query}\n\n"
        
        # Also include JSON format for backward compatibility
        results = [
            {"title": f"Result 1 for {query}", "url": "https://example.com/1"},
            {"title": f"Result 2 for {query}", "url": "https://example.com/2"}
        ]
        output += f"Links: {json.dumps(results)}\n\n"
        output += "Based on the search results, here's what I found:\n[Search results summary would go here]"
        
        return output