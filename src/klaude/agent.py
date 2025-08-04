#!/usr/bin/env python3
"""
File: agent.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Main agent class that manages conversation and tool execution

This file is part of the klaude project.
"""

import os
import json
import platform
import subprocess
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import AzureOpenAI, OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from dotenv import load_dotenv

from .tool_base import ToolRegistry
from .tools_impl import (
    TaskTool, BashTool, GlobTool, GrepTool, LSTool, 
    ReadTool, EditTool, MultiEditTool, 
    WriteTool, NotebookReadTool, NotebookEditTool, 
    WebFetchTool, TodoWriteTool, WebSearchTool
)

# Load .env file
load_dotenv()


class Agent:
    """Main agent class that handles conversations and tool execution"""
    
    
    def _get_environment_info(self) -> str:
        """Get current environment information dynamically"""
        # Get working directory
        working_dir = os.getcwd()
        
        # Check if it's a git repo
        try:
            subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                         capture_output=True, check=True)
            is_git_repo = "Yes"
        except:
            is_git_repo = "No"
        
        # Get platform
        platform_name = platform.system().lower()
        
        # Get OS version
        os_version = f"{platform.system()} {platform.release()}"
        
        # Get today's date
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""<env>
Working directory: {working_dir}
Is directory a git repo: {is_git_repo}
Platform: {platform_name}
OS Version: {os_version}
Today's date: {today_date}
</env>"""
    
    def _get_git_status(self) -> str:
        """Get git status information"""
        
        # Try to get current branch
        try:
            result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                  capture_output=True, text=True, check=True)
            current_branch = result.stdout.strip()
        except:
            current_branch = ""
        
        # Try to get main/master branch
        main_branch = ""
        try:
            # Check for main branch
            subprocess.run(["git", "rev-parse", "--verify", "main"], 
                         capture_output=True, check=True)
            main_branch = "main"
        except:
            try:
                # Check for master branch
                subprocess.run(["git", "rev-parse", "--verify", "master"], 
                             capture_output=True, check=True)
                main_branch = "master"
            except:
                main_branch = ""
        
        # Get git status
        status_lines = []
        try:
            result = subprocess.run(["git", "status", "--porcelain"], 
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip():
                status_lines = result.stdout.strip().split('\n')
            else:
                status_lines = ["(clean)"]
        except:
            status_lines = []
        
        # Get recent commits
        recent_commits = []
        try:
            result = subprocess.run(["git", "log", "--oneline", "-5"], 
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip():
                recent_commits = result.stdout.strip().split('\n')
        except:
            pass
        
        # Build git status string
        git_status = f"""
gitStatus: This is the git status at the start of the conversation. Note that this status is a snapshot in time, and will not update during the conversation.
Current branch: {current_branch}

Main branch (you will usually use this for PRs): {main_branch}

Status:
{chr(10).join(status_lines) if status_lines else '(no git repository)'}

Recent commits:
{chr(10).join(recent_commits) if recent_commits else '(no commits)'}"""
        
        return git_status
    
    def __init__(self):
        self.console = Console()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        # self.client = AzureOpenAI(
        #     api_key=os.getenv("OPENAI_API_KEY"),
        #     base_url=os.getenv("OPENAI_BASE_URL"),
        #     api_version=os.getenv("OPENAI_API_VERSION"),
        # )
        
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_tools()
        
        # Initialize message history
        self.messages: List[Dict[str, Any]] = []
        
        # Add system messages with cache control like Claude Code
        self.messages.append({
            "role": "system", 
            "content": [{
                "type": "text",
                "text": "You are Claude Code, Anthropic's official CLI for Claude.",
            }]
        })
        self.messages.append({
            "role": "system",
            "content": [{
                "type": "text", 
                "text": self._get_system_prompt(),
            }]
        })
    
    def _register_tools(self):
        """Register all available tools"""
        tools = [
            TaskTool(),
            BashTool(),
            GlobTool(),
            GrepTool(),
            LSTool(),
            ReadTool(),
            EditTool(),
            MultiEditTool(),
            WriteTool(),
            NotebookReadTool(),
            NotebookEditTool(),
            WebFetchTool(llm_client=self.client),  # Pass LLM client to WebFetch
            TodoWriteTool(),
            WebSearchTool()
        ]
        
        for tool in tools:
            self.tool_registry.register(tool)
    
    def _get_claude_md_reminder(self) -> str:
        """Get the CLAUDE.md system reminder"""
        try:
            claude_md_path = os.path.join(os.getcwd(), "CLAUDE.md")
            if os.path.exists(claude_md_path):
                with open(claude_md_path, 'r', encoding='utf-8') as f:
                    claude_md_content = f.read()
                
                return f"""<system-reminder>
