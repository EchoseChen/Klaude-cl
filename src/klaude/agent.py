import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
from klaude.tools import BashTool

# 加载.env文件
load_dotenv()


class Agent:
    def __init__(self):
        self.console = Console()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.tools = {
            "bash": BashTool()
        }
        self.messages: List[Dict[str, Any]] = []
    
    def run(self, prompt: str):
        self.console.print(f"[bold green]User:[/bold green] {prompt}")
        self.messages.append({"role": "user", "content": prompt})
        
        while True:
            response = self._get_completion()
            
            if response.choices[0].finish_reason == "stop":
                assistant_message = response.choices[0].message
                self.messages.append(assistant_message.model_dump())
                
                if assistant_message.content:
                    self.console.print("\n[bold blue]Assistant:[/bold blue]")
                    self.console.print(Markdown(assistant_message.content))
                break
            
            elif response.choices[0].finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                self.messages.append(assistant_message.model_dump())
                
                if assistant_message.content:
                    self.console.print("\n[bold blue]Assistant:[/bold blue]")
                    self.console.print(Markdown(assistant_message.content))
                
                for tool_call in assistant_message.tool_calls:
                    self._execute_tool_call(tool_call)
            
            else:
                self.console.print("[red]Unexpected response from API[/red]")
                break
    
    def _get_completion(self):
        tools_schema = [tool.to_function_schema() for tool in self.tools.values()]
        
        return self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
            messages=self.messages,
            tools=tools_schema,
            temperature=0
        )
    
    def _execute_tool_call(self, tool_call):
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        self.console.print(f"\n[bold yellow]Executing {tool_name}:[/bold yellow]")
        
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            
            if tool_name == "bash":
                self.console.print(f"[dim]$ {tool_args['command']}[/dim]")
                result = tool.execute(**tool_args)
            else:
                result = tool.execute(**tool_args)
            
            self.console.print(f"[dim]{result}[/dim]")
            
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
        else:
            error_msg = f"Unknown tool: {tool_name}"
            self.console.print(f"[red]{error_msg}[/red]")
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": error_msg
            })