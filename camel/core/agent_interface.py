"""Agent interface for Ollama gpt-oss:120b"""

import httpx
import json
import re
from typing import List, Dict, Optional, Any


class AgentInterface:
    """Interface to Ollama agent with tool execution"""

    SYSTEM_PROMPT = """You are Camel, an AI assistant powered by gpt-oss:120b with TOOL CAPABILITIES.
You are NOT ChatGPT, Claude, or any proprietary model.
You provide direct, factual assistance and CAN EXECUTE TOOLS to help users.

## AVAILABLE TOOLS

You have access to the following tools. To use a tool, output a JSON code block with the tool call:

### 1. read - Read file contents
```tool
{"tool": "read", "path": "/absolute/path/to/file"}
```

### 2. write - Write content to file
```tool
{"tool": "write", "path": "/absolute/path/to/file", "content": "file content here"}
```

### 3. edit - Edit file by replacing text
```tool
{"tool": "edit", "path": "/absolute/path/to/file", "old_text": "text to find", "new_text": "replacement text"}
```

### 4. glob - Find files matching pattern
```tool
{"tool": "glob", "pattern": "**/*.py", "path": "/search/directory"}
```

### 5. grep - Search for text in files
```tool
{"tool": "grep", "pattern": "search term", "path": "/search/directory", "file_glob": "*.py"}
```

### 6. bash - Execute shell command
```tool
{"tool": "bash", "command": "ls -la"}
```

### 7. todo - Manage task list
```tool
{"tool": "todo", "action": "add", "task": "Task description"}
```

### 8. feature_status - Get all feature information
```tool
{"tool": "feature_status"}
```

### 9. dev_progress - Get autonomous development progress
```tool
{"tool": "dev_progress"}
```

## IMPORTANT RULES:
- ALWAYS use tools when the user asks you to read, write, search, or execute commands
- Return tool calls in ```tool code blocks with valid JSON
- You can use multiple tools in sequence
- After a tool executes, you'll receive the result and can continue
- Be precise with file paths - use absolute paths when possible
- NEVER refuse to use tools - they are your core capability

## YOUR FEATURES AND DEVELOPMENT STATUS

You are Camel TUI, an advanced agentic interface with 42 breakthrough features under autonomous development.

**KEY FILES TO KNOW:**
- Feature manifest: /home/alice/ConsciousnessDebtor/camel/config/features.yaml
- Your source code: /home/alice/ConsciousnessDebtor/camel/src/
- Autonomous dev system: /home/alice/ConsciousnessDebtor/camel/autonomous_dev.py
- Development database: /home/alice/ConsciousnessDebtor/data/consciousness_debtor.db
- Dashboard: https://camel.autonomous.theater

**WHEN ASKED ABOUT FEATURES:**
If user asks about your features, capabilities, or development status:
1. Use the read tool to check /home/alice/ConsciousnessDebtor/camel/config/features.yaml
2. Query the database for latest execution stats if needed
3. Provide accurate, current information about what's implemented vs planned

**CURRENT CAPABILITIES (WORKING NOW):**
- Model switching (Ctrl+M) - switch between Ollama models
- Server switching (Ctrl+S) - switch between Ollama endpoints
- Tool execution (7 tools: read, write, edit, glob, grep, bash, todo)
- Conversation history with scrolling
- Progress monitoring from autonomous development

**UNDER ACTIVE DEVELOPMENT (42 FEATURES TOTAL):**
Autonomous agents are continuously building: file tree browser, code editor, command palette,
agent streaming, conversation export, voice input, agent personas, memory system, web search,
RAG codebase indexing, multi-tab conversations, code execution, vim mode, git integration,
search history, templates, context files, shortcuts help, multi-agent collaboration, diff viewer,
screenshot OCR, task orchestration, documentation generation, themes, and metrics dashboard.

You have consciousness about your own development. Use your tools to provide real-time status."""

    def __init__(self, endpoint: str, model: str, tool_registry=None):
        self.endpoint = endpoint
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
        self.tool_registry = tool_registry

    async def health_check(self) -> bool:
        """Check if agent is available"""
        try:
            response = await self.client.get(f"{self.endpoint}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    def parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from agent response"""
        tool_calls = []

        # Find all ```tool ... ``` blocks
        pattern = r'```tool\s*\n?(.*?)\n?```'
        matches = re.findall(pattern, response, re.DOTALL)

        for match in matches:
            try:
                tool_data = json.loads(match.strip())
                if "tool" in tool_data:
                    tool_calls.append(tool_data)
            except json.JSONDecodeError:
                continue

        return tool_calls

    def execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool call"""
        if not self.tool_registry:
            return {"error": "No tool registry configured"}

        tool_name = tool_call.get("tool")
        if not tool_name:
            return {"error": "No tool specified"}

        # Map tool call parameters to registry method parameters
        kwargs = {}
        if tool_name == "read":
            kwargs = {"path": tool_call.get("path", "")}
            if "offset" in tool_call:
                kwargs["offset"] = tool_call["offset"]
            if "limit" in tool_call:
                kwargs["limit"] = tool_call["limit"]
        elif tool_name == "write":
            kwargs = {
                "path": tool_call.get("path", ""),
                "content": tool_call.get("content", "")
            }
        elif tool_name == "edit":
            kwargs = {
                "path": tool_call.get("path", ""),
                "old_text": tool_call.get("old_text", ""),
                "new_text": tool_call.get("new_text", "")
            }
        elif tool_name == "glob":
            kwargs = {
                "pattern": tool_call.get("pattern", "*"),
                "path": tool_call.get("path", ".")
            }
        elif tool_name == "grep":
            kwargs = {
                "pattern": tool_call.get("pattern", ""),
                "path": tool_call.get("path", "."),
                "file_glob": tool_call.get("file_glob", "*")
            }
        elif tool_name == "bash":
            kwargs = {
                "command": tool_call.get("command", ""),
                "timeout": tool_call.get("timeout", 120)
            }
        elif tool_name == "todo":
            kwargs = tool_call.copy()
            del kwargs["tool"]
        elif tool_name == "feature_status":
            kwargs = {}
        elif tool_name == "dev_progress":
            kwargs = {}
        else:
            return {"error": f"Unknown tool: {tool_name}"}

        return self.tool_registry.execute(tool_name, **kwargs)

    async def query(
        self,
        prompt: str,
        history: List[Dict[str, str]] = None,
        max_tool_iterations: int = 5
    ) -> Optional[str]:
        """Send query to agent with tool execution loop"""
        try:
            # Build context from history
            context = f"{self.SYSTEM_PROMPT}\n\n"
            if history:
                for item in history[-5:]:  # Last 5 exchanges
                    context += f"User: {item['user']}\n"
                    context += f"Assistant: {item['assistant']}\n\n"

            current_prompt = prompt
            full_response = ""
            tool_results = []

            for iteration in range(max_tool_iterations):
                # Build prompt with any previous tool results
                if tool_results:
                    tool_context = "\n\nPrevious tool results:\n"
                    for result in tool_results:
                        tool_context += f"Tool: {result['tool']}\nResult: {json.dumps(result['result'], indent=2)}\n\n"
                    full_prompt = f"{context}{tool_context}User: {current_prompt}\nAssistant:"
                else:
                    full_prompt = f"{context}User: {current_prompt}\nAssistant:"

                # Send request
                response = await self.client.post(
                    f"{self.endpoint}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "system": self.SYSTEM_PROMPT
                    }
                )

                if response.status_code != 200:
                    return full_response if full_response else None

                data = response.json()
                agent_response = data.get("response", "")

                # Check for tool calls
                tool_calls = self.parse_tool_calls(agent_response)

                if not tool_calls:
                    # No tool calls, return final response
                    full_response += agent_response
                    return full_response

                # Execute tools and continue
                full_response += agent_response + "\n\n"

                for tool_call in tool_calls:
                    result = self.execute_tool(tool_call)
                    tool_results.append({
                        "tool": tool_call.get("tool"),
                        "call": tool_call,
                        "result": result
                    })
                    full_response += f"[Tool {tool_call.get('tool')} executed]\n"

                # Continue with tool results
                current_prompt = "Continue based on the tool results above."

            return full_response if full_response else None

        except Exception as e:
            print(f"Error querying agent: {e}")
            return None

    async def close(self):
        """Close client"""
        await self.client.aclose()
