"""
Performance Monitor for EQUITR Coder

This module provides performance tracking, cost monitoring, and analytics.
"""

import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation."""

    operation: str
    execution_time: float
    token_usage: int
    cost: float
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class CostAlert:
    """Cost alert when thresholds are exceeded."""

    alert_type: str
    current_value: float
    threshold: float
    message: str
    timestamp: datetime


class TrackingContext:
    """Context manager for tracking operation performance."""

    def __init__(
        self,
        monitor: "PerformanceMonitor",
        operation: str,
        metadata: Dict[str, Any] = None,
    ):
        self.monitor = monitor
        self.operation = operation
        self.metadata = metadata or {}
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        execution_time = self.end_time - self.start_time

        success = exc_type is None
        error_message = str(exc_val) if exc_val else None

        self.monitor.record_operation(
            operation=self.operation,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            metadata=self.metadata,
        )


class PerformanceMonitor:
    """Centralized performance monitoring and analytics."""

    def __init__(self, max_history: int = 10000, cost_threshold: float = 10.0):
        self.max_history = max_history
        self.cost_threshold = cost_threshold

        # Thread-safe storage
        self._lock = threading.Lock()
        self._metrics_history = deque(maxlen=max_history)
        self._cost_alerts = deque(maxlen=1000)

        # Aggregated statistics
        self._operation_stats = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "success_count": 0,
                "error_count": 0,
            }
        )

        # Current session tracking
        self._session_start = datetime.now()
        self._session_cost = 0.0
        self._session_tokens = 0

    def start_tracking(
        self, operation: str, metadata: Dict[str, Any] = None
    ) -> TrackingContext:
        """Start tracking an operation."""
        return TrackingContext(self, operation, metadata)

    def record_operation(
        self,
        operation: str,
        execution_time: float,
        success: bool = True,
        error_message: Optional[str] = None,
        token_usage: int = 0,
        cost: float = 0.0,
        metadata: Dict[str, Any] = None,
    ):
        """Record metrics for a completed operation."""
        with self._lock:
            # Create metrics record
            metrics = PerformanceMetrics(
                operation=operation,
                execution_time=execution_time,
                token_usage=token_usage,
                cost=cost,
                success=success,
                error_message=error_message,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

            # Add to history
            self._metrics_history.append(metrics)

            # Update aggregated stats
            stats = self._operation_stats[operation]
            stats["count"] += 1
            stats["total_time"] += execution_time
            stats["total_cost"] += cost
            stats["total_tokens"] += token_usage

            if success:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1

            # Update session tracking
            self._session_cost += cost
            self._session_tokens += token_usage

            # Check for cost alerts
            self._check_cost_thresholds(cost)

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        execution_time: float,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Record metrics for an LLM API call."""
        self.record_operation(
            operation="llm_call",
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            token_usage=prompt_tokens + completion_tokens,
            cost=cost,
            metadata={
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "tokens_per_second": (
                    (prompt_tokens + completion_tokens) / execution_time
                    if execution_time > 0
                    else 0
                ),
            },
        )

    def record_task_execution(
        self,
        task_type: str,
        agent_type: str,
        execution_time: float,
        cost: float,
        iterations: int,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Record metrics for a task execution."""
        self.record_operation(
            operation="task_execution",
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            cost=cost,
            metadata={
                "task_type": task_type,
                "agent_type": agent_type,
                "iterations": iterations,
                "cost_per_iteration": cost / iterations if iterations > 0 else 0,
            },
        )

    def _check_cost_thresholds(self, new_cost: float):
        """Check if cost thresholds are exceeded and create alerts."""
        # Check session cost threshold
        if self._session_cost > self.cost_threshold:
            alert = CostAlert(
                alert_type="session_threshold",
                current_value=self._session_cost,
                threshold=self.cost_threshold,
                message=f"Session cost ${self._session_cost:.4f} exceeded threshold ${self.cost_threshold:.2f}",
                timestamp=datetime.now(),
            )
            self._cost_alerts.append(alert)

        # Check single operation cost (if unusually high)
        if (
            new_cost > self.cost_threshold * 0.1
        ):  # 10% of threshold for single operation
            alert = CostAlert(
                alert_type="high_single_cost",
                current_value=new_cost,
                threshold=self.cost_threshold * 0.1,
                message=f"Single operation cost ${new_cost:.4f} is unusually high",
                timestamp=datetime.now(),
            )
            self._cost_alerts.append(alert)

    def get_performance_report(self, timeframe_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)

        with self._lock:
            # Filter metrics by timeframe
            recent_metrics = [
                m for m in self._metrics_history if m.timestamp >= cutoff_time
            ]

            if not recent_metrics:
                return {
                    "timeframe_hours": timeframe_hours,
                    "total_operations": 0,
                    "message": "No operations in the specified timeframe",
                }

            # Calculate summary statistics
            total_operations = len(recent_metrics)
            successful_operations = sum(1 for m in recent_metrics if m.success)
            total_cost = sum(m.cost for m in recent_metrics)
            total_tokens = sum(m.token_usage for m in recent_metrics)
            total_time = sum(m.execution_time for m in recent_metrics)

            # Operation breakdown
            operation_breakdown = defaultdict(
                lambda: {
                    "count": 0,
                    "avg_time": 0.0,
                    "total_cost": 0.0,
                    "success_rate": 0.0,
                }
            )

            for metrics in recent_metrics:
                op_stats = operation_breakdown[metrics.operation]
                op_stats["count"] += 1
                op_stats["total_cost"] += metrics.cost

                # Calculate running averages
                if op_stats["count"] == 1:
                    op_stats["avg_time"] = metrics.execution_time
                    op_stats["success_rate"] = 1.0 if metrics.success else 0.0
                else:
                    # Update running average
                    op_stats["avg_time"] = (
                        op_stats["avg_time"] * (op_stats["count"] - 1)
                        + metrics.execution_time
                    ) / op_stats["count"]

                    # Update success rate
                    success_count = sum(
                        1
                        for m in recent_metrics
                        if m.operation == metrics.operation and m.success
                    )
                    op_stats["success_rate"] = success_count / op_stats["count"]

            # Recent alerts
            recent_alerts = [
                alert for alert in self._cost_alerts if alert.timestamp >= cutoff_time
            ]

            return {
                "timeframe_hours": timeframe_hours,
                "summary": {
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "success_rate": (
                        successful_operations / total_operations
                        if total_operations > 0
                        else 0
                    ),
                    "total_cost": total_cost,
                    "total_tokens": total_tokens,
                    "total_execution_time": total_time,
                    "avg_cost_per_operation": (
                        total_cost / total_operations if total_operations > 0 else 0
                    ),
                    "avg_time_per_operation": (
                        total_time / total_operations if total_operations > 0 else 0
                    ),
                },
                "operation_breakdown": dict(operation_breakdown),
                "session_stats": {
                    "session_duration": (
                        datetime.now() - self._session_start
                    ).total_seconds(),
                    "session_cost": self._session_cost,
                    "session_tokens": self._session_tokens,
                },
                "alerts": [asdict(alert) for alert in recent_alerts],
                "cost_efficiency": {
                    "tokens_per_dollar": (
                        total_tokens / total_cost if total_cost > 0 else 0
                    ),
                    "operations_per_dollar": (
                        total_operations / total_cost if total_cost > 0 else 0
                    ),
                },
            }

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary and budget status."""
        with self._lock:
            return {
                "session_cost": self._session_cost,
                "cost_threshold": self.cost_threshold,
                "threshold_usage_percent": (
                    (self._session_cost / self.cost_threshold * 100)
                    if self.cost_threshold > 0
                    else 0
                ),
                "remaining_budget": max(0, self.cost_threshold - self._session_cost),
                "session_tokens": self._session_tokens,
                "recent_alerts": len(
                    [
                        a
                        for a in self._cost_alerts
                        if a.timestamp >= datetime.now() - timedelta(hours=1)
                    ]
                ),
            }

    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by model."""
        with self._lock:
            model_stats = defaultdict(
                lambda: {
                    "calls": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "avg_response_time": 0.0,
                    "success_rate": 0.0,
                }
            )

            llm_metrics = [
                m for m in self._metrics_history if m.operation == "llm_call"
            ]

            for metrics in llm_metrics:
                model = metrics.metadata.get("model", "unknown")
                stats = model_stats[model]

                stats["calls"] += 1
                stats["total_cost"] += metrics.cost
                stats["total_tokens"] += metrics.token_usage

                # Update running averages
                if stats["calls"] == 1:
                    stats["avg_response_time"] = metrics.execution_time
                    stats["success_rate"] = 1.0 if metrics.success else 0.0
                else:
                    stats["avg_response_time"] = (
                        stats["avg_response_time"] * (stats["calls"] - 1)
                        + metrics.execution_time
                    ) / stats["calls"]

                    success_count = sum(
                        1
                        for m in llm_metrics
                        if m.metadata.get("model") == model and m.success
                    )
                    stats["success_rate"] = success_count / stats["calls"]

            return dict(model_stats)

    def export_metrics(self, filepath: str, format: str = "json"):
        """Export metrics to file."""
        with self._lock:
            data = {
                "export_timestamp": datetime.now().isoformat(),
                "session_start": self._session_start.isoformat(),
                "metrics": [asdict(m) for m in self._metrics_history],
                "operation_stats": dict(self._operation_stats),
                "cost_alerts": [asdict(a) for a in self._cost_alerts],
            }

            filepath = Path(filepath)

            if format.lower() == "json":
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")

    def reset_session(self):
        """Reset session-level tracking."""
        with self._lock:
            self._session_start = datetime.now()
            self._session_cost = 0.0
            self._session_tokens = 0

    def clear_history(self):
        """Clear all performance history."""
        with self._lock:
            self._metrics_history.clear()
            self._cost_alerts.clear()
            self._operation_stats.clear()
            self.reset_session()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
