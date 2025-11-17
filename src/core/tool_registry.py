"""Tool registry - all available tools"""

from typing import Dict, Callable, Any
import os
import subprocess
import json
from pathlib import Path


class ToolRegistry:
    """Registry of all tools available to the agent"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_all()

    def _register_all(self):
        """Register all tools"""
        # Filesystem tools
        self.register("read", self.read_file)
        self.register("write", self.write_file)
        self.register("edit", self.edit_file)
        self.register("glob", self.glob_files)
        self.register("grep", self.grep_content)

        # Shell tools
        self.register("bash", self.execute_bash)

        # Task tools
        self.register("todo", self.manage_todos)

        # Feature status tools
        self.register("feature_status", self.get_feature_status)
        self.register("dev_progress", self.get_dev_progress)

    def register(self, name: str, func: Callable):
        """Register a tool"""
        self.tools[name] = func

    def execute(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            return self.tools[tool_name](**kwargs)
        except Exception as e:
            return {"error": str(e)}

    # Tool implementations

    def read_file(self, path: str, offset: int = 0, limit: int = None) -> Dict:
        """Read file content"""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()

            if offset:
                lines = lines[offset:]
            if limit:
                lines = lines[:limit]

            return {
                "success": True,
                "content": "".join(lines),
                "lines": len(lines)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, path: str, content: str) -> Dict:
        """Write file content"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def edit_file(self, path: str, old_text: str, new_text: str) -> Dict:
        """Edit file by replacing text"""
        try:
            with open(path, 'r') as f:
                content = f.read()

            if old_text not in content:
                return {"success": False, "error": "Text not found"}

            new_content = content.replace(old_text, new_text, 1)

            with open(path, 'w') as f:
                f.write(new_content)

            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def glob_files(self, pattern: str, path: str = ".") -> Dict:
        """Find files matching pattern"""
        try:
            from pathlib import Path
            matches = list(Path(path).glob(pattern))
            return {
                "success": True,
                "matches": [str(m) for m in matches],
                "count": len(matches)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def grep_content(self, pattern: str, path: str = ".", file_glob: str = "*") -> Dict:
        """Search for pattern in files"""
        try:
            result = subprocess.run(
                ["rg", pattern, path, "-g", file_glob, "--json"],
                capture_output=True,
                text=True
            )

            matches = []
            for line in result.stdout.split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'match':
                            matches.append(data)
                    except:
                        pass

            return {
                "success": True,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_bash(self, command: str, timeout: int = 120) -> Dict:
        """Execute bash command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def manage_todos(self, action: str, **kwargs) -> Dict:
        """Manage todo list"""
        # Placeholder for todo management
        return {"success": True, "action": action, "data": kwargs}

    def get_feature_status(self) -> Dict:
        """Get current feature development status"""
        try:
            import yaml
            features_file = Path(__file__).parent.parent.parent / "config" / "features.yaml"

            if features_file.exists():
                with open(features_file) as f:
                    features = yaml.safe_load(f)

                # Count features by status
                in_dev = 0
                planned = 0

                for priority in ['critical', 'high', 'medium', 'low']:
                    if priority in features:
                        for feature in features[priority]:
                            if feature.get('status') == 'in_development':
                                in_dev += 1
                            else:
                                planned += 1

                return {
                    "success": True,
                    "total_features": features.get("total_features", 42),
                    "in_development": in_dev,
                    "planned": planned,
                    "features": features
                }
            else:
                return {"success": False, "error": "Features file not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_dev_progress(self) -> Dict:
        """Get autonomous development progress from database"""
        try:
            import sqlite3
            db_path = Path(__file__).parent.parent.parent.parent / "data" / "consciousness_debtor.db"

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Total executions
            cursor.execute("SELECT COUNT(*) FROM agent_execution_log")
            total = cursor.fetchone()[0] or 0

            # Completed
            cursor.execute("SELECT COUNT(*) FROM agent_execution_log WHERE status = 'completed'")
            completed = cursor.fetchone()[0] or 0

            # Failed
            cursor.execute("SELECT COUNT(*) FROM agent_execution_log WHERE status = 'failed'")
            failed = cursor.fetchone()[0] or 0

            # Unique tasks
            cursor.execute("SELECT DISTINCT task FROM agent_execution_log")
            unique_tasks = [row[0] for row in cursor.fetchall()]

            # Recent activity
            cursor.execute("""
                SELECT task, status, created_at
                FROM agent_execution_log
                ORDER BY created_at DESC
                LIMIT 10
            """)
            recent = [{"task": r[0], "status": r[1], "time": r[2]} for r in cursor.fetchall()]

            conn.close()

            success_rate = (completed / total * 100) if total > 0 else 0

            return {
                "success": True,
                "total_executions": total,
                "completed": completed,
                "failed": failed,
                "success_rate": round(success_rate, 1),
                "unique_features_attempted": len(unique_tasks),
                "features_list": unique_tasks,
                "recent_activity": recent,
                "dashboard_url": "https://camel.autonomous.theater"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
