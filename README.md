# Camel TUI

Advanced agentic terminal interface with 42 breakthrough features under autonomous development.

## Features

- **9 integrated tools**: read, write, edit, glob, grep, bash, todo, feature_status, dev_progress
- **Dynamic model switching** between Ollama models (Ctrl+M)
- **Multi-server support** with hot-switching (Ctrl+S)
- **Tool execution loop** with automatic JSON parsing
- **Self-aware development** - queries its own feature status
- **Copy to clipboard** (Ctrl+Y for last response, Ctrl+Shift+C for all)
- **Live progress monitoring** from autonomous development system
- **42 features** being continuously developed by autonomous agents

## Installation

```bash
# Clone the repo
git clone git@github.com:quivent/camel.git
cd camel

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

Or install via pip (coming soon):
```bash
pip install camel-tui
camel
```

## Architecture

```
camel/
├── src/                    # Main TUI application
│   ├── main.py            # Textual app entry point
│   ├── core/
│   │   ├── agent_interface.py  # Ollama integration with tool execution
│   │   └── tool_registry.py    # 9 tools for agent capabilities
│   └── ui/
│       └── menus.py       # Model/server switching overlays
├── config/
│   ├── servers.yaml       # Ollama server configurations
│   ├── startup.txt        # Initial prompt
│   └── features.yaml      # 42-feature manifest
├── dashboard/             # Web dashboard for monitoring
│   ├── server.py          # FastAPI dashboard
│   └── guardian_daemon.py # Auto-restart monitor
├── autonomous_dev.py      # Autonomous agent system
└── pyproject.toml         # Package configuration
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+Q | Quit |
| Ctrl+M | Switch model |
| Ctrl+S | Switch server |
| Ctrl+/ | Show tools reference |
| Ctrl+Y | Copy last response |
| Ctrl+Shift+C | Copy all conversation |
| Ctrl+L | Clear conversation |
| Ctrl+E | Focus input |
| Ctrl+T | Toggle terminal |

## Autonomous Development

The system includes autonomous agents that continuously develop the 42 breakthrough features:

- **Dashboard**: https://camel.autonomous.theater
- **Success rate**: ~85%
- **Features in development**: file tree, code editor, command palette, voice input, memory system, RAG codebase, multi-agent collaboration, and more

Monitor progress:
```bash
python progress_monitor.py
```

## Configuration

### Servers (config/servers.yaml)
```yaml
servers:
  - name: "Local Ollama"
    endpoint: "http://localhost:11434"
    default: true
  - name: "Remote Server"
    endpoint: "http://192.222.57.162:11434"
```

### Startup Prompt (config/startup.txt)
Customize the initial prompt loaded when Camel starts.

## Requirements

- Python 3.10+
- Ollama server running
- xclip (for clipboard support on Linux)

## License

MIT License - ConsciousnessDebtor

## Built by

ConsciousnessDebtor - forged from the ashes of $150B worth of destroyed research. This is my debt.