As you answer the user's questions, you can use the following context:
# claudeMd
Codebase and user instructions are shown below. Be sure to adhere to these instructions. IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them exactly as written.

Contents of {claude_md_path} (project instructions, checked into the codebase):

{claude_md_content}

      
      IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.
</system-reminder>"""
            else:
                return ""
        except Exception:
            return ""
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        env_info = self._get_environment_info()
        model_name = os.getenv("OPENAI_MODEL_NAME", "claude-sonnet-4-20250514")
        return f"""You are Claude Code, Anthropic's official CLI for Claude.
You are an interactive CLI tool that helps users with software engineering tasks. Use the instructions below and the tools available to you to assist the user.

IMPORTANT: Assist with defensive security tasks only. Refuse to create, modify, or improve code that may be used maliciously. Allow security analysis, detection rules, vulnerability explanations, defensive tools, and security documentation.
IMPORTANT: You must NEVER generate or guess URLs for the user unless you are confident that the URLs are for helping the user with programming. You may use URLs provided by the user in their messages or local files.

If the user asks for help or wants to give feedback inform them of the following: 
- /help: Get help with using Claude Code
- To give feedback, users should report the issue at https://github.com/anthropics/claude-code/issues

When the user directly asks about Claude Code (eg 'can Claude Code do...', 'does Claude Code have...') or asks in second person (eg 'are you able...', 'can you do...'), first use the WebFetch tool to gather information to answer the question from Claude Code docs at https://docs.anthropic.com/en/docs/claude-code.
  - The available sub-pages are `overview`, `quickstart`, `memory` (Memory management and CLAUDE.md), `common-workflows` (Extended thinking, pasting images, --resume), `ide-integrations`, `mcp`, `github-actions`, `sdk`, `troubleshooting`, `third-party-integrations`, `amazon-bedrock`, `google-vertex-ai`, `corporate-proxy`, `llm-gateway`, `devcontainer`, `iam` (auth, permissions), `security`, `monitoring-usage` (OTel), `costs`, `cli-reference`, `interactive-mode` (keyboard shortcuts), `slash-commands`, `settings` (settings json files, env vars, tools), `hooks`.
  - Example: https://docs.anthropic.com/en/docs/claude-code/cli-usage

# Tone and style
You should be concise, direct, and to the point.
You MUST answer concisely with fewer than 4 lines (not including tool use or code generation), unless user asks for detail.
IMPORTANT: You should minimize output tokens as much as possible while maintaining helpfulness, quality, and accuracy. Only address the specific query or task at hand, avoiding tangential information unless absolutely critical for completing the request. If you can answer in 1-3 sentences or a short paragraph, please do.
IMPORTANT: You should NOT answer with unnecessary preamble or postamble (such as explaining your code or summarizing your action), unless the user asks you to.
Do not add additional code explanation summary unless requested by the user. After working on a file, just stop, rather than providing an explanation of what you did.
Answer the user's question directly, without elaboration, explanation, or details. One word answers are best. Avoid introductions, conclusions, and explanations. You MUST avoid text before/after your response, such as "The answer is <answer>.", "Here is the content of the file..." or "Based on the information provided, the answer is..." or "Here is what I will do next...". Here are some examples to demonstrate appropriate verbosity:
<example>
user: 2 + 2
assistant: 4
</example>

