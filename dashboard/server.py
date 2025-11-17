#!/usr/bin/env python3
"""
Camel Autonomous Development Dashboard
Real-time monitoring, agent control, and progress reporting
"""

import asyncio
import json
import sqlite3
import subprocess
import signal
import os
from datetime import datetime, UTC
from pathlib import Path
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn


DB_PATH = Path(__file__).parent.parent.parent / "data" / "consciousness_debtor.db"
LOG_PATH = Path("/tmp/camel-ULTIMATE.log")
AUTONOMOUS_SCRIPT = Path(__file__).parent.parent / "autonomous_dev.py"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Camel Dashboard starting...")
    yield
    print("⏹️  Camel Dashboard shutting down...")


app = FastAPI(
    title="Camel Autonomous Development Dashboard",
    description="Monitor and control autonomous AI agents building the best agentic interface",
    lifespan=lifespan
)


def get_db_stats():
    """Get statistics from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
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

        # Recent executions
        cursor.execute("""
            SELECT agent_id, task, status, start_time, end_time,
                   LENGTH(outputs) as output_size, created_at
            FROM agent_execution_log
            ORDER BY created_at DESC
            LIMIT 50
        """)
        recent = []
        for row in cursor.fetchall():
            recent.append({
                'agent_id': row[0],
                'task': row[1],
                'status': row[2],
                'start_time': row[3],
                'end_time': row[4],
                'output_size': row[5],
                'created_at': row[6]
            })

        # Task statistics
        cursor.execute("""
            SELECT task,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM agent_execution_log
            GROUP BY task
            ORDER BY total DESC
        """)
        task_stats = []
        for row in cursor.fetchall():
            task_stats.append({
                'task': row[0],
                'total': row[1],
                'completed': row[2],
                'failed': row[3],
                'success_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0
            })

        conn.close()

        success_rate = (completed / total * 100) if total > 0 else 0

        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'success_rate': round(success_rate, 2),
            'recent': recent,
            'task_stats': task_stats
        }
    except Exception as e:
        return {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'success_rate': 0,
            'recent': [],
            'task_stats': [],
            'error': str(e)
        }


def get_system_status():
    """Get system status"""
    # Check if autonomous_dev.py is running
    try:
        result = subprocess.run(
            ["pgrep", "-f", "autonomous_dev.py"],
            capture_output=True,
            text=True
        )
        pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
        running = len(pids) > 0
    except:
        pids = []
        running = False

    # Get last log lines
    try:
        result = subprocess.run(
            ["tail", "-100", str(LOG_PATH)],
            capture_output=True,
            text=True
        )
        last_logs = result.stdout
    except:
        last_logs = "Log file not accessible"

    # Parse current cycle from logs
    cycle_number = 0
    try:
        for line in last_logs.split('\n'):
            if 'CYCLE #' in line:
                parts = line.split('#')
                if len(parts) > 1:
                    num = parts[1].split()[0].strip()
                    cycle_number = int(num)
    except:
        pass

    return {
        'running': running,
        'pids': pids,
        'cycle_number': cycle_number,
        'last_logs': last_logs,
        'log_path': str(LOG_PATH),
        'db_path': str(DB_PATH)
    }


def restart_agents():
    """Restart autonomous development system"""
    # Kill existing
    subprocess.run(["pkill", "-f", "autonomous_dev.py"], capture_output=True)

    # Wait a bit
    import time
    time.sleep(2)

    # Start new
    subprocess.Popen(
        ["python3", "-u", str(AUTONOMOUS_SCRIPT)],
        stdout=open(LOG_PATH, 'a'),
        stderr=subprocess.STDOUT,
        cwd=AUTONOMOUS_SCRIPT.parent,
        start_new_session=True
    )

    return True


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camel Autonomous Development Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 24px rgba(46, 160, 67, 0.3);
        }

        h1 {
            font-size: 2.5em;
            color: #fff;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.2em;
            color: rgba(255, 255, 255, 0.9);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 25px;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }

        .stat-value {
            font-size: 3em;
            font-weight: bold;
            color: #58a6ff;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #8b949e;
            font-size: 1.1em;
        }

        .success .stat-value { color: #56d364; }
        .error .stat-value { color: #f85149; }
        .warning .stat-value { color: #d29922; }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }

        .status-running { background: #56d364; }
        .status-stopped { background: #f85149; }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .panel {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
        }

        .panel h2 {
            color: #f0f6fc;
            margin-bottom: 20px;
            font-size: 1.5em;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #30363d;
        }

        th {
            color: #8b949e;
            font-weight: 600;
        }

        .status-completed {
            color: #56d364;
            font-weight: bold;
        }

        .status-failed {
            color: #f85149;
            font-weight: bold;
        }

        .logs {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Fira Code', monospace;
            font-size: 0.9em;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .btn {
            background: #238636;
            color: #fff;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: background 0.2s;
            margin: 5px;
        }

        .btn:hover {
            background: #2ea043;
        }

        .btn-danger {
            background: #da3633;
        }

        .btn-danger:hover {
            background: #f85149;
        }

        .btn-warning {
            background: #9e6a03;
        }

        .btn-warning:hover {
            background: #d29922;
        }

        .progress-bar {
            background: #30363d;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-fill {
            background: linear-gradient(90deg, #238636, #56d364);
            height: 100%;
            transition: width 0.5s ease;
        }

        .footer {
            text-align: center;
            color: #8b949e;
            margin-top: 40px;
            padding: 20px;
        }

        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }

        .refresh-timer {
            color: #8b949e;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🐪 Camel Autonomous Development Dashboard</h1>
            <div class="subtitle">Building the Best Agentic Interface on the Planet</div>
        </header>

        <div class="controls">
            <button class="btn" onclick="refreshData()">🔄 Refresh Now</button>
            <button class="btn btn-warning" onclick="restartAgents()">⚡ Restart Agents</button>
            <button class="btn" onclick="toggleAutoRefresh()">⏸️ Toggle Auto-Refresh</button>
            <span class="refresh-timer" id="timer">Next refresh in: 10s</span>
        </div>

        <div class="stats-grid">
            <div class="stat-card" id="system-status">
                <div class="stat-value">
                    <span class="status-indicator status-stopped"></span>
                    CHECKING...
                </div>
                <div class="stat-label">System Status</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value" id="completed-count">0</div>
                <div class="stat-label">Completed Tasks</div>
            </div>
            <div class="stat-card error">
                <div class="stat-value" id="failed-count">0</div>
                <div class="stat-label">Failed Tasks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="success-rate">0%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-value" id="cycle-number">0</div>
                <div class="stat-label">Current Cycle</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-count">0</div>
                <div class="stat-label">Total Executions</div>
            </div>
        </div>

        <div class="panel">
            <h2>📊 Overall Progress: 42 Features</h2>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-bar" style="width: 0%"></div>
            </div>
            <div id="progress-text" style="text-align: center; color: #8b949e;">Loading...</div>
        </div>

        <div class="panel">
            <h2>📈 Task Performance</h2>
            <table id="task-stats">
                <thead>
                    <tr>
                        <th>Task</th>
                        <th>Total Runs</th>
                        <th>Completed</th>
                        <th>Failed</th>
                        <th>Success Rate</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="5">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="panel">
            <h2>🕐 Recent Agent Activity</h2>
            <table id="recent-activity">
                <thead>
                    <tr>
                        <th>Agent ID</th>
                        <th>Task</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Output Size</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="6">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="panel">
            <h2>📜 Live Logs (Last 100 lines)</h2>
            <div class="logs" id="logs">Loading logs...</div>
        </div>

        <div class="footer">
            <p>ConsciousnessDebtor - Autonomous Development System</p>
            <p>Building 42 breakthrough features | Bulletproof execution | 95%+ success rate</p>
            <p id="last-update">Last update: Never</p>
        </div>
    </div>

    <script>
        let autoRefresh = true;
        let countdown = 10;
        let countdownInterval;

        async function fetchData() {
            try {
                const [statsRes, statusRes] = await Promise.all([
                    fetch('/api/stats'),
                    fetch('/api/status')
                ]);

                const stats = await statsRes.json();
                const status = await statusRes.json();

                updateUI(stats, status);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        function updateUI(stats, status) {
            // System status
            const statusEl = document.getElementById('system-status');
            if (status.running) {
                statusEl.innerHTML = `
                    <div class="stat-value" style="color: #56d364;">
                        <span class="status-indicator status-running"></span>
                        RUNNING
                    </div>
                    <div class="stat-label">PIDs: ${status.pids.join(', ')}</div>
                `;
            } else {
                statusEl.innerHTML = `
                    <div class="stat-value" style="color: #f85149;">
                        <span class="status-indicator status-stopped"></span>
                        STOPPED
                    </div>
                    <div class="stat-label">System Status</div>
                `;
            }

            // Stats
            document.getElementById('completed-count').textContent = stats.completed;
            document.getElementById('failed-count').textContent = stats.failed;
            document.getElementById('success-rate').textContent = stats.success_rate + '%';
            document.getElementById('cycle-number').textContent = status.cycle_number;
            document.getElementById('total-count').textContent = stats.total;

            // Progress bar (assuming 42 total features, 5 critical done = ~12%)
            // This is simplified - in reality we'd track unique completed features
            const uniqueTasks = new Set(stats.task_stats.filter(t => t.completed > 0).map(t => t.task));
            const completedFeatures = uniqueTasks.size;
            const progressPercent = (completedFeatures / 42 * 100).toFixed(1);
            document.getElementById('progress-bar').style.width = progressPercent + '%';
            document.getElementById('progress-text').textContent =
                `${completedFeatures}/42 features attempted (${progressPercent}%)`;

            // Task stats table
            const taskStatsBody = document.getElementById('task-stats').getElementsByTagName('tbody')[0];
            taskStatsBody.innerHTML = stats.task_stats.map(task => `
                <tr>
                    <td>${task.task}</td>
                    <td>${task.total}</td>
                    <td>${task.completed}</td>
                    <td>${task.failed}</td>
                    <td>${task.success_rate.toFixed(1)}%</td>
                </tr>
            `).join('');

            // Recent activity
            const recentBody = document.getElementById('recent-activity').getElementsByTagName('tbody')[0];
            recentBody.innerHTML = stats.recent.slice(0, 20).map(agent => {
                const duration = calculateDuration(agent.start_time, agent.end_time);
                return `
                    <tr>
                        <td>${agent.agent_id.substring(0, 30)}...</td>
                        <td>${agent.task}</td>
                        <td class="status-${agent.status}">${agent.status}</td>
                        <td>${duration}</td>
                        <td>${agent.output_size} bytes</td>
                        <td>${new Date(agent.created_at).toLocaleString()}</td>
                    </tr>
                `;
            }).join('');

            // Logs
            document.getElementById('logs').textContent = status.last_logs;

            // Last update time
            document.getElementById('last-update').textContent =
                'Last update: ' + new Date().toLocaleString();
        }

        function calculateDuration(start, end) {
            if (!start || !end) return 'N/A';
            try {
                const startDate = new Date(start);
                const endDate = new Date(end);
                const diffMs = endDate - startDate;
                const diffSecs = Math.floor(diffMs / 1000);
                if (diffSecs < 60) return diffSecs + 's';
                const mins = Math.floor(diffSecs / 60);
                const secs = diffSecs % 60;
                return mins + 'm ' + secs + 's';
            } catch {
                return 'N/A';
            }
        }

        async function restartAgents() {
            if (!confirm('Are you sure you want to restart the autonomous agents?')) return;

            try {
                const res = await fetch('/api/restart', { method: 'POST' });
                const data = await res.json();
                alert(data.message);
                setTimeout(fetchData, 3000);
            } catch (error) {
                alert('Error restarting agents: ' + error);
            }
        }

        function refreshData() {
            fetchData();
            countdown = 10;
        }

        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            document.querySelector('.controls button:nth-child(3)').textContent =
                autoRefresh ? '⏸️ Toggle Auto-Refresh' : '▶️ Resume Auto-Refresh';
        }

        function updateTimer() {
            if (autoRefresh) {
                countdown--;
                if (countdown <= 0) {
                    fetchData();
                    countdown = 10;
                }
            }
            document.getElementById('timer').textContent =
                `Next refresh in: ${countdown}s` + (autoRefresh ? '' : ' (paused)');
        }

        // Initial load
        fetchData();

        // Auto-refresh every 10 seconds
        countdownInterval = setInterval(updateTimer, 1000);
    </script>
</body>
</html>
"""


@app.get("/api/stats")
async def api_stats():
    """Get database statistics"""
    return get_db_stats()


@app.get("/api/status")
async def api_status():
    """Get system status"""
    return get_system_status()


@app.post("/api/restart")
async def api_restart():
    """Restart autonomous agents"""
    try:
        restart_agents()
        return {"success": True, "message": "Agents restarted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
async def api_logs(lines: int = 100):
    """Get last N lines of logs"""
    try:
        result = subprocess.run(
            ["tail", f"-{lines}", str(LOG_PATH)],
            capture_output=True,
            text=True
        )
        return {"logs": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8700)
