# Klaude

An experimental reproduction work of Claude Code

## Setup & Run

`.env` file format:

```
OPENAI_BASE_URL=...
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=...
GOOGLE_SEARCH_KEY=...
```

Run command:

```
uv venv
uv run klaude -p "hi"
```

Output:

```
uv run klaude -p "hi"
╭──────────────────────────────────────── User ─────────────────────────────────────────╮
│ hi                                                                                    │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────── Assistant ──────────────────────────────────────╮
│ Hello! How can I help you today?                                                      │
╰───────────────────────────────────────────────────────────────────────────────────────╯
```

Or run in interactive mode:

```
uv run klaude -i
```

## Examples

Interactive logs and examples of parallel and serial execution using sub-agents can be found in the `docs` folder.
