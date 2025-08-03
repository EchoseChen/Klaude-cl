#!/usr/bin/env python3
"""
File: agent_config.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Agent configuration loader for custom sub-agents

This file is part of the klaude project.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class AgentConfig:
    """Represents a custom agent configuration"""
    
    def __init__(self, name: str, description: str, tools: List[str], 
                 system_prompt: str, model: str = "inherit", color: str = "default"):
        self.name = name
        self.description = description
        self.tools = tools
        self.system_prompt = system_prompt
        self.model = model
        self.color = color
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "color": self.color
        }


class AgentConfigLoader:
    """Loads custom agent configurations from files"""
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self._load_agents()
    
    def _load_agents(self):
        """Load agents from both global and project directories"""
        # Global agents directory
        global_dir = Path.home() / ".claude" / "agents"
        if global_dir.exists() and global_dir.is_dir():
            self._load_agents_from_directory(global_dir)
        
        # Project agents directory
        project_dir = Path.cwd() / ".claude" / "agents"
        if project_dir.exists() and project_dir.is_dir():
            self._load_agents_from_directory(project_dir)
    
    def _load_agents_from_directory(self, directory: Path):
        """Load all agent configurations from a directory"""
        for file_path in directory.glob("*.md"):
            try:
                config = self._parse_agent_file(file_path)
                if config:
                    # Project configs override global configs with same name
                    self.agents[config.name] = config
            except Exception as e:
                print(f"Error loading agent config from {file_path}: {e}")
    
    def _parse_agent_file(self, file_path: Path) -> Optional[AgentConfig]:
        """Parse a single agent configuration file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by the header delimiter
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None
        
        # Parse the header section
        header = parts[1].strip()
        system_prompt = parts[2].strip()
        
        # Extract fields from header
        config_data = {}
        for line in header.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                config_data[key.strip()] = value.strip()
        
        # Validate required fields
        if 'name' not in config_data or 'description' not in config_data:
            return None
        
        # Parse tools list
        tools = []
        if 'tools' in config_data:
            tools = [t.strip() for t in config_data['tools'].split(',')]
        
        return AgentConfig(
            name=config_data['name'],
            description=config_data['description'],
            tools=tools,
            system_prompt=system_prompt,
            model=config_data.get('model', 'inherit'),
            color=config_data.get('color', 'default')
        )
    
    def get_agent(self, name: str) -> Optional[AgentConfig]:
        """Get an agent configuration by name"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all available agent names"""
        return list(self.agents.keys())
    
    def get_all_agents(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations"""
        return self.agents.copy()