from __future__ import annotations

import argparse
import asyncio
import os
from typing import Optional

from ..core.audit_monitor import AuditMonitor


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the audit monitor to audit groups on completion")
    p.add_argument("--todo-file", required=True, help="Path to the session-local todos.json")
    p.add_argument("--task-name", required=True, help="Task/session name used for audit output under docs/<task>")
    p.add_argument("--auth-token", required=False, default=None, help="Audit auth token. If omitted, uses ENV EQUITR_AUDIT_TOKEN")
    p.add_argument("--sections-file", required=False, default=None, help="Optional JSON mapping of group_id -> [section paths]")
    p.add_argument("--poll-interval", type=float, default=10.0, help="Polling interval seconds")
    return p.parse_args()


async def _amain() -> None:
    args = _parse_args()
    token: Optional[str] = args.auth_token or os.environ.get("EQUITR_AUDIT_TOKEN")
    if not token:
        print("Warning: no EQUITR_AUDIT_TOKEN set. Use --auth-token or set ENV; write ops require it.")
        # Allow monitor to run; tools will gate write ops as needed

    monitor = AuditMonitor(
        todo_file=args.todo_file,
        task_name=args.task_name,
        auth_token=token or "",
        sections_mapping_file=args.sections_file,
        poll_interval=args.poll_interval,
    )
    print("🕵️  Audit monitor started. Watching for completed groups...")
    await monitor.run_forever()


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()


