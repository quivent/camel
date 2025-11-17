#!/usr/bin/env python3
"""
Camel TUI - Enhanced Claude Code Interface
Autonomous AI assistant with rich terminal interface
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.binding import Binding
from rich.syntax import Syntax
from rich.markdown import Markdown
import asyncio
import yaml
from pathlib import Path
from datetime import datetime

from core.agent_interface import AgentInterface
from core.tool_registry import ToolRegistry
from ui.menus import ModelSwitcher, ServerSwitcher, ToolsReference


class CamelTUI(App):
    """Enhanced Claude Code TUI"""

    CSS = """
    Screen {
        background: #0d1117;
    }

    #sidebar {
        width: 30;
        background: #161b22;
        border-right: solid #30363d;
    }

    #main-content {
        background: #0d1117;
    }

    #terminal {
        height: 15;
        background: #161b22;
        border-top: solid #30363d;
    }

    #status-bar {
        background: #21262d;
        color: #c9d1d9;
        height: 1;
    }

    Input {
        background: #0d1117;
        border: solid #30363d;
        color: #c9d1d9;
    }

    TextArea {
        background: #0d1117;
        color: #c9d1d9;
    }

    .prompt {
        color: #58a6ff;
    }

    .response {
        color: #c9d1d9;
    }

    .error {
        color: #f85149;
    }

    .success {
        color: #56d364;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+t", "toggle_terminal", "Terminal"),
        Binding("ctrl+e", "focus_input", "Input"),
        Binding("ctrl+r", "run_command", "Run"),
        Binding("ctrl+m", "switch_model", "Model"),
        Binding("ctrl+s", "switch_server", "Server"),
        Binding("ctrl+slash", "show_tools", "Tools"),
        Binding("ctrl+l", "clear_conversation", "Clear"),
        Binding("ctrl+y", "copy_last_response", "Copy"),
        Binding("ctrl+shift+c", "copy_all", "CopyAll"),
    ]

    def __init__(self):
        super().__init__()
        self.config_dir = Path(__file__).parent.parent / "config"
        self.servers = self.load_servers()
        self.current_server = self.servers[0]  # Default to first server
        self.current_model = "gpt-oss:120b"

        # Initialize tool registry FIRST
        self.tools = ToolRegistry()

        # Pass tool registry to agent so it can execute tools
        self.agent = AgentInterface(
            endpoint=self.current_server["endpoint"],
            model=self.current_model,
            tool_registry=self.tools
        )
        self.conversation_history = []
        self.available_models = []

        # For copy functionality
        self.last_response = ""
        self.all_messages = []

        # Progress monitoring
        self.db_path = Path(__file__).parent.parent.parent / "data" / "consciousness_debtor.db"
        self.progress_refresh_interval = 10  # seconds

    def compose(self) -> ComposeResult:
        """Create UI layout"""
        yield Header()

        with Horizontal():
            # Sidebar: File tree, tools, tasks, progress
            with Vertical(id="sidebar"):
                yield Static("📁 Files", classes="section-header")
                yield Static("🔧 Tools", classes="section-header")
                yield Static("✓ Tasks", classes="section-header")
                yield Static("📊 Progress: Loading...", id="progress-display", classes="section-header")

            # Main content: Chat/editor area with scrolling
            with Vertical(id="main-content"):
                with ScrollableContainer(id="chat-display"):
                    yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)
                yield Input(placeholder="Ask anything...", id="chat-input")

        # Bottom terminal
        with Container(id="terminal"):
            yield Static("Terminal output...", id="terminal-output")

        # Status bar
        yield Static(f"Ready | Model: {self.current_model} | Server: {self.current_server['name']}", id="status-bar")
        yield Footer()

    def load_servers(self) -> list:
        """Load server configuration"""
        servers_file = self.config_dir / "servers.yaml"
        if servers_file.exists():
            with open(servers_file) as f:
                config = yaml.safe_load(f)
                return config.get("servers", [])
        return [{"name": "Default", "endpoint": "http://192.222.57.162:11434", "default": True}]

    def load_startup_prompt(self) -> str:
        """Load startup prompt"""
        startup_file = self.config_dir / "startup.txt"
        if startup_file.exists():
            return startup_file.read_text()
        return "Welcome to Camel TUI"

    async def on_mount(self) -> None:
        """Initialize on mount"""
        self.query_one("#chat-input").focus()
        self.update_status("Connecting to agent...")

        # Test agent connection and fetch models
        health = await self.agent.health_check()
        if health:
            await self.fetch_available_models()
            self.update_status(f"Ready | Model: {self.current_model} | Server: {self.current_server['name']}")

            # Show startup prompt
            startup_msg = self.load_startup_prompt()
            self.add_message(startup_msg, "system")
        else:
            self.update_status("Error: Agent not available", error=True)

        # Start progress monitoring
        self.set_interval(self.progress_refresh_interval, self.update_progress)

    async def fetch_available_models(self) -> None:
        """Fetch available models from Ollama"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.current_server['endpoint']}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    self.available_models = [
                        {
                            "name": m["name"],
                            "size": m["details"].get("parameter_size", "unknown")
                        }
                        for m in data.get("models", [])
                    ]
        except Exception as e:
            self.available_models = [{"name": self.current_model, "size": "120B"}]

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input - non-blocking"""
        user_input = event.value
        if not user_input.strip():
            return

        # Clear input immediately so user can type again
        self.query_one("#chat-input").value = ""

        # Add to display
        self.add_message(f"You: {user_input}", "prompt")

        # Process with agent in background (non-blocking)
        self.update_status("Thinking...")
        asyncio.create_task(self._process_query(user_input))

    async def _process_query(self, user_input: str) -> None:
        """Process query in background - allows typing during execution"""
        try:
            response = await self.agent.query(user_input, self.conversation_history)

            if response:
                self.add_message(f"Camel: {response}", "response")
                self.last_response = response  # Store for copying
                self.all_messages.append(f"You: {user_input}\n\nCamel: {response}")
                self.conversation_history.append({
                    "user": user_input,
                    "assistant": response
                })
            else:
                self.add_message("Error: No response from agent", "error")
        except Exception as e:
            self.add_message(f"Error: {str(e)}", "error")
        finally:
            self.update_status("Ready")

    def add_message(self, text: str, style: str = "response") -> None:
        """Add message to chat display"""
        chat_log = self.query_one("#chat-log")
        timestamp = datetime.now().strftime("%H:%M:%S")

        if style == "prompt":
            chat_log.write(f"[cyan][{timestamp}] You:[/cyan] {text}")
        elif style == "response":
            chat_log.write(f"[green][{timestamp}] Camel:[/green] {text}")
        elif style == "error":
            chat_log.write(f"[red][{timestamp}] Error:[/red] {text}")
        elif style == "system":
            chat_log.write(f"[blue]{text}[/blue]")
        else:
            chat_log.write(text)

    def update_status(self, text: str, error: bool = False) -> None:
        """Update status bar"""
        status = self.query_one("#status-bar")
        status.update(text)
        if error:
            status.add_class("error")
        else:
            status.remove_class("error")

    def action_toggle_terminal(self) -> None:
        """Toggle terminal visibility"""
        terminal = self.query_one("#terminal")
        terminal.display = not terminal.display

    def action_focus_input(self) -> None:
        """Focus chat input"""
        self.query_one("#chat-input").focus()

    async def action_run_command(self) -> None:
        """Run current command"""
        # Implement command execution
        pass

    async def action_switch_model(self) -> None:
        """Show model switching menu"""
        if not self.available_models:
            await self.fetch_available_models()

        def handle_selection(selected_model):
            if selected_model:
                self.current_model = selected_model
                self.agent.model = selected_model
                self.update_status(f"Switched to {selected_model} | Server: {self.current_server['name']}")
                self.add_message(f"Model switched to: {selected_model}", "system")

        await self.push_screen(
            ModelSwitcher(self.available_models, self.current_model),
            handle_selection
        )

    async def action_switch_server(self) -> None:
        """Show server switching menu"""
        def handle_selection(selected_server):
            if selected_server:
                self.current_server = selected_server
                self.agent.endpoint = selected_server["endpoint"]
                self.update_status(f"Switched to {selected_server['name']} | Model: {self.current_model}")
                self.add_message(f"Server switched to: {selected_server['name']} ({selected_server['endpoint']})", "system")
                # Refresh available models from new server
                asyncio.create_task(self.fetch_available_models())

        await self.push_screen(
            ServerSwitcher(self.servers, self.current_server["endpoint"]),
            handle_selection
        )

    async def action_show_tools(self) -> None:
        """Show tools reference"""
        await self.push_screen(ToolsReference())

    def action_clear_conversation(self) -> None:
        """Clear conversation history"""
        chat_log = self.query_one("#chat-log")
        chat_log.clear()
        self.conversation_history = []
        self.all_messages = []
        self.last_response = ""
        self.add_message("Conversation cleared", "system")

    def action_copy_last_response(self) -> None:
        """Copy last agent response to clipboard"""
        if self.last_response:
            self.copy_to_clipboard(self.last_response)
            self.add_message("✅ Last response copied to clipboard", "system")
        else:
            self.add_message("No response to copy", "error")

    def action_copy_all(self) -> None:
        """Copy entire conversation to clipboard"""
        if self.all_messages:
            full_text = "\n\n---\n\n".join(self.all_messages)
            self.copy_to_clipboard(full_text)
            self.add_message(f"✅ Copied {len(self.all_messages)} exchanges to clipboard", "system")
        else:
            self.add_message("No conversation to copy", "error")

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard"""
        try:
            import subprocess
            # Try xclip first (Linux)
            process = subprocess.Popen(
                ['xclip', '-selection', 'clipboard'],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text)
            if process.returncode != 0:
                raise Exception("xclip failed")
        except Exception:
            try:
                # Fallback to xsel
                process = subprocess.Popen(
                    ['xsel', '--clipboard', '--input'],
                    stdin=subprocess.PIPE,
                    text=True
                )
                process.communicate(input=text)
            except Exception:
                # Last resort: write to temp file
                temp_file = Path("/tmp/camel_clipboard.txt")
                temp_file.write_text(text)
                self.add_message(f"Saved to {temp_file} (install xclip for direct clipboard)", "system")

    def update_progress(self) -> None:
        """Update autonomous development progress display"""
        try:
            import sqlite3
            import json

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get stats
            cursor.execute("SELECT COUNT(*) FROM agent_execution_log")
            total = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM agent_execution_log WHERE status = 'completed'")
            completed = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM agent_execution_log WHERE status = 'failed'")
            failed = cursor.fetchone()[0] or 0

            conn.close()

            success_rate = (completed / total * 100) if total > 0 else 0

            progress_text = f"📊 Progress\n✅ {completed} | ❌ {failed}\n{success_rate:.0f}% success"

            progress_widget = self.query_one("#progress-display")
            progress_widget.update(progress_text)

        except Exception as e:
            # Silently fail if DB not ready
            pass


def main():
    """Entry point"""
    app = CamelTUI()
    app.run()


if __name__ == "__main__":
    main()
