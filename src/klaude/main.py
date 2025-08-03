#!/usr/bin/env python3
"""
File: main.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: CLI entry point for Klaude assistant

This file is part of the klaude project.
"""

import click
from klaude.agent import Agent


@click.command()
@click.option('-p', '--prompt', help='User prompt for the agent (non-interactive mode)')
@click.option('-i', '--interactive', is_flag=True, help='Run in interactive mode')
def main(prompt: str = None, interactive: bool = False):
    """Klaude - AI Coding Assistant
    
    Run with -p for single prompt or -i for interactive mode.
    """
    agent = Agent()
    
    if interactive or not prompt:
        # Run in interactive mode
        agent.interactive_mode()
    else:
        # Run single prompt
        agent.run(prompt)


if __name__ == '__main__':
    main()