#!/usr/bin/env python3
"""
File: websocket_server.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: WebSocket server for real-time conversation display

This file is part of the klaude project.
"""

import asyncio
import logging
from aiohttp import web
from typing import Dict, List, Any, Optional
import weakref
from datetime import datetime
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class ConversationHistory:
    """Manages conversation history and state"""
    
    def __init__(self, max_size: int = 1000):
        self.messages: List[Dict[str, Any]] = []
        self.max_size = max_size
        self.session_id = str(uuid.uuid4())
        
    def add_message(self, message: Dict[str, Any]):
        """Add a message to history with automatic trimming"""
        self.messages.append({
            **message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim old messages if exceeds max_size
        if len(self.messages) > self.max_size:
            self.messages = self.messages[-self.max_size:]
    
    def get_init_data(self) -> Dict[str, Any]:
        """Get initialization data for new connections"""
        return {
            "type": "init",
            "data": {
                "session_id": self.session_id,
                "history": self.messages
            }
        }


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self._websockets = weakref.WeakSet()
        self.history = ConversationHistory()
        self._loop = None  # Will be set when server starts
        
    async def handle_websocket(self, request):
        """Handle new WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._websockets.add(ws)
        
        try:
            # Send initialization data
            await ws.send_json(self.history.get_init_data())
            
            # Keep connection alive
            async for msg in ws:
                if msg.type == web.WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            return ws
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        # Add to history
        self.history.add_message(message)
        
        # Send to all connected clients
        if self._websockets:
            await asyncio.gather(
                *[ws.send_json(message) for ws in self._websockets],
                return_exceptions=True
            )
    
    async def send_user_message(self, content: str):
        """Send user message event"""
        await self.broadcast({
            "type": "user_message",
            "data": {
                "content": content
            }
        })
    
    async def send_assistant_message(self, content: str):
        """Send assistant message event"""
        await self.broadcast({
            "type": "assistant_message",
            "data": {
                "content": content
            }
        })
    
    async def send_tool_call(self, tool_name: str, tool_args: Dict[str, Any], 
                           tool_id: str, description: Optional[str] = None):
        """Send tool call event"""
        await self.broadcast({
            "type": "tool_call",
            "data": {
                "id": tool_id,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "description": description,
                "status": "running"
            }
        })
    
    async def send_tool_result(self, tool_id: str, result: str, 
                             error: Optional[str] = None):
        """Send tool result event"""
        await self.broadcast({
            "type": "tool_result",
            "data": {
                "id": tool_id,
                "result": result,
                "error": error,
                "status": "completed" if not error else "error"
            }
        })
    
    async def send_task_start(self, task_id: str, description: str, 
                            parent_task_id: Optional[str] = None):
        """Send task start event for nested tasks"""
        await self.broadcast({
            "type": "task_start",
            "data": {
                "id": task_id,
                "description": description,
                "parent_task_id": parent_task_id
            }
        })
    
    async def send_task_end(self, task_id: str):
        """Send task end event"""
        await self.broadcast({
            "type": "task_end",
            "data": {
                "id": task_id
            }
        })


async def serve_static(request):
    """Serve static files"""
    path = request.match_info.get('path', 'index.html')
    if not path:
        path = 'index.html'
    
    # Security: prevent directory traversal
    if '..' in path:
        return web.Response(status=403)
    
    static_dir = request.app['static_dir']
    file_path = static_dir / path
    
    if file_path.exists() and file_path.is_file():
        return web.FileResponse(file_path)
    else:
        return web.Response(status=404)


def create_app(static_dir: str, ws_manager: WebSocketManager) -> web.Application:
    """Create and configure the web application"""
    app = web.Application()
    app['static_dir'] = Path(static_dir)
    app['ws_manager'] = ws_manager
    
    # Routes
    app.router.add_get('/ws', ws_manager.handle_websocket)
    app.router.add_get('/', serve_static)
    app.router.add_get('/{path:.*}', serve_static)
    
    return app


async def start_server(port: int = 8080, static_dir: Optional[str] = None) -> WebSocketManager:
    """Start the WebSocket server"""
    if static_dir is None:
        # Default to static directory in the same folder
        import os
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    # Ensure static directory exists
    Path(static_dir).mkdir(exist_ok=True)
    
    ws_manager = WebSocketManager()
    # Store the event loop reference
    ws_manager._loop = asyncio.get_event_loop()
    
    app = create_app(static_dir, ws_manager)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"WebSocket server started at http://0.0.0.0:{port}")
    print(f"\n🌐 Web UI available at http://localhost:{port}")
    print(f"   (Also accessible from external devices at http://<your-ip>:{port})\n")
    
    return ws_manager