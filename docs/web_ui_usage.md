# Web UI Usage Guide

The Klaude assistant now includes a real-time web interface that displays conversation history and tool execution details.

## Features

1. **Real-time Updates**: All conversations and tool calls are displayed in real-time
2. **Tool Call Visualization**: See input parameters and output results for each tool
3. **Nested Task Support**: TaskTool sub-agent calls are displayed in a nested structure
4. **Session Persistence**: Refreshing the page restores the current session history
5. **Responsive Design**: Works on desktop and mobile devices

## Running with Web UI

### Default mode (with web UI on port 8080):
```bash
uv run klaude -i
```

### Custom port:
```bash
uv run klaude -i --port 8888
```

### Disable web UI:
```bash
uv run klaude -i --no-web
```

### Single prompt mode with web UI:
```bash
uv run klaude -p "List all Python files"
```

## Accessing the Web UI

1. Start Klaude with web UI enabled (default)
2. Open http://localhost:8080 in your browser
3. The interface will automatically connect and display the conversation

## Interface Components

- **Header**: Shows connection status and application title
- **Conversation Area**: Displays messages and tool calls
- **Tool Calls**: Expandable/collapsible sections showing:
  - Tool name and description
  - Input parameters (JSON formatted)
  - Execution status (running/completed/error)
  - Output results
- **Footer**: Shows current session ID

## Testing the Web UI

Run the test script to see all features in action:
```bash
uv run python test_web_ui.py
```

This will demonstrate:
- Simple message exchanges
- Tool execution with parameters and results
- Multiple concurrent tool calls
- Nested task execution with sub-agents