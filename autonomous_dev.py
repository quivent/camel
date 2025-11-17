#!/usr/bin/env python3
"""
Real Autonomous Development System for Camel TUI
BULLETPROOF - Will not crash, will handle all errors, will continue running
"""

import asyncio
import httpx
import json
import time
import sqlite3
import sys
import traceback
from pathlib import Path
from datetime import datetime, UTC
from typing import List, Dict, Optional


OLLAMA_ENDPOINT = "http://192.222.57.162:11434"
MODEL = "phi3.5:3.8b-mini-instruct-fp16"  # Lightweight, fast responses


class DevelopmentAgent:
    """Real autonomous development agent - bulletproof"""

    def __init__(self, agent_id: str, task: Dict, project_root: Path):
        self.agent_id = agent_id
        self.task = task
        self.project_root = project_root
        self.status = "initialized"
        self.start_time = None
        self.end_time = None
        self.outputs = []
        self.client = httpx.AsyncClient(timeout=120.0)  # 2 minute timeout - FAST FAIL

    async def log(self, message: str):
        """Log agent activity - never crashes"""
        try:
            timestamp = datetime.now(UTC).isoformat()
            log_entry = {
                'agent_id': self.agent_id,
                'timestamp': timestamp,
                'message': message,
                'status': self.status
            }
            self.outputs.append(log_entry)
            print(f"[{self.agent_id}] {timestamp}: {message}", flush=True)
        except Exception as e:
            print(f"[{self.agent_id}] LOG ERROR: {e}", flush=True)

    async def read_file(self, filepath: str) -> str:
        """Read file from project - MINIMAL CONTEXT, never crashes"""
        try:
            path = self.project_root / filepath
            if path.exists():
                content = path.read_text()
                lines = content.split('\n')

                # CRITICAL: Only send first 50 lines to keep context small
                if len(lines) > 50:
                    return '\n'.join(lines[:50]) + f"\n\n... [TRUNCATED: {len(lines) - 50} more lines]"
                return content
            return f"File not found: {filepath}"
        except Exception as e:
            return f"Error reading {filepath}: {e}"

    async def write_file(self, filepath: str, content: str) -> bool:
        """Write file to project - never crashes"""
        try:
            path = self.project_root / filepath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            await self.log(f"Wrote {filepath}")
            return True
        except Exception as e:
            await self.log(f"Failed to write {filepath}: {e}")
            return False

    async def query_ollama(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Query Ollama with streaming for faster response - never crashes"""
        try:
            # Use streaming to avoid timeout issues
            async with self.client.stream(
                "POST",
                f"{OLLAMA_ENDPOINT}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": True,
                    "options": {
                        "num_predict": 500,  # MAX 500 tokens - keep it fast
                        "temperature": 0.7
                    }
                }
            ) as response:
                if response.status_code != 200:
                    await self.log(f"Ollama returned status {response.status_code}")
                    return None

                full_response = ""
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            full_response += token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            pass

                return full_response if full_response else None

        except Exception as e:
            await self.log(f"Ollama query failed: {e}")
            return None

    async def execute_task(self):
        """Execute the development task - NEVER CRASHES"""
        try:
            self.status = "running"
            self.start_time = datetime.now(UTC).isoformat()
            await self.log(f"Starting task: {self.task['name']}")

            # Build MINIMAL context - only first file, truncated
            file_context = ""
            files_to_read = self.task.get('files', [])[:1]  # MAX 1 file
            for filepath in files_to_read:
                content = await self.read_file(filepath)
                file_context += f"=== {filepath} (first 50 lines) ===\n{content}\n"

            # ULTRA COMPACT prompt - minimal tokens
            system_prompt = f"""Python dev. Camel TUI feature.

TASK: {self.task['description']}

CODE CONTEXT:
{file_context}

REQUIREMENTS:
- {chr(10).join('- ' + r for r in self.task.get('requirements', [])[:3])}

Give concise Python code only. No explanation."""

            prompt = f"Implement {self.task['name']}. Code only."

            await self.log("Querying Ollama for implementation...")
            response = await self.query_ollama(prompt, system_prompt)

            if response:
                await self.log(f"Received response: {len(response)} chars")

                # Store response
                self.outputs.append({
                    'type': 'implementation',
                    'content': response[:5000]  # Store first 5000 chars
                })
                self.status = "completed"
            else:
                await self.log("❌ No response from Ollama")
                self.status = "failed"

        except Exception as e:
            await self.log(f"FATAL ERROR in task execution: {e}")
            await self.log(f"Traceback: {traceback.format_exc()}")
            self.status = "failed"
        finally:
            self.end_time = datetime.now(UTC).isoformat()
            await self.log(f"Task {self.status}")

    async def close(self):
        """Cleanup - never crashes"""
        try:
            await self.client.aclose()
        except Exception as e:
            print(f"[{self.agent_id}] Error closing client: {e}", flush=True)


class AutonomousDevelopmentSystem:
    """Bulletproof autonomous development orchestrator - WILL NOT CRASH"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tasks = self.load_development_tasks()
        self.agents = []
        self.db_path = self.project_root.parent / "data" / "consciousness_debtor.db"
        self.cycle_count = 0
        self.total_completions = 0
        self.total_failures = 0

    def load_development_tasks(self) -> List[Dict]:
        """Load actual development tasks"""
        return [
            # CRITICAL PRIORITY - Core UX features
            {
                "name": "model_switching",
                "description": "Add clean menu for switching between available Ollama models",
                "priority": "critical",
                "files": ["src/main.py", "src/ui/menus.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Hidden menu accessible via keyboard shortcut (Ctrl+M)",
                    "List all available models from Ollama API",
                    "Show current model in status bar",
                    "Minimal UI footprint - dropdown or overlay menu",
                    "Persist selection across sessions"
                ]
            },
            {
                "name": "server_switching",
                "description": "Add capability to switch between Ollama server endpoints",
                "priority": "critical",
                "files": ["src/main.py", "src/core/agent_interface.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Hidden menu accessible via Ctrl+S",
                    "Define servers in config/servers.yaml",
                    "Test connection before switching",
                    "Show server status in status bar",
                    "Clean UX - minimal space usage"
                ]
            },
            {
                "name": "tools_menu",
                "description": "Create intuitive menu showing available tools and their usage",
                "priority": "critical",
                "files": ["src/main.py", "src/ui/menus.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Accessible via Ctrl+/ or clicking 'Tools' in sidebar",
                    "Show all 7 tools with descriptions and examples",
                    "Copy-paste ready tool syntax",
                    "Searchable/filterable tool list",
                    "Overlay panel that doesn't disrupt main UI"
                ]
            },
            {
                "name": "conversation_window",
                "description": "Extend conversation area with scrolling and history",
                "priority": "critical",
                "files": ["src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "ScrollableContainer for unlimited conversation history",
                    "Auto-scroll to bottom on new messages",
                    "Scroll up to view history",
                    "Message bubbles with timestamps",
                    "Clear conversation button (Ctrl+L)"
                ]
            },
            {
                "name": "startup_prompt",
                "description": "Initialize Camel with configurable startup prompt",
                "priority": "critical",
                "files": ["src/main.py", "config/startup.txt"],
                "agent_type": "Solver",
                "requirements": [
                    "Load startup prompt from config/startup.txt",
                    "Display in conversation on launch",
                    "User can edit config/startup.txt for custom initialization",
                    "Optional: skip with --no-init flag"
                ]
            },

            # HIGH PRIORITY - Productivity features
            {
                "name": "file_tree",
                "description": "Interactive file tree browser in sidebar",
                "priority": "high",
                "files": ["src/ui/file_tree.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Tree view of project directory",
                    "Expand/collapse folders",
                    "Click to view file contents",
                    "Show git status indicators (modified, untracked)",
                    "Filter by file type (.py, .js, etc)"
                ]
            },
            {
                "name": "code_editor",
                "description": "Inline code editor with syntax highlighting",
                "priority": "high",
                "files": ["src/ui/editor.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "TextArea widget with syntax highlighting",
                    "Open files from file tree",
                    "Save changes with Ctrl+S",
                    "Line numbers and current line highlight",
                    "Support Python, JavaScript, YAML, Markdown"
                ]
            },
            {
                "name": "command_palette",
                "description": "Quick command access like VS Code command palette",
                "priority": "high",
                "files": ["src/ui/command_palette.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Fuzzy search all commands (Ctrl+Shift+P)",
                    "Recent commands at top",
                    "Show keyboard shortcuts next to commands",
                    "Filter as you type",
                    "Execute command on Enter"
                ]
            },
            {
                "name": "agent_streaming",
                "description": "Stream agent responses token-by-token",
                "priority": "high",
                "files": ["src/core/agent_interface.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Use Ollama streaming API",
                    "Display tokens as they arrive",
                    "Show 'thinking...' indicator",
                    "Cancel mid-stream with Esc",
                    "Smooth scrolling as text appears"
                ]
            },
            {
                "name": "conversation_export",
                "description": "Export conversation history to markdown/JSON",
                "priority": "high",
                "files": ["src/tools/export.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Export to .md with formatted code blocks",
                    "Export to .json with full metadata",
                    "Save to ~/camel-exports/ directory",
                    "Include timestamps and model used",
                    "Ctrl+E to trigger export"
                ]
            },

            # MEDIUM PRIORITY - Advanced features
            {
                "name": "multi_tab_conversations",
                "description": "Multiple conversation tabs like browser tabs",
                "priority": "medium",
                "files": ["src/ui/tabs.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Create new tab with Ctrl+T",
                    "Switch tabs with Ctrl+1-9",
                    "Each tab has independent conversation",
                    "Tab shows first message as title",
                    "Close tab with Ctrl+W"
                ]
            },
            {
                "name": "code_execution",
                "description": "Execute Python/shell code directly in TUI",
                "priority": "medium",
                "files": ["src/tools/executor.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Detect code blocks in agent responses",
                    "Run button appears next to executable code",
                    "Execute in sandboxed subprocess",
                    "Show output inline with ANSI colors",
                    "Timeout after 30 seconds"
                ]
            },
            {
                "name": "vim_mode",
                "description": "Vim keybindings for navigation",
                "priority": "medium",
                "files": ["src/ui/vim_bindings.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Toggle with :set vim / :set normal",
                    "hjkl navigation in chat history",
                    "dd to delete message",
                    "yy to copy message",
                    "Visual mode for selection"
                ]
            },
            {
                "name": "git_integration",
                "description": "Git operations from within TUI",
                "priority": "medium",
                "files": ["src/tools/git.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Show git status in file tree",
                    "Stage/unstage files",
                    "Commit with message (Ctrl+G)",
                    "View diff in overlay",
                    "Push/pull with status display"
                ]
            },
            {
                "name": "search_history",
                "description": "Search through all past conversations",
                "priority": "medium",
                "files": ["src/tools/search.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Full-text search across all saved conversations",
                    "Filter by date range, model, keywords",
                    "Regex support for advanced queries",
                    "Jump to matching conversation",
                    "Ctrl+F to open search"
                ]
            },
            {
                "name": "template_system",
                "description": "Reusable prompt templates",
                "priority": "medium",
                "files": ["src/tools/templates.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Define templates in config/templates.yaml",
                    "Variables like {{filename}}, {{language}}",
                    "Quick insert from menu",
                    "Common templates: code review, debug, explain",
                    "Custom user templates supported"
                ]
            },
            {
                "name": "context_files",
                "description": "Attach files as context to conversation",
                "priority": "medium",
                "files": ["src/tools/context.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Drag-drop files or browse to attach",
                    "Show attached files in sidebar",
                    "Auto-include in next prompt",
                    "Support code, text, markdown files",
                    "Clear context with button"
                ]
            },
            {
                "name": "keyboard_shortcuts_help",
                "description": "Overlay showing all keyboard shortcuts",
                "priority": "medium",
                "files": ["src/ui/shortcuts.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Press ? to show shortcuts overlay",
                    "Grouped by category (Navigation, Editing, Tools)",
                    "Search/filter shortcuts",
                    "Click shortcut to execute command",
                    "Printable cheat sheet"
                ]
            },

            # LOW PRIORITY - Nice to have
            {
                "name": "themes",
                "description": "Customizable color themes",
                "priority": "low",
                "files": ["src/ui/themes.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Built-in themes: GitHub Dark, Dracula, Nord, Monokai",
                    "Load from config/theme.yaml",
                    "Live preview when switching",
                    "Custom theme support",
                    "Syntax highlighting matches theme"
                ]
            },
            {
                "name": "metrics_dashboard",
                "description": "Usage analytics and statistics",
                "priority": "low",
                "files": ["src/ui/metrics.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Tokens used per conversation",
                    "Most used models",
                    "Response time graphs",
                    "Conversation length trends",
                    "Export metrics to CSV"
                ]
            },

            # BREAKTHROUGH PRIORITY - Best agentic interface on the planet
            {
                "name": "voice_input",
                "description": "Voice-to-text for hands-free interaction",
                "priority": "high",
                "files": ["src/tools/voice.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Push-to-talk with Ctrl+Space",
                    "Uses Whisper API or local STT",
                    "Show recording indicator",
                    "Auto-submit after speech ends",
                    "Fallback to typing if STT unavailable"
                ]
            },
            {
                "name": "agent_personas",
                "description": "Switchable agent personalities and expertise",
                "priority": "high",
                "files": ["src/core/personas.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Personas: Senior Dev, Architect, Security Expert, Teacher, Debugger",
                    "Each has custom system prompt",
                    "Switch persona mid-conversation",
                    "Show active persona in status bar",
                    "Custom personas via config/personas.yaml"
                ]
            },
            {
                "name": "memory_system",
                "description": "Long-term memory across conversations",
                "priority": "high",
                "files": ["src/core/memory.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Vector DB for semantic memory (ChromaDB/FAISS)",
                    "Auto-save important facts from conversations",
                    "Retrieve relevant context automatically",
                    "User can flag messages as 'remember this'",
                    "Clear/manage memory in settings"
                ]
            },
            {
                "name": "web_search_tool",
                "description": "Agent can search the web for current info",
                "priority": "high",
                "files": ["src/tools/web_search.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Integrate DuckDuckGo/SearxNG API",
                    "Agent triggers search when needed",
                    "Show 'searching web...' indicator",
                    "Display sources inline",
                    "Cache results for session"
                ]
            },
            {
                "name": "rag_codebase",
                "description": "RAG over entire codebase for context",
                "priority": "high",
                "files": ["src/tools/rag.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Index project files on startup",
                    "Semantic search across codebase",
                    "Auto-include relevant files in context",
                    "Show which files were retrieved",
                    "Update index on file changes"
                ]
            },
            {
                "name": "multi_agent_collab",
                "description": "Multiple specialized agents working together",
                "priority": "medium",
                "files": ["src/core/multi_agent.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Spawn multiple agents for complex tasks",
                    "Planner agent breaks down tasks",
                    "Executor agents work in parallel",
                    "Reviewer agent validates output",
                    "Show agent collaboration tree"
                ]
            },
            {
                "name": "diff_viewer",
                "description": "Side-by-side diff viewer for code changes",
                "priority": "medium",
                "files": ["src/ui/diff.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Compare before/after when agent suggests edits",
                    "Syntax highlighted diff",
                    "Accept/reject individual hunks",
                    "Apply all changes at once",
                    "Undo/redo support"
                ]
            },
            {
                "name": "screenshot_ocr",
                "description": "Paste screenshot and extract code/text",
                "priority": "medium",
                "files": ["src/tools/ocr.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Paste image from clipboard",
                    "OCR with Tesseract or vision model",
                    "Extract code blocks automatically",
                    "Send extracted text to agent",
                    "Preview OCR result before sending"
                ]
            },
            {
                "name": "task_orchestrator",
                "description": "AutoGPT-style autonomous task execution",
                "priority": "medium",
                "files": ["src/core/orchestrator.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Give high-level goal, agent executes steps",
                    "Agent can use all tools autonomously",
                    "Show execution plan before starting",
                    "Step-by-step progress display",
                    "Pause/resume/cancel execution"
                ]
            },
            {
                "name": "documentation_generator",
                "description": "Auto-generate docs from codebase",
                "priority": "medium",
                "files": ["src/tools/docgen.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Scan project for undocumented functions",
                    "Generate docstrings with AI",
                    "Create README sections automatically",
                    "API documentation from code",
                    "Export as Markdown/HTML"
                ]
            },
            {
                "name": "test_generator",
                "description": "Automatically generate unit tests",
                "priority": "medium",
                "files": ["src/tools/testgen.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Analyze function and generate pytest tests",
                    "Edge cases and error conditions",
                    "Mock external dependencies",
                    "Run tests and show results",
                    "Update tests based on failures"
                ]
            },
            {
                "name": "refactor_assistant",
                "description": "AI-powered code refactoring",
                "priority": "medium",
                "files": ["src/tools/refactor.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Detect code smells automatically",
                    "Suggest refactoring improvements",
                    "Preview changes in diff viewer",
                    "Apply refactorings safely",
                    "Verify tests still pass after refactor"
                ]
            },
            {
                "name": "dependency_analyzer",
                "description": "Visualize and manage dependencies",
                "priority": "low",
                "files": ["src/tools/deps.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Parse requirements.txt/package.json",
                    "Show dependency graph visualization",
                    "Check for outdated packages",
                    "Security vulnerability scanning",
                    "Suggest safe upgrades"
                ]
            },
            {
                "name": "notebook_mode",
                "description": "Jupyter-style notebook interface",
                "priority": "low",
                "files": ["src/ui/notebook.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Mix code, output, and markdown cells",
                    "Execute cells independently",
                    "Maintain kernel state across cells",
                    "Export to .ipynb format",
                    "Rich output (plots, tables, HTML)"
                ]
            },
            {
                "name": "session_replay",
                "description": "Record and replay entire coding sessions",
                "priority": "low",
                "files": ["src/tools/replay.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Record all commands and outputs",
                    "Replay at adjustable speed",
                    "Export as video/GIF",
                    "Share session as shareable link",
                    "Annotate key moments"
                ]
            },
            {
                "name": "plugin_system",
                "description": "Extensible plugin architecture",
                "priority": "low",
                "files": ["src/core/plugins.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Load plugins from ~/.camel/plugins/",
                    "Plugins can add tools, commands, themes",
                    "Hot reload without restart",
                    "Plugin marketplace/registry",
                    "Sandboxed execution for safety"
                ]
            },
            {
                "name": "collaboration_mode",
                "description": "Real-time collaboration like Google Docs",
                "priority": "low",
                "files": ["src/core/collab.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "WebSocket server for sync",
                    "Multiple users share same session",
                    "See cursors and edits in real-time",
                    "Chat with collaborators",
                    "Session sharing via link"
                ]
            },
            {
                "name": "smart_autocomplete",
                "description": "AI-powered autocomplete for prompts",
                "priority": "high",
                "files": ["src/ui/autocomplete.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Suggest completions as you type",
                    "Learn from your prompting patterns",
                    "Common patterns: 'explain', 'debug', 'refactor'",
                    "File/function name completion",
                    "Tab to accept suggestion"
                ]
            },
            {
                "name": "inline_documentation",
                "description": "Hover over code to see docs inline",
                "priority": "medium",
                "files": ["src/ui/inline_docs.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Hover over function/class names",
                    "Show docstring in popup",
                    "Link to full documentation",
                    "Type hints and signatures",
                    "Works with custom and stdlib code"
                ]
            },
            {
                "name": "error_explainer",
                "description": "AI explains errors and suggests fixes",
                "priority": "high",
                "files": ["src/tools/error_explain.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Detect errors in terminal output",
                    "Auto-explain what went wrong",
                    "Suggest concrete fixes",
                    "One-click to apply fix",
                    "Learn from past errors"
                ]
            },
            {
                "name": "performance_profiler",
                "description": "Profile code and suggest optimizations",
                "priority": "medium",
                "files": ["src/tools/profiler.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Run cProfile on Python code",
                    "Visualize hotspots with flamegraph",
                    "AI suggests optimization strategies",
                    "Compare before/after benchmarks",
                    "Memory profiling included"
                ]
            },
            {
                "name": "code_snippets",
                "description": "Personal snippet library with AI search",
                "priority": "medium",
                "files": ["src/tools/snippets.py", "src/main.py"],
                "agent_type": "Solver",
                "requirements": [
                    "Save frequently used code snippets",
                    "Semantic search to find snippets",
                    "Variables/placeholders in snippets",
                    "Import from GitHub gists",
                    "Share snippets with team"
                ]
            }
        ]

    def init_database(self):
        """Initialize database for agent logging - NEVER CRASHES"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Drop old table if exists to avoid schema conflicts
            cursor.execute("DROP TABLE IF EXISTS agent_execution_log")

            # Create fresh table with correct schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    task TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    outputs TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()
            conn.close()
            print("✅ Database initialized", flush=True)
        except Exception as e:
            print(f"⚠️  Database init failed (non-fatal): {e}", flush=True)

    async def spawn_agent(self, task: Dict) -> DevelopmentAgent:
        """Spawn a real autonomous agent - never crashes"""
        try:
            agent_id = f"{task['agent_type'].lower()}_{task['name']}_{int(time.time())}"
            agent = DevelopmentAgent(agent_id, task, self.project_root)
            self.agents.append(agent)

            print(f"\n🚀 Spawning {task['agent_type']} Agent for: {task['name']}", flush=True)
            print(f"   Priority: {task['priority']}", flush=True)
            print(f"   Files: {', '.join(task['files'])}", flush=True)

            return agent
        except Exception as e:
            print(f"❌ Failed to spawn agent for {task.get('name', 'unknown')}: {e}", flush=True)
            return None

    async def log_agent_completion(self, agent: DevelopmentAgent):
        """Log agent execution to database - NEVER CRASHES"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO agent_execution_log
                (agent_id, task, start_time, end_time, status, outputs, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent.agent_id,
                agent.task['name'],
                agent.start_time or "unknown",
                agent.end_time or "unknown",
                agent.status,
                json.dumps(agent.outputs)[:10000],  # Limit to 10KB
                datetime.now(UTC).isoformat()
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️  Failed to log agent {agent.agent_id} (non-fatal): {e}", flush=True)

    async def run_development_cycle(self):
        """Execute one development cycle - NEVER CRASHES"""
        try:
            self.cycle_count += 1
            print("\n" + "=" * 80, flush=True)
            print("🔥 AUTONOMOUS DEVELOPMENT CYCLE - BULLETPROOF MODE", flush=True)
            print("=" * 80, flush=True)

            # Cycle through ALL priority tiers round-robin style
            priority_order = ['critical', 'high', 'medium', 'low']
            current_priority = priority_order[(self.cycle_count - 1) % len(priority_order)]

            print(f"\n🎯 PRIORITY TIER: {current_priority.upper()} (Cycle #{self.cycle_count})", flush=True)

            # Get tasks for current priority tier
            priority_tasks = [t for t in self.tasks if t['priority'] == current_priority]
            print(f"📋 Found {len(priority_tasks)} {current_priority} priority tasks", flush=True)

            # If no tasks in this tier, move to next
            if not priority_tasks:
                print(f"⚠️  No tasks in {current_priority} tier, using critical", flush=True)
                priority_tasks = [t for t in self.tasks if t['priority'] == 'critical']

            # Spawn agents for each task (max 2 at a time to avoid overloading)
            active_agents = []
            for task in priority_tasks[:2]:  # MAX 2 to keep Ollama responsive
                agent = await self.spawn_agent(task)
                if agent:
                    active_agents.append(agent)

            if not active_agents:
                print("⚠️  No agents spawned", flush=True)
                return

            # Execute all agents in parallel with timeout protection
            print(f"\n⚡ Executing {len(active_agents)} agents in parallel...", flush=True)

            try:
                await asyncio.wait_for(
                    asyncio.gather(*[agent.execute_task() for agent in active_agents], return_exceptions=True),
                    timeout=600  # 10 minute max
                )
            except asyncio.TimeoutError:
                print("⚠️  Cycle timeout reached (10 min), continuing...", flush=True)
            except Exception as e:
                print(f"⚠️  Error in parallel execution (non-fatal): {e}", flush=True)

            # Log results
            print("\n" + "=" * 80, flush=True)
            print("📊 EXECUTION RESULTS", flush=True)
            print("=" * 80, flush=True)

            completed = 0
            failed = 0

            for agent in active_agents:
                try:
                    print(f"\n[{agent.agent_id}]", flush=True)
                    print(f"  Task: {agent.task['name']}", flush=True)
                    print(f"  Status: {agent.status}", flush=True)
                    print(f"  Duration: {agent.start_time} -> {agent.end_time}", flush=True)
                    print(f"  Outputs: {len(agent.outputs)} entries", flush=True)

                    if agent.status == "completed":
                        completed += 1
                    else:
                        failed += 1

                    # Log to database
                    await self.log_agent_completion(agent)

                    # Cleanup
                    await agent.close()
                except Exception as e:
                    print(f"⚠️  Error processing agent {agent.agent_id}: {e}", flush=True)
                    failed += 1

            self.total_completions += completed
            self.total_failures += failed

            print(f"\n✅ Cycle complete: {completed} succeeded, {failed} failed", flush=True)
            print(f"📈 Total stats: {self.total_completions} completions, {self.total_failures} failures across {self.cycle_count} cycles", flush=True)

        except Exception as e:
            print(f"\n❌ CYCLE ERROR (non-fatal): {e}", flush=True)
            print(f"Traceback: {traceback.format_exc()}", flush=True)
            print("🔄 Will retry next cycle...", flush=True)

    async def continuous_development(self):
        """Run continuous development cycles - INFINITE BULLETPROOF LOOP"""
        print("\n🔄 Starting BULLETPROOF continuous autonomous development...", flush=True)
        print(f"📍 Project: {self.project_root}", flush=True)
        print(f"🤖 Model: {MODEL} @ {OLLAMA_ENDPOINT}", flush=True)
        print(f"🛡️  CRASH PROTECTION: Active", flush=True)
        print(f"🔁 MODE: Infinite loop with error recovery\n", flush=True)

        self.init_database()

        while True:
            try:
                print(f"\n\n{'=' * 80}", flush=True)
                print(f"🔁 CYCLE #{self.cycle_count + 1} - {datetime.now(UTC).isoformat()}", flush=True)
                print(f"{'=' * 80}", flush=True)

                await self.run_development_cycle()

                print("\n💤 Sleeping 600s before next cycle...", flush=True)
                await asyncio.sleep(600)  # 10 minutes between cycles - be gentle on Ollama

            except KeyboardInterrupt:
                print("\n\n⏹️  Stopped by user", flush=True)
                break
            except Exception as e:
                print(f"\n\n❌ FATAL ERROR IN MAIN LOOP: {e}", flush=True)
                print(f"Traceback: {traceback.format_exc()}", flush=True)
                print("🔄 Recovering in 60 seconds...\n", flush=True)
                await asyncio.sleep(60)
                # Loop continues - NEVER DIES


async def main():
    """Entry point - BULLETPROOF"""
    system = AutonomousDevelopmentSystem()
    try:
        await system.continuous_development()
    except KeyboardInterrupt:
        print("\n\n⏹️  Autonomous development stopped by user", flush=True)
    except Exception as e:
        print(f"\n\n❌ UNRECOVERABLE ERROR: {e}", flush=True)
        print(f"Traceback: {traceback.format_exc()}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
