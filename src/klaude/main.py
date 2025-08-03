#!/usr/bin/env python3
"""
File: main.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: CLI entry point for Klaude assistant

This file is part of the klaude project.
"""

import click
import asyncio
import threading
from klaude.agent import Agent
from klaude.websocket_server import start_server


def run_websocket_server(port: int, ws_manager_container: list):
    """Run WebSocket server in a separate thread"""
    async def start_ws_server():
        ws_manager = await start_server(port)
        ws_manager_container.append(ws_manager)
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    
    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_ws_server())


@click.command()
@click.option('-p', '--prompt', help='User prompt for the agent (non-interactive mode)')
@click.option('-i', '--interactive', is_flag=True, help='Run in interactive mode')
@click.option('--no-web', is_flag=True, help='Disable web interface')
@click.option('--port', default=8080, help='Port for web interface (default: 8080)')
def main(prompt: str = None, interactive: bool = False, no_web: bool = False, port: int = 8080):
    """Klaude - AI Coding Assistant
    
    Run with -p for single prompt or -i for interactive mode.
    """
    ws_manager = None
    
    # Start WebSocket server in separate thread unless disabled
    if not no_web:
        ws_manager_container = []
        ws_thread = threading.Thread(
            target=run_websocket_server,
            args=(port, ws_manager_container),
            daemon=True
        )
        ws_thread.start()
        
        # Wait for WebSocket server to start
        import time
        timeout = 5
        start_time = time.time()
        while not ws_manager_container and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if ws_manager_container:
            ws_manager = ws_manager_container[0]
        else:
            print("Warning: WebSocket server failed to start")
    
    # Create agent with WebSocket manager
    agent = Agent(ws_manager)
    
    if interactive or not prompt:
        # Run in interactive mode
        agent.interactive_mode()
    else:
        # Run single prompt
        agent.run(prompt)


if __name__ == '__main__':
    main()