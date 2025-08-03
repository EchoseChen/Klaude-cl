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
from typing import List, Dict, Any
from openai import OpenAI
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
    
    def __init__(self):
        self.console = Console()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_tools()
        
        # Initialize message history
        self.messages: List[Dict[str, Any]] = []
        
        # Add system message
        self.messages.append({
            "role": "system",
            "content": self._get_system_prompt()
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
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return """You are Klaude, an AI coding assistant similar to Claude Code.

You are an interactive CLI tool that helps users with software engineering tasks. Use the available tools to assist the user.

Key principles:
- Be concise and direct in your responses
- Minimize output tokens while maintaining helpfulness
- Use tools proactively when appropriate
- Follow existing code conventions in the project
- Prioritize readability and maintainability

When working with code:
- Always read files before editing them
- Follow existing patterns and conventions
- Never create files unless necessary
- Prefer editing existing files over creating new ones

Tool usage:
- You can call multiple tools in a single response for better performance
- Use the Task tool for complex multi-step operations
- Use TodoWrite to track progress on complex tasks
- Always check file contents with Read before using Edit or MultiEdit

Remember to be helpful while keeping responses brief and to the point."""
    
    def run(self, prompt: str):
        """Run the agent with a user prompt"""
        self.console.print(Panel(prompt, title="[bold green]User", border_style="green"))
        self.messages.append({"role": "user", "content": prompt})
        
        while True:
            response = self._get_completion()
            
            if response.choices[0].finish_reason == "stop":
                assistant_message = response.choices[0].message
                self.messages.append(assistant_message.model_dump())
                
                if assistant_message.content:
                    self._display_assistant_message(assistant_message.content)
                break
            
            elif response.choices[0].finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                self.messages.append(assistant_message.model_dump())
                
                if assistant_message.content:
                    self._display_assistant_message(assistant_message.content)
                
                # Execute tool calls
                for tool_call in assistant_message.tool_calls:
                    self._execute_tool_call(tool_call)
            
            else:
                self.console.print("[red]Unexpected response from API[/red]")
                break
    
    def _get_completion(self):
        """Get completion from the API"""
        tools_schema = self.tool_registry.get_all_schemas()
        
        return self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
            messages=self.messages,
            tools=tools_schema,
            temperature=0
        )
    
    def _execute_tool_call(self, tool_call):
        """Execute a tool call"""
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
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