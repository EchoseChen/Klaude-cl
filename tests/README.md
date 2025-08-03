# Tools Implementation Tests

This directory contains comprehensive pytest tests for all tools implemented in `src/klaude/tools_impl.py`.

## Test Structure

- `test_tools_impl.py` - Main test file containing tests for all 14 tools
- `test_samples/` - Sample files used for testing various tools
  - `sample.py` - Python file with imports and functions
  - `test_import.py` - Python file with various import statements
  - `sample_notebook.ipynb` - Jupyter notebook for notebook tools testing
  - `subdir/nested.py` - Nested Python file for glob testing

## Running Tests

Run all tests:
```bash
uv run pytest tests/test_tools_impl.py -v
```

Run specific test class:
```bash
uv run pytest tests/test_tools_impl.py::TestGrepTool -v
```

Run with coverage:
```bash
uv run pytest tests/test_tools_impl.py --cov=src/klaude/tools_impl --cov-report=html
```

## Test Coverage

The test suite includes tests for:

1. **TaskTool** - Agent task launching
2. **BashTool** - Command execution with timeout support
3. **GlobTool** - File pattern matching
4. **GrepTool** - File content searching (with ripgrep and Python fallback)
5. **LSTool** - Directory listing with tree structure
6. **ReadTool** - File reading with line numbers
7. **EditTool** - Single string replacement in files
8. **MultiEditTool** - Multiple sequential edits
9. **WriteTool** - File writing with directory creation
10. **NotebookReadTool** - Jupyter notebook reading
11. **NotebookEditTool** - Jupyter notebook editing
12. **WebFetchTool** - URL content fetching
13. **TodoWriteTool** - Task list management
14. **WebSearchTool** - Web search functionality

## Integration Tests

The test suite includes integration tests that match the actual tool usage patterns from the trace files in `debug/traces/`. These tests ensure the tools behave exactly as expected in real usage scenarios.

## Test Design

Each tool test class includes:
- Tool creation and initialization tests
- Parameter schema validation
- Basic execution tests
- Error handling tests
- Edge case tests
- Integration tests matching real usage traces