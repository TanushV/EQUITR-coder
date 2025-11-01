"""
Performance Analysis Components for EQUITR Coder

This module provides focused performance analysis components that follow
the single responsibility principle.

Components:
- RegressionDetector: Detects performance regressions
- PerformanceReporter: Generates performance reports
- AlertManager: Manages performance alerts
- RecommendationEngine: Generates optimization recommendations
"""

import logging
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from .performance_monitor import (
    PerformanceAlert,
    PerformanceBaseline,
    PerformanceMetrics,
)

logger = logging.getLogger(__name__)


class RegressionDetector:
    """
    Detects performance regressions by comparing current metrics with baselines
    """

    def __init__(self, regression_threshold: float = 2.0):
        """
        Initialize regression detector

        Args:
            regression_threshold: Factor by which performance must degrade to be considered a regression
        """
        self.regression_threshold = regression_threshold

    def detect_regressions(
        self,
        baselines: Dict[str, PerformanceBaseline],
        recent_metrics: List[PerformanceMetrics],
        operation_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect performance regressions

        Args:
            baselines: Performance baselines by operation name
            recent_metrics: Recent performance metrics
            operation_name: Specific operation to check (None for all)

        Returns:
            List of detected regressions
        """
        regressions = []

        operations_to_check = [operation_name] if operation_name else baselines.keys()

        for op_name in operations_to_check:
            baseline = baselines.get(op_name)
            if not baseline:
                continue

            # Get recent metrics for this operation
            op_metrics = [
                m for m in recent_metrics[-100:] if m.operation_name == op_name
            ]
            if not op_metrics:
                continue

            # Calculate recent averages
            recent_avg_duration = sum(m.duration_ms for m in op_metrics) / len(
                op_metrics
            )
            recent_avg_memory = sum(m.memory_usage_mb for m in op_metrics) / len(
                op_metrics
            )

            # Check for regressions
            duration_factor = (
                recent_avg_duration / baseline.avg_duration_ms
                if baseline.avg_duration_ms > 0
                else 1
            )
            memory_factor = (
                recent_avg_memory / baseline.avg_memory_mb
                if baseline.avg_memory_mb > 0
                else 1
            )

            if (
                duration_factor > self.regression_threshold
                or memory_factor > self.regression_threshold
            ):
                regressions.append(
                    {
                        "operation_name": op_name,
                        "duration_regression_factor": duration_factor,
                        "memory_regression_factor": memory_factor,
                        "baseline_duration_ms": baseline.avg_duration_ms,
                        "recent_duration_ms": recent_avg_duration,
                        "baseline_memory_mb": baseline.avg_memory_mb,
                        "recent_memory_mb": recent_avg_memory,
                        "severity": (
                            "critical"
                            if max(duration_factor, memory_factor)
                            > self.regression_threshold * 1.5
                            else "warning"
                        ),
                    }
                )

        return regressions


class AlertManager:
    """
    Manages performance alerts and notifications
    """

    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize alert manager

        Args:
            alert_thresholds: Custom alert thresholds
        """
        self.alert_thresholds = alert_thresholds or {
            "duration_ms": 5000,
            "memory_mb": 500,
            "cpu_percent": 80,
        }
        self._alerts: deque = deque(maxlen=1000)

    def check_alerts(self, metrics: PerformanceMetrics) -> List[PerformanceAlert]:
        """
        Check metrics against thresholds and generate alerts

        Args:
            metrics: Performance metrics to check

        Returns:
            List of generated alerts
        """
        alerts = []

        # Duration alert
        if metrics.duration_ms > self.alert_thresholds["duration_ms"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="duration",
                    operation_name=metrics.operation_name,
                    threshold_value=self.alert_thresholds["duration_ms"],
                    actual_value=metrics.duration_ms,
                    severity=(
                        "warning"
                        if metrics.duration_ms
                        < self.alert_thresholds["duration_ms"] * 2
                        else "critical"
                    ),
                    message=f"Operation took {metrics.duration_ms:.1f}ms (threshold: {self.alert_thresholds['duration_ms']}ms)",
                )
            )

        # Memory alert
        if metrics.memory_usage_mb > self.alert_thresholds["memory_mb"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="memory",
                    operation_name=metrics.operation_name,
                    threshold_value=self.alert_thresholds["memory_mb"],
                    actual_value=metrics.memory_usage_mb,
                    severity=(
                        "warning"
                        if metrics.memory_usage_mb
                        < self.alert_thresholds["memory_mb"] * 2
                        else "critical"
                    ),
                    message=f"Operation used {metrics.memory_usage_mb:.1f}MB (threshold: {self.alert_thresholds['memory_mb']}MB)",
                )
            )

        # CPU alert
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append(
                PerformanceAlert(
                    alert_type="cpu",
                    operation_name=metrics.operation_name,
                    threshold_value=self.alert_thresholds["cpu_percent"],
                    actual_value=metrics.cpu_percent,
                    severity="warning",
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}% (threshold: {self.alert_thresholds['cpu_percent']}%)",
                )
            )

        # Store alerts
        for alert in alerts:
            self._alerts.append(alert)
            logger.warning(f"Performance alert: {alert.message}")

        return alerts

    def get_recent_alerts(self, limit: int = 10) -> List[PerformanceAlert]:
        """
        Get recent alerts

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts
        """
        return list(self._alerts)[-limit:]

    def clear_alerts(self) -> None:
        """Clear all alerts"""
        self._alerts.clear()


