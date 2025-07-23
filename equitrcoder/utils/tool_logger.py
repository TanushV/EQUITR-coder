"""
Tool Call Logger

Utility for logging tool calls and their results in programmatic mode.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from ..providers.openrouter import ToolCall
from ..tools.base import ToolResult


@dataclass
class ToolCallLog:
    """Log entry for a tool call."""

    timestamp: str
    session_id: Optional[str]
    tool_name: str
    tool_args: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    duration_ms: float
    error: Optional[str] = None


class ToolCallLogger:
    """Logger for tool calls and their results."""

    def __init__(self, log_file: str = "tool_calls.log", enabled: bool = False):
        self.log_file = Path(log_file)
        self.enabled = enabled
        self.logs: List[ToolCallLog] = []

        # Set up file logger
        if self.enabled:
            self.logger = logging.getLogger("tool_calls")
            self.logger.setLevel(logging.INFO)

            # Create file handler
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_tool_call(
        self,
        tool_call: ToolCall,
        result: ToolResult,
        duration_ms: float,
        session_id: Optional[str] = None,
    ):
        """Log a tool call and its result."""
        if not self.enabled:
            return

        # Parse tool arguments
        tool_args = tool_call.function.get("arguments", {})
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError:
                tool_args = {"raw_args": tool_args}

        # Create log entry
        log_entry = ToolCallLog(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            tool_name=tool_call.function["name"],
            tool_args=tool_args,
            result={
                "success": result.success,
                "content": str(result)[:1000],  # Truncate long results
                "metadata": getattr(result, "metadata", {}),
            },
            success=result.success,
            duration_ms=duration_ms,
            error=result.error if not result.success else None,
        )

        # Add to in-memory logs
        self.logs.append(log_entry)

        # Log to file
        self.logger.info(json.dumps(asdict(log_entry), indent=2))

    def get_logs(self, limit: Optional[int] = None) -> List[ToolCallLog]:
        """Get recent tool call logs."""
        if limit:
            return self.logs[-limit:]
        return self.logs.copy()

    def clear_logs(self):
        """Clear in-memory logs."""
        self.logs.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tool calls."""
        if not self.logs:
            return {}

        total_calls = len(self.logs)
        successful_calls = sum(1 for log in self.logs if log.success)
        failed_calls = total_calls - successful_calls

        # Tool usage statistics
        tool_usage = {}
        total_duration = 0

        for log in self.logs:
            tool_name = log.tool_name
            if tool_name not in tool_usage:
                tool_usage[tool_name] = {
                    "count": 0,
                    "success_count": 0,
                    "total_duration_ms": 0,
                }

            tool_usage[tool_name]["count"] += 1
            if log.success:
                tool_usage[tool_name]["success_count"] += 1
            tool_usage[tool_name]["total_duration_ms"] += log.duration_ms
            total_duration += log.duration_ms

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "total_duration_ms": total_duration,
            "average_duration_ms": total_duration / total_calls
            if total_calls > 0
            else 0,
            "tool_usage": tool_usage,
        }

    def export_logs(self, file_path: str, format: str = "json"):
        """Export logs to a file."""
        export_path = Path(file_path)

        if format == "json":
            with open(export_path, "w") as f:
                json.dump([asdict(log) for log in self.logs], f, indent=2)
        elif format == "csv":
            import csv

            with open(export_path, "w", newline="") as f:
                if self.logs:
                    writer = csv.DictWriter(f, fieldnames=asdict(self.logs[0]).keys())
                    writer.writeheader()
                    for log in self.logs:
                        writer.writerow(asdict(log))
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global tool call logger instance
tool_logger = ToolCallLogger()


def configure_tool_logger(log_file: str = "tool_calls.log", enabled: bool = False):
    """Configure the global tool call logger."""
    global tool_logger
    tool_logger = ToolCallLogger(log_file, enabled)


def get_tool_logger() -> ToolCallLogger:
    """Get the global tool call logger instance."""
    return tool_logger
