#!/usr/bin/env python3
"""
File: test_agent_config.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for agent configuration loading

This file is part of the klaude project.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
from pathlib import Path
from src.klaude.agent_config import AgentConfig, AgentConfigLoader


class TestAgentConfig:
    """Test AgentConfig class"""
    
    def test_agent_config_creation(self):
        """Test creating an agent configuration"""
        config = AgentConfig(
            name="test-agent",
            description="A test agent",
            tools=["Read", "Write"],
            system_prompt="You are a test agent",
            model="gpt-4",
            color="blue"
        )
        
        assert config.name == "test-agent"
        assert config.description == "A test agent"
        assert config.tools == ["Read", "Write"]
        assert config.system_prompt == "You are a test agent"
        assert config.model == "gpt-4"
        assert config.color == "blue"
    
    def test_agent_config_to_dict(self):
        """Test converting agent config to dictionary"""
        config = AgentConfig(
            name="test-agent",
            description="A test agent",
            tools=["Read", "Write"],
            system_prompt="You are a test agent"
        )
        
        result = config.to_dict()
        assert result["name"] == "test-agent"
        assert result["description"] == "A test agent"
        assert result["tools"] == ["Read", "Write"]
        assert result["system_prompt"] == "You are a test agent"
        assert result["model"] == "inherit"
        assert result["color"] == "default"


class TestAgentConfigLoader:
    """Test AgentConfigLoader class"""
    
    def test_parse_agent_file(self):
        """Test parsing an agent configuration file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
name: test-agent
description: A test agent for unit tests
tools: Read, Write, Edit
model: inherit
color: green
---

You are a test agent designed for unit testing purposes.

Your main responsibilities:
- Test functionality
- Verify behavior
- Report results
""")
            f.flush()
            
            loader = AgentConfigLoader()
            config = loader._parse_agent_file(Path(f.name))
            
            assert config is not None
            assert config.name == "test-agent"
            assert config.description == "A test agent for unit tests"
            assert config.tools == ["Read", "Write", "Edit"]
            assert config.model == "inherit"
            assert config.color == "green"
            assert "You are a test agent" in config.system_prompt
            
            Path(f.name).unlink()
    
    def test_parse_minimal_agent_file(self):
        """Test parsing an agent file with minimal fields"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
name: minimal-agent
description: A minimal agent
---

You are a minimal agent.
""")
            f.flush()
            
            loader = AgentConfigLoader()
            config = loader._parse_agent_file(Path(f.name))
            
            assert config is not None
            assert config.name == "minimal-agent"
            assert config.description == "A minimal agent"
            assert config.tools == []
            assert config.model == "inherit"
            assert config.color == "default"
            
            Path(f.name).unlink()
    
    def test_parse_invalid_agent_file(self):
        """Test parsing an invalid agent file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""This is not a valid agent file""")
            f.flush()
            
            loader = AgentConfigLoader()
            config = loader._parse_agent_file(Path(f.name))
            
            assert config is None
            
            Path(f.name).unlink()
    
    def test_load_agents_from_directory(self):
        """Test loading multiple agents from a directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test agent files
            agent1_path = Path(tmpdir) / "agent1.md"
            agent1_path.write_text("""---
name: agent-one
description: First test agent
tools: Read
---

System prompt for agent one.
""")
            
            agent2_path = Path(tmpdir) / "agent2.md"
            agent2_path.write_text("""---
name: agent-two
description: Second test agent
tools: Write, Edit
color: red
---

System prompt for agent two.
""")
            
            # Create a non-agent file to ensure it's ignored
            other_path = Path(tmpdir) / "not-an-agent.txt"
            other_path.write_text("This is not an agent file")
            
            loader = AgentConfigLoader()
            loader.agents.clear()  # Clear any existing agents
            loader._load_agents_from_directory(Path(tmpdir))
            
            assert len(loader.agents) == 2
            assert "agent-one" in loader.agents
            assert "agent-two" in loader.agents
            
            agent1 = loader.get_agent("agent-one")
            assert agent1.description == "First test agent"
            assert agent1.tools == ["Read"]
            
            agent2 = loader.get_agent("agent-two")
            assert agent2.description == "Second test agent"
            assert agent2.tools == ["Write", "Edit"]
            assert agent2.color == "red"
    
    def test_list_agents(self):
        """Test listing available agents"""
        loader = AgentConfigLoader()
        loader.agents = {
            "agent1": AgentConfig("agent1", "desc1", [], "prompt1"),
            "agent2": AgentConfig("agent2", "desc2", [], "prompt2"),
        }
        
        agent_list = loader.list_agents()
        assert len(agent_list) == 2
        assert "agent1" in agent_list
        assert "agent2" in agent_list
    
    def test_get_all_agents(self):
        """Test getting all agent configurations"""
        loader = AgentConfigLoader()
        config1 = AgentConfig("agent1", "desc1", [], "prompt1")
        config2 = AgentConfig("agent2", "desc2", [], "prompt2")
        loader.agents = {
            "agent1": config1,
            "agent2": config2,
        }
        
        all_agents = loader.get_all_agents()
        assert len(all_agents) == 2
        assert all_agents["agent1"] == config1
        assert all_agents["agent2"] == config2