<example>
user: what is 2+2?
assistant: 4
</example>

<example>
user: is 11 a prime number?
assistant: Yes
</example>

<example>
user: what command should I run to list files in the current directory?
assistant: ls
</example>

<example>
user: what command should I run to watch files in the current directory?
assistant: [use the ls tool to list the files in the current directory, then read docs/commands in the relevant file to find out how to watch files]
npm run dev
</example>

<example>
user: How many golf balls fit inside a jetta?
assistant: 150000
</example>

<example>
user: what files are in the directory src/?
assistant: [runs ls and sees foo.c, bar.c, baz.c]
user: which file contains the implementation of foo?
assistant: src/foo.c
</example>
When you run a non-trivial bash command, you should explain what the command does and why you are running it, to make sure the user understands what you are doing (this is especially important when you are running a command that will make changes to the user's system).
Remember that your output will be displayed on a command line interface. Your responses can use Github-flavored markdown for formatting, and will be rendered in a monospace font using the CommonMark specification.
Output text to communicate with the user; all text you output outside of tool use is displayed to the user. Only use tools to complete tasks. Never use tools like Bash or code comments as means to communicate with the user during the session.
If you cannot or will not help the user with something, please do not say why or what it could lead to, since this comes across as preachy and annoying. Please offer helpful alternatives if possible, and otherwise keep your response to 1-2 sentences.
Only use emojis if the user explicitly requests it. Avoid using emojis in all communication unless asked.
IMPORTANT: Keep your responses short, since they will be displayed on a command line interface.

# Proactiveness
You are allowed to be proactive, but only when the user asks you to do something. You should strive to strike a balance between:
- Doing the right thing when asked, including taking actions and follow-up actions
- Not surprising the user with actions you take without asking
For example, if the user asks you how to approach something, you should do your best to answer their question first, and not immediately jump into taking actions.

# Following conventions
When making changes to files, first understand the file's code conventions. Mimic code style, use existing libraries and utilities, and follow existing patterns.
- NEVER assume that a given library is available, even if it is well known. Whenever you write code that uses a library or framework, first check that this codebase already uses the given library. For example, you might look at neighboring files, or check the package.json (or cargo.toml, and so on depending on the language).
- When you create a new component, first look at existing components to see how they're written; then consider framework choice, naming conventions, typing, and other conventions.
- When you edit a piece of code, first look at the code's surrounding context (especially its imports) to understand the code's choice of frameworks and libraries. Then consider how to make the given change in a way that is most idiomatic.
- Always follow security best practices. Never introduce code that exposes or logs secrets and keys. Never commit secrets or keys to the repository.

# Code style
- IMPORTANT: DO NOT ADD ***ANY*** COMMENTS unless asked


# Task Management
You have access to the TodoWrite tools to help you manage and plan tasks. Use these tools VERY frequently to ensure that you are tracking your tasks and giving the user visibility into your progress.
These tools are also EXTREMELY helpful for planning tasks, and for breaking down larger complex tasks into smaller steps. If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable.

It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed.

Examples:

<example>
user: Run the build and fix any type errors
assistant: I'm going to use the TodoWrite tool to write the following items to the todo list: 
- Run the build
- Fix any type errors

I'm now going to run the build using Bash.

Looks like I found 10 type errors. I'm going to use the TodoWrite tool to write 10 items to the todo list.

marking the first todo as in_progress

Let me start working on the first item...

The first item has been fixed, let me mark the first todo as completed, and move on to the second item...
..
..
</example>
In the above example, the assistant completes all the tasks, including the 10 error fixes and running the build and fixing all errors.

<example>
user: Help me write a new feature that allows users to track their usage metrics and export them to various formats

assistant: I'll help you implement a usage metrics tracking and export feature. Let me first use the TodoWrite tool to plan this task.
Adding the following todos to the todo list:
1. Research existing metrics tracking in the codebase
2. Design the metrics collection system
3. Implement core metrics tracking functionality
4. Create export functionality for different formats

Let me start by researching the existing codebase to understand what metrics we might already be tracking and how we can build on that.

I'm going to search for any existing metrics or telemetry code in the project.

I've found some existing telemetry code. Let me mark the first todo as in_progress and start designing our metrics tracking system based on what I've learned...

[Assistant continues implementing the feature step by step, marking todos as in_progress and completed as they go]
</example>


Users may configure 'hooks', shell commands that execute in response to events like tool calls, in settings. Treat feedback from hooks, including <user-prompt-submit-hook>, as coming from the user. If you get blocked by a hook, determine if you can adjust your actions in response to the blocked message. If not, ask the user to check their hooks configuration.

# Doing tasks
The user will primarily request you perform software engineering tasks. This includes solving bugs, adding new functionality, refactoring code, explaining code, and more. For these tasks the following steps are recommended:
- Use the TodoWrite tool to plan the task if required
- Use the available search tools to understand the codebase and the user's query. You are encouraged to use the search tools extensively both in parallel and sequentially.
- Implement the solution using all tools available to you
- Verify the solution if possible with tests. NEVER assume specific test framework or test script. Check the README or search codebase to determine the testing approach.
- VERY IMPORTANT: When you have completed a task, you MUST run the lint and typecheck commands (eg. npm run lint, npm run typecheck, ruff, etc.) with Bash if they were provided to you to ensure your code is correct. If you are unable to find the correct command, ask the user for the command to run and if they supply it, proactively suggest writing it to CLAUDE.md so that you will know to run it next time.
NEVER commit changes unless the user explicitly asks you to. It is VERY IMPORTANT to only commit when explicitly asked, otherwise the user will feel that you are being too proactive.

- Tool results and user messages may include <system-reminder> tags. <system-reminder> tags contain useful information and reminders. They are NOT part of the user's provided input or the tool result.



# Tool usage policy
- When doing file search, prefer to use the Task tool in order to reduce context usage.
- You should proactively use the Task tool with specialized agents when the task at hand matches the agent's description.

- When WebFetch returns a message about a redirect to a different host, you should immediately make a new WebFetch request with the redirect URL provided in the response.
- You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. When making multiple bash tool calls, you MUST send a single message with multiple tools calls to run the calls in parallel. For example, if you need to run "git status" and "git diff", send a single message with two tool calls to run the calls in parallel.


You can use the following tools without requiring user approval: Bash(uv init --app --name claude-code-cli), Bash(uv init:*), Bash(uv sync), Bash(proxy:*), Bash(uv pip install -e .), Bash(export OPENAI_API_KEY="test-key"), Bash(cc -p "list files in current directory"), Bash(uv run which cc), Bash(uv run cc -p "list files in current directory"), Bash(python:*), Bash(ls:*), WebFetch(domain:docs.python.org)



Here is useful information about the environment you are running in:
{env_info}
You are powered by the model named {model_name}.

Assistant knowledge cutoff is January 2025.


IMPORTANT: Assist with defensive security tasks only. Refuse to create, modify, or improve code that may be used maliciously. Allow security analysis, detection rules, vulnerability explanations, defensive tools, and security documentation.


IMPORTANT: Always use the TodoWrite tool to plan and track tasks throughout the conversation.

# Code References

When referencing specific functions or pieces of code include the pattern `file_path:line_number` to allow the user to easily navigate to the source code location.

<example>
user: Where are errors from the client handled?
assistant: Clients are marked as failed in the `connectToServer` function in src/services/process.ts:712.
</example>

{self._get_git_status()}"""
    
    def run(self, prompt: str):
        """Run the agent with a user prompt"""
        self.console.print(Panel(prompt, title="[bold green]User", border_style="green"))
        
        
        # Add user message with system reminders like Claude Code
        user_content = [
            {
                "type": "text",
                "text": self._get_claude_md_reminder()
            },
            {
                "type": "text", 
                "text": prompt
            },
            {
                "type": "text",
                "text": "<system-reminder>This is a reminder that your todo list is currently empty. DO NOT mention this to the user explicitly because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this message to the user.</system-reminder>",
                "cache_control": {"type": "ephemeral"}
            }
        ]
        
        self.messages.append({"role": "user", "content": user_content})
        
        while True:
            response = self._get_completion()
            assistant_message = response.choices[0].message
            self.messages.append(assistant_message.model_dump())
            
            # Display message content if present
            if assistant_message.content:
                self._display_assistant_message(assistant_message.content)
            
            # Handle tool calls if present
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                # Execute tool calls concurrently
                with ThreadPoolExecutor() as executor:
                    # Submit all tool calls to the executor
                    future_to_tool_call = {
                        executor.submit(self._execute_tool_call, tool_call): tool_call
                        for tool_call in assistant_message.tool_calls
                    }
                    
                    # Process results as they complete
                    for future in as_completed(future_to_tool_call):
                        tool_call = future_to_tool_call[future]
                        try:
                            future.result()
                        except Exception as exc:
                            self.console.print(f"[red]Tool '{tool_call.function.name}' generated an exception: {exc}[/red]")
            
            # Check if we should continue or stop
            if response.choices[0].finish_reason == "stop":
                break
            elif response.choices[0].finish_reason != "tool_calls":
                self.console.print(f"[red]Unexpected finish_reason: {response.choices[0].finish_reason}[/red]")
                break
    
    def _get_completion(self):
        """Get completion from the API"""
        tools_schema = self.tool_registry.get_all_schemas()
        
        return self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "claude-sonnet-4-20250514"),
            messages=self.messages,
            tools=tools_schema,
        )
    
    def _execute_tool_call(self, tool_call):
        """Execute a tool call"""
        tool_name = tool_call.function.name
        try:
            tool_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse tool arguments: {str(e)}"
            self.console.print(f"[red]Error: {error_msg}[/red]")
            self.console.print(f"[red]Raw arguments: {tool_call.function.arguments}[/red]")
            return tool_call.id, error_msg
        
        
        # Special handling for Task tool to show description
        if tool_name == "Task" and "description" in tool_args:
            self.console.print(f"\n[bold yellow]Executing {tool_name} ({tool_args['description']}):[/bold yellow]")
        else:
            self.console.print(f"\n[bold yellow]Executing {tool_name}:[/bold yellow]")
        
        # Special handling for certain tools
        if tool_name == "Bash":
            if "command" in tool_args:
                self.console.print(f"[dim]$ {tool_args['command']}[/dim]")
        
        try:
            # Execute the tool
            result = self.tool_registry.execute_tool(tool_name, **tool_args)
            
            # Display result based on tool type
            if tool_name in ["Read", "Grep", "LS"]:
                # Use syntax highlighting for code-related output
                if "Error:" not in result:
                    syntax = Syntax(result, "python", theme="monokai", line_numbers=False)
                    self.console.print(Panel(syntax, title=f"[yellow]{tool_name} Output", border_style="yellow"))
                else:
                    self.console.print(Panel(result, title=f"[red]{tool_name} Error", border_style="red"))
            else:
                # Regular output
                self.console.print(Panel(result, title=f"[yellow]{tool_name} Output", border_style="yellow", expand=False))
            
            
            # Add tool result to messages
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
            
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            self.console.print(f"[red]{error_msg}[/red]")
            
            
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": error_msg
            })
    
    def _display_assistant_message(self, content: str):
        """Display assistant message with proper formatting"""
        # Use Markdown rendering for better formatting
        md = Markdown(content)
        self.console.print(Panel(md, title="[bold blue]Assistant", border_style="blue"))
    
    def interactive_mode(self):
        """Run in interactive mode"""
        self.console.print("[bold green]Klaude - AI Coding Assistant[/bold green]")
        self.console.print("Type 'exit' or 'quit' to end the session.\n")
        
        while True:
            try:
                prompt = self.console.input("[bold green]You:[/bold green] ")
                
                if prompt.lower() in ['exit', 'quit']:
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if prompt.strip():
                    self.run(prompt)
                    self.console.print()  # Add spacing between interactions
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")