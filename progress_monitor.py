#!/usr/bin/env python3
"""
Real-time Progress Monitor for Autonomous Development
Shows live agent progress, percentages, worker status
"""

import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List


class ProgressMonitor:
    """Monitor autonomous agent progress in real-time"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_current_stats(self) -> Dict:
        """Get current execution statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total executions
            cursor.execute("SELECT COUNT(*) FROM agent_execution_log")
            total = cursor.fetchone()[0]

            # Completed
            cursor.execute("SELECT COUNT(*) FROM agent_execution_log WHERE status = 'completed'")
            completed = cursor.fetchone()[0]

            # Failed
            cursor.execute("SELECT COUNT(*) FROM agent_execution_log WHERE status = 'failed'")
            failed = cursor.fetchone()[0]

            # Recent executions (last 10)
            cursor.execute("""
                SELECT agent_id, task, status, start_time, end_time, outputs
                FROM agent_execution_log
                ORDER BY created_at DESC
                LIMIT 10
            """)
            recent = cursor.fetchall()

            conn.close()

            success_rate = (completed / total * 100) if total > 0 else 0

            return {
                'total': total,
                'completed': completed,
                'failed': failed,
                'success_rate': success_rate,
                'recent': [
                    {
                        'agent_id': r[0],
                        'task': r[1],
                        'status': r[2],
                        'start_time': r[3],
                        'end_time': r[4],
                        'outputs': len(json.loads(r[5])) if r[5] else 0
                    }
                    for r in recent
                ]
            }
        except Exception as e:
            return {
                'total': 0,
                'completed': 0,
                'failed': 0,
                'success_rate': 0,
                'recent': [],
                'error': str(e)
            }

    def get_live_status(self) -> str:
        """Get formatted live status string"""
        stats = self.get_current_stats()

        status = f"""
╔═══════════════════════════════════════════════════════════════════╗
║          AUTONOMOUS DEVELOPMENT - LIVE PROGRESS                   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Total Executions:    {stats['total']:>4}                                     ║
║  ✅ Completed:         {stats['completed']:>4}  ({stats['success_rate']:.1f}%)                         ║
║  ❌ Failed:            {stats['failed']:>4}  ({(stats['failed']/stats['total']*100) if stats['total'] > 0 else 0:.1f}%)                         ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  RECENT AGENT ACTIVITY                                            ║
╠═══════════════════════════════════════════════════════════════════╣
"""

        for agent in stats['recent'][:5]:
            status_icon = "✅" if agent['status'] == 'completed' else "❌"
            task_name = agent['task'][:20].ljust(20)
            status += f"║  {status_icon} {task_name} | {agent['status']:<10} | {agent['outputs']} outputs    ║\n"

        status += "╚═══════════════════════════════════════════════════════════════════╝\n"

        return status

    def format_for_tui(self) -> Dict:
        """Format data for TUI display"""
        stats = self.get_current_stats()

        return {
            'summary': f"✅ {stats['completed']} | ❌ {stats['failed']} | 📊 {stats['success_rate']:.1f}% success",
            'total': stats['total'],
            'completed': stats['completed'],
            'failed': stats['failed'],
            'success_rate': stats['success_rate'],
            'recent_tasks': [
                f"{'✅' if a['status'] == 'completed' else '❌'} {a['task']}"
                for a in stats['recent'][:5]
            ]
        }


def main():
    """CLI display of progress"""
    db_path = Path(__file__).parent.parent / "data" / "consciousness_debtor.db"
    monitor = ProgressMonitor(db_path)

    print("\n🔄 Autonomous Development Progress Monitor")
    print("=" * 70)
    print("\nPress Ctrl+C to exit\n")

    try:
        while True:
            # Clear screen
            print("\033[2J\033[H", end='')

            # Show status
            print(monitor.get_live_status())

            # Update timestamp
            print(f"\nLast update: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print("Refreshing in 5 seconds...\n")

            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.\n")


if __name__ == "__main__":
    main()