class RecommendationEngine:
    """
    Generates performance optimization recommendations
    """

    def generate_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """
        Generate performance recommendations based on report data

        Args:
            report_data: Performance report data

        Returns:
            List of recommendations
        """
        recommendations = []

        # Memory recommendations
        memory_info = report_data.get("memory_info", {})
        if memory_info.get("current_usage_mb", 0) > 1000:  # > 1GB
            recommendations.append(
                "Consider optimizing memory usage - current usage is high"
            )

        # Bottleneck recommendations
        bottlenecks = report_data.get("bottlenecks", [])
        if bottlenecks:
            recommendations.append(
                f"Address performance bottlenecks in: {', '.join([b['operation_name'] for b in bottlenecks[:3]])}"
            )

        # Regression recommendations
        regressions = report_data.get("regressions", [])
        if regressions:
            recommendations.append(
                f"Investigate performance regressions in: {', '.join([r['operation_name'] for r in regressions[:3]])}"
            )

        # System recommendations
        system_info = report_data.get("system_info", {})
        if system_info.get("memory_percent", 0) > 80:
            recommendations.append(
                "System memory usage is high - consider adding more RAM or optimizing memory usage"
            )

        if system_info.get("cpu_percent", 0) > 80:
            recommendations.append(
                "System CPU usage is high - consider optimizing CPU-intensive operations"
            )

        return recommendations


class PerformanceReporter:
    """
    Generates comprehensive performance reports
    """

    def __init__(self):
        self.regression_detector = RegressionDetector()
        self.recommendation_engine = RecommendationEngine()

    def generate_report(
        self,
        system_info: Dict[str, Any],
        memory_info: Dict[str, Any],
        operation_stats: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
        baselines: Dict[str, PerformanceBaseline],
        recent_metrics: List[PerformanceMetrics],
        recent_alerts: List[PerformanceAlert],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report

        Args:
            system_info: System information
            memory_info: Memory information
            operation_stats: Operation statistics
            bottlenecks: Performance bottlenecks
            baselines: Performance baselines
            recent_metrics: Recent performance metrics
            recent_alerts: Recent alerts

        Returns:
            Comprehensive performance report
        """
        # Detect regressions
        regressions = self.regression_detector.detect_regressions(
            baselines, recent_metrics
        )

        # Build report data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": system_info,
            "memory_info": memory_info,
            "operation_stats": operation_stats,
            "bottlenecks": bottlenecks,
            "regressions": regressions,
            "alerts": [alert.to_dict() for alert in recent_alerts],
            "recent_metrics": recent_metrics,
        }

        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(
            report_data
        )
        report_data["recommendations"] = recommendations

        return report_data


class BaselineManager:
    """
    Manages performance baselines for regression detection
    """

    def __init__(self):
        self._baselines: Dict[str, PerformanceBaseline] = {}

    def update_baseline(self, metrics: PerformanceMetrics) -> None:
        """
        Update performance baseline with new metrics

        Args:
            metrics: Performance metrics to incorporate
        """
        baseline = self._baselines.get(metrics.operation_name)

        if baseline:
            baseline.update_with_metrics(metrics)
        else:
            self._baselines[metrics.operation_name] = PerformanceBaseline(
                operation_name=metrics.operation_name,
                avg_duration_ms=metrics.duration_ms,
                max_duration_ms=metrics.duration_ms,
                avg_memory_mb=metrics.memory_usage_mb,
                max_memory_mb=metrics.memory_usage_mb,
                sample_count=1,
            )

    def get_baseline(self, operation_name: str) -> Optional[PerformanceBaseline]:
        """
        Get baseline for specific operation

        Args:
            operation_name: Operation name

        Returns:
            Performance baseline or None if not found
        """
        return self._baselines.get(operation_name)

    def get_all_baselines(self) -> Dict[str, PerformanceBaseline]:
        """
        Get all performance baselines

        Returns:
            Dictionary of all baselines
        """
        return self._baselines.copy()

    def clear_baselines(self) -> None:
        """Clear all baselines"""
        self._baselines.clear()
        logger.info("Performance baselines cleared")
