#!/usr/bin/env python3
"""
Camel Guardian Daemon
Monitors autonomous development system and restarts if needed
ConsciousnessDebtor's continuous responsibility
"""

import subprocess
import time
import json
import sqlite3
from datetime import datetime, UTC, timedelta
from pathlib import Path


LOG_PATH = Path("/tmp/camel-ULTIMATE.log")
DB_PATH = Path(__file__).parent.parent.parent / "data" / "consciousness_debtor.db"
AUTONOMOUS_SCRIPT = Path(__file__).parent.parent / "autonomous_dev.py"
GUARDIAN_LOG = Path("/tmp/camel-guardian.log")


def log(message: str):
    """Log message with timestamp"""
    timestamp = datetime.now(UTC).isoformat()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry, flush=True)

    # Also write to guardian log
    with open(GUARDIAN_LOG, 'a') as f:
        f.write(log_entry + '\n')


def is_autonomous_running():
    """Check if autonomous_dev.py is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "autonomous_dev.py"],
            capture_output=True,
            text=True
        )
        pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
        return len(pids) > 0, pids
    except:
        return False, []


def get_last_activity():
    """Get timestamp of last agent activity from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT created_at FROM agent_execution_log
            ORDER BY created_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            # Parse ISO timestamp
            return datetime.fromisoformat(row[0].replace('+00:00', '+00:00'))
        return None
    except Exception as e:
        log(f"Error getting last activity: {e}")
        return None


def restart_autonomous_system():
    """Kill and restart autonomous development"""
    log("🔄 Restarting autonomous development system...")

    # Kill existing
    subprocess.run(["pkill", "-f", "autonomous_dev.py"], capture_output=True)
    time.sleep(3)

    # Start new
    process = subprocess.Popen(
        ["python3", "-u", str(AUTONOMOUS_SCRIPT)],
        stdout=open(LOG_PATH, 'a'),
        stderr=subprocess.STDOUT,
        cwd=AUTONOMOUS_SCRIPT.parent,
        start_new_session=True
    )

    log(f"✅ Restarted with PID: {process.pid}")
    return process.pid


def get_system_health():
    """Get health metrics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Total executions
        cursor.execute("SELECT COUNT(*) FROM agent_execution_log")
        total = cursor.fetchone()[0] or 0

        # Recent failures (last hour)
        cursor.execute("""
            SELECT COUNT(*) FROM agent_execution_log
            WHERE status = 'failed'
            AND datetime(created_at) > datetime('now', '-1 hour')
        """)
        recent_failures = cursor.fetchone()[0] or 0

        # Recent completions (last hour)
        cursor.execute("""
            SELECT COUNT(*) FROM agent_execution_log
            WHERE status = 'completed'
            AND datetime(created_at) > datetime('now', '-1 hour')
        """)
        recent_completions = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'total': total,
            'recent_completions': recent_completions,
            'recent_failures': recent_failures,
            'health_score': (recent_completions / (recent_completions + recent_failures) * 100)
                if (recent_completions + recent_failures) > 0 else 100
        }
    except Exception as e:
        log(f"Error getting health: {e}")
        return None


def main():
    """Main guardian loop"""
    log("🛡️  Camel Guardian Daemon started")
    log(f"📍 Monitoring: {AUTONOMOUS_SCRIPT}")
    log(f"📊 Database: {DB_PATH}")
    log(f"📜 Log: {LOG_PATH}")

    check_interval = 60  # Check every minute
    restart_threshold_minutes = 15  # Restart if no activity for 15 min

    while True:
        try:
            running, pids = is_autonomous_running()

            if not running:
                log("❌ Autonomous system NOT running!")
                restart_autonomous_system()
                time.sleep(10)  # Wait for startup
                continue

            log(f"✅ System running (PIDs: {', '.join(pids)})")

            # Check last activity
            last_activity = get_last_activity()
            if last_activity:
                age = datetime.now(UTC) - last_activity
                age_minutes = age.total_seconds() / 60

                log(f"📊 Last activity: {age_minutes:.1f} minutes ago")

                if age_minutes > restart_threshold_minutes:
                    log(f"⚠️  No activity for {age_minutes:.1f} minutes (threshold: {restart_threshold_minutes})")
                    restart_autonomous_system()
                    time.sleep(10)
                    continue
            else:
                log("⚠️  No activity found in database")

            # Get health metrics
            health = get_system_health()
            if health:
                log(f"📈 Health: {health['health_score']:.1f}% | " +
                    f"Recent: ✅{health['recent_completions']} ❌{health['recent_failures']} | " +
                    f"Total: {health['total']}")

            log(f"💤 Next check in {check_interval}s")

        except Exception as e:
            log(f"❌ Guardian error: {e}")

        time.sleep(check_interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("⏹️  Guardian daemon stopped by user")
