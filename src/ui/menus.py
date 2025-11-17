"""Menu components for Camel TUI"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, ListItem, ListView, Label
from textual.screen import ModalScreen


class ModelSwitcher(ModalScreen):
    """Model switching overlay"""

    CSS = """
    ModelSwitcher {
        align: center middle;
    }

    #model-dialog {
        width: 60;
        height: auto;
        background: #161b22;
        border: thick #30363d;
        padding: 1 2;
    }

    #model-list {
        height: auto;
        max-height: 15;
        background: #0d1117;
        border: solid #30363d;
    }

    .model-item {
        padding: 0 1;
        color: #c9d1d9;
    }

    .model-item:hover {
        background: #21262d;
    }

    .current-model {
        color: #56d364;
    }

    .model-header {
        color: #58a6ff;
        text-style: bold;
    }
    """

    def __init__(self, models: list, current_model: str):
        super().__init__()
        self.models = models
        self.current_model = current_model

    def compose(self) -> ComposeResult:
        with Container(id="model-dialog"):
            yield Label("Select Model (↑↓ to navigate, Enter to select, Esc to cancel)", classes="model-header")
            yield ListView(
                *[
                    ListItem(
                        Label(
                            f"{'● ' if m['name'] == self.current_model else '  '}{m['name']} ({m['size']})",
                            classes="current-model" if m['name'] == self.current_model else "model-item"
                        ),
                        id=f"model-{i}"
                    )
                    for i, m in enumerate(self.models)
                ],
                id="model-list"
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle model selection"""
        idx = int(event.item.id.split("-")[1])
        selected_model = self.models[idx]["name"]
        self.dismiss(selected_model)

    def on_key(self, event) -> None:
        """Handle escape key"""
        if event.key == "escape":
            self.dismiss(None)


class ServerSwitcher(ModalScreen):
    """Server switching overlay"""

    CSS = """
    ServerSwitcher {
        align: center middle;
    }

    #server-dialog {
        width: 70;
        height: auto;
        background: #161b22;
        border: thick #30363d;
        padding: 1 2;
    }

    #server-list {
        height: auto;
        max-height: 12;
        background: #0d1117;
        border: solid #30363d;
    }

    .server-item {
        padding: 0 1;
        color: #c9d1d9;
    }

    .server-item:hover {
        background: #21262d;
    }

    .current-server {
        color: #56d364;
    }

    .server-header {
        color: #58a6ff;
        text-style: bold;
    }

    .server-online {
        color: #56d364;
    }

    .server-offline {
        color: #f85149;
    }
    """

    def __init__(self, servers: list, current_endpoint: str):
        super().__init__()
        self.servers = servers
        self.current_endpoint = current_endpoint

    def compose(self) -> ComposeResult:
        with Container(id="server-dialog"):
            yield Label("Select Server (↑↓ to navigate, Enter to select, Esc to cancel)", classes="server-header")
            yield ListView(
                *[
                    ListItem(
                        Label(
                            f"{'● ' if s['endpoint'] == self.current_endpoint else '  '}{s['name']} - {s['endpoint']}",
                            classes="current-server" if s['endpoint'] == self.current_endpoint else "server-item"
                        ),
                        id=f"server-{i}"
                    )
                    for i, s in enumerate(self.servers)
                ],
                id="server-list"
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle server selection"""
        idx = int(event.item.id.split("-")[1])
        selected_server = self.servers[idx]
        self.dismiss(selected_server)

    def on_key(self, event) -> None:
        """Handle escape key"""
        if event.key == "escape":
            self.dismiss(None)


class ToolsReference(ModalScreen):
    """Tools reference overlay"""

    CSS = """
    ToolsReference {
        align: center middle;
    }

    #tools-dialog {
        width: 80;
        height: 30;
        background: #161b22;
        border: thick #30363d;
        padding: 1 2;
    }

    #tools-content {
        height: 100%;
        background: #0d1117;
        border: solid #30363d;
        padding: 1;
    }

    .tool-header {
        color: #58a6ff;
        text-style: bold;
    }

    .tool-name {
        color: #56d364;
        text-style: bold;
    }

    .tool-desc {
        color: #c9d1d9;
    }

    .tool-example {
        color: #d29922;
    }
    """

    TOOLS_INFO = [
        {
            "name": "Read",
            "desc": "Read file contents",
            "usage": "Read(file_path='/path/to/file', offset=0, limit=100)",
            "example": "Read(file_path='src/main.py')"
        },
        {
            "name": "Write",
            "desc": "Write content to file",
            "usage": "Write(file_path='/path/to/file', content='text')",
            "example": "Write(file_path='test.txt', content='Hello world')"
        },
        {
            "name": "Edit",
            "desc": "Replace text in file",
            "usage": "Edit(file_path='/path/to/file', old_string='old', new_string='new')",
            "example": "Edit(file_path='config.py', old_string='DEBUG=False', new_string='DEBUG=True')"
        },
        {
            "name": "Glob",
            "desc": "Find files by pattern",
            "usage": "Glob(pattern='**/*.py', path='/search/dir')",
            "example": "Glob(pattern='**/*.md')"
        },
        {
            "name": "Grep",
            "desc": "Search file contents",
            "usage": "Grep(pattern='search_term', path='/search/dir', output_mode='files_with_matches')",
            "example": "Grep(pattern='def main', output_mode='content')"
        },
        {
            "name": "Bash",
            "desc": "Execute shell command",
            "usage": "Bash(command='ls -la', timeout=5000)",
            "example": "Bash(command='git status')"
        },
        {
            "name": "Todo",
            "desc": "Manage task list",
            "usage": "Todo(action='list|add|complete', task='description')",
            "example": "Todo(action='add', task='Implement feature X')"
        }
    ]

    def compose(self) -> ComposeResult:
        with Container(id="tools-dialog"):
            yield Label("Available Tools (Esc to close)", classes="tool-header")
            content_text = "\n".join([
                f"{t['name']} - {t['desc']}\n  Usage: {t['usage']}\n  Example: {t['example']}\n"
                for t in self.TOOLS_INFO
            ])
            with Vertical(id="tools-content"):
                yield Static(content_text)

    def on_key(self, event) -> None:
        """Handle escape key"""
        if event.key == "escape":
            self.dismiss()
