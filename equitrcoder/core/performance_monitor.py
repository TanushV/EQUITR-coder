"""
Performance Optimization Engine for EQUITR Coder

This module provides comprehensive performance monitoring, optimization,
and regression detection capabilities.

Features:
- Memory usage monitoring and optimization
- Performance profiling for bottleneck identification
- Automated performance regression detection
- Performance metrics collection and reporting
- Resource usage optimization
- Performance alerting and notifications
"""

# import os  # Unused
import gc
import logging
import sys
import threading
import time
import tracemalloc
from collections import defaultdict, deque

# import json  # Unused
# import weakref  # Unused
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict, cast

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a specific operation or time period"""

    timestamp: datetime = field(default_factory=datetime.now)
    operation_name: str = ""
    duration_ms: float = 0.0
    memory_usage_mb: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_percent: float = 0.0
    thread_count: int = 0
    gc_collections: int = 0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation_name": self.operation_name,
            "duration_ms": self.duration_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "memory_peak_mb": self.memory_peak_mb,
            "cpu_percent": self.cpu_percent,
            "thread_count": self.thread_count,
            "gc_collections": self.gc_collections,
            "custom_metrics": self.custom_metrics,
        }


@dataclass
class PerformanceBaseline:
    """Performance baseline for regression detection"""

    operation_name: str
    avg_duration_ms: float
    max_duration_ms: float
    avg_memory_mb: float
    max_memory_mb: float
    sample_count: int
    last_updated: datetime = field(default_factory=datetime.now)

    def update_with_metrics(self, metrics: PerformanceMetrics) -> None:
        """Update baseline with new metrics"""
        # Simple moving average update
        weight = 1.0 / (self.sample_count + 1)
        self.avg_duration_ms = (
            1 - weight
        ) * self.avg_duration_ms + weight * metrics.duration_ms
        self.avg_memory_mb = (
            1 - weight
        ) * self.avg_memory_mb + weight * metrics.memory_usage_mb

        # Update maximums
        self.max_duration_ms = max(self.max_duration_ms, metrics.duration_ms)
        self.max_memory_mb = max(self.max_memory_mb, metrics.memory_usage_mb)

        self.sample_count += 1
        self.last_updated = datetime.now()


@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations"""

    alert_type: str  # 'duration', 'memory', 'cpu', 'regression'
    operation_name: str
    threshold_value: float
    actual_value: float
    severity: str  # 'warning', 'error', 'critical'
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "alert_type": self.alert_type,
            "operation_name": self.operation_name,
            "threshold_value": self.threshold_value,
            "actual_value": self.actual_value,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
        }


class MemoryProfiler:
    """Memory profiling and optimization utilities"""

    def __init__(self):
        self._tracemalloc_started = False
        self._snapshots: List[Any] = []
        self._max_snapshots = 10

    def start_profiling(self) -> None:
        """Start memory profiling"""
        if not self._tracemalloc_started:
            tracemalloc.start()
            self._tracemalloc_started = True
            logger.debug("Memory profiling started")

    def stop_profiling(self) -> None:
        """Stop memory profiling"""
        if self._tracemalloc_started:
            tracemalloc.stop()
            self._tracemalloc_started = False
            logger.debug("Memory profiling stopped")

    def take_snapshot(self, description: str = "") -> None:
        """Take a memory snapshot"""
        if not self._tracemalloc_started:
            self.start_profiling()

        snapshot = tracemalloc.take_snapshot()
        self._snapshots.append(
            {
                "snapshot": snapshot,
                "description": description,
                "timestamp": datetime.now(),
            }
        )

        # Limit number of snapshots
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots.pop(0)

        logger.debug(f"Memory snapshot taken: {description}")

    def get_memory_usage(self) -> Tuple[float, float]:
        """Get current memory usage in MB"""
        process = psutil.Process()
        memory_info = process.memory_info()

        # RSS (Resident Set Size) - physical memory currently used
        current_mb = memory_info.rss / 1024 / 1024

        # Peak memory usage if available
        try:
            peak_mb = (
                process.memory_info().peak_wss / 1024 / 1024
                if hasattr(process.memory_info(), "peak_wss")
                else current_mb
            )
        except AttributeError:
            peak_mb = current_mb

        return current_mb, peak_mb

    def get_top_memory_consumers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top memory consuming code locations"""
        if not self._snapshots:
            return []

        latest_snapshot = self._snapshots[-1]["snapshot"]
        top_stats = latest_snapshot.statistics("lineno")

        consumers = []
        for stat in top_stats[:limit]:
            consumers.append(
                {
                    "filename": (
                        stat.traceback.format()[0]
                        if stat.traceback.format()
                        else "unknown"
                    ),
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count,
                }
            )

        return consumers

    def compare_snapshots(
        self, index1: int = -2, index2: int = -1
    ) -> List[Dict[str, Any]]:
        """Compare two memory snapshots"""
        if len(self._snapshots) < 2:
            return []

        snapshot1 = self._snapshots[index1]["snapshot"]
        snapshot2 = self._snapshots[index2]["snapshot"]

        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        differences = []
        for stat in top_stats[:10]:  # Top 10 differences
            differences.append(
                {
                    "filename": (
                        stat.traceback.format()[0]
                        if stat.traceback.format()
                        else "unknown"
                    ),
                    "size_diff_mb": stat.size_diff / 1024 / 1024,
                    "count_diff": stat.count_diff,
                }
            )

        return differences

    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        # Force garbage collection
        collected_objects = []
        for generation in range(3):
            collected = gc.collect()
            collected_objects.append(collected)

        # Get memory usage after optimization
        current_mb, peak_mb = self.get_memory_usage()

        return {
            "gc_collected": sum(collected_objects),
            "gc_by_generation": collected_objects,
            "memory_after_mb": current_mb,
            "peak_memory_mb": peak_mb,
        }


class PerformanceProfiler:
    """Performance profiling for bottleneck identification"""

    def __init__(self):
        self._profiles: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self._active_profiles: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    @contextmanager
    def profile_operation(
        self, operation_name: str, custom_metrics: Optional[Dict[str, Any]] = None
    ):
        """Context manager for profiling operations"""
        start_time = time.time()
        start_memory, _ = self._get_memory_usage()
        start_cpu = psutil.cpu_percent()
        start_threads = threading.active_count()
        start_gc = sum(
            gc.get_stats()[i]["collections"] for i in range(len(gc.get_stats()))
        )

        try:
            yield
        finally:
            end_time = time.time()
            end_memory, peak_memory = self._get_memory_usage()
            end_cpu = psutil.cpu_percent()
            end_threads = threading.active_count()
            end_gc = sum(
                gc.get_stats()[i]["collections"] for i in range(len(gc.get_stats()))
            )

            # Create performance metrics
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                duration_ms=(end_time - start_time) * 1000,
                memory_usage_mb=end_memory,
                memory_peak_mb=peak_memory,
                cpu_percent=(start_cpu + end_cpu) / 2,  # Average CPU usage
                thread_count=max(start_threads, end_threads),
                gc_collections=end_gc - start_gc,
                custom_metrics=custom_metrics or {},
            )

            with self._lock:
                self._profiles[operation_name].append(metrics)

                # Limit profile history
                if len(self._profiles[operation_name]) > 100:
                    self._profiles[operation_name] = self._profiles[operation_name][
                        -100:
                    ]

    def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get statistics for a specific operation"""
        with self._lock:
            profiles = self._profiles.get(operation_name, [])

            if not profiles:
                return {}

            durations = [p.duration_ms for p in profiles]
            memory_usage = [p.memory_usage_mb for p in profiles]

            return {
                "operation_name": operation_name,
                "sample_count": len(profiles),
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "avg_memory_mb": sum(memory_usage) / len(memory_usage),
                "min_memory_mb": min(memory_usage),
                "max_memory_mb": max(memory_usage),
                "last_run": profiles[-1].timestamp.isoformat(),
            }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all profiled operations"""
        with self._lock:
            return {
                op_name: self.get_operation_stats(op_name)
                for op_name in self._profiles.keys()
            }

    def identify_bottlenecks(self, threshold_ms: float = 1000) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""

        class BottleneckInfo(TypedDict):
            operation_name: str
            avg_duration_ms: float
            max_duration_ms: float
            sample_count: int
            severity: str

        bottlenecks: List[BottleneckInfo] = []

        with self._lock:
            for operation_name, profiles in self._profiles.items():
                if not profiles:
                    continue

                avg_duration = sum(p.duration_ms for p in profiles) / len(profiles)
                max_duration = max(p.duration_ms for p in profiles)

                if avg_duration > threshold_ms or max_duration > threshold_ms * 2:
                    bottlenecks.append(
                        {
                            "operation_name": operation_name,
                            "avg_duration_ms": avg_duration,
                            "max_duration_ms": max_duration,
                            "sample_count": len(profiles),
                            "severity": (
                                "critical"
                                if avg_duration > threshold_ms * 2
                                else "warning"
                            ),
                        }
                    )

        # Sort by average duration (worst first)
        bottlenecks.sort(key=lambda x: x["avg_duration_ms"], reverse=True)
        return cast(List[Dict[str, Any]], bottlenecks)

    def _get_memory_usage(self) -> Tuple[float, float]:
        """Get current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        current_mb = memory_info.rss / 1024 / 1024
        return current_mb, current_mb  # Simplified for now


class PerformanceOptimizationEngine:
    """
    Comprehensive performance optimization engine
    """

    def __init__(
        self,
        enable_memory_profiling: bool = True,
        enable_performance_profiling: bool = True,
        alert_thresholds: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize the performance optimization engine

        Args:
            enable_memory_profiling: Enable memory profiling
            enable_performance_profiling: Enable performance profiling
            alert_thresholds: Custom alert thresholds
        """
        self.enable_memory_profiling = enable_memory_profiling
        self.enable_performance_profiling = enable_performance_profiling

        # Default alert thresholds
        self.alert_thresholds = {
            "duration_ms": 5000,  # 5 seconds
            "memory_mb": 500,  # 500 MB
            "cpu_percent": 80,  # 80% CPU
            "regression_factor": 2.0,  # 2x slower than baseline
        }
        if alert_thresholds:
            self.alert_thresholds.update(alert_thresholds)

        # Components following SRP
        try:
            from .performance_analyzer import (
                AlertManager,
                BaselineManager,
                PerformanceReporter,
                RegressionDetector,
            )

            self.alert_manager: Optional[Any] = AlertManager(alert_thresholds)
            self.baseline_manager: Optional[Any] = BaselineManager()
            self.performance_reporter: Optional[Any] = PerformanceReporter()
            self.regression_detector: Optional[Any] = RegressionDetector()
        except ImportError:
            # Fallback to integrated components if analyzer module not available
            self.alert_manager = None
            self.baseline_manager = None
            self.performance_reporter = None
            self.regression_detector = None

        self.memory_profiler = MemoryProfiler() if enable_memory_profiling else None
        self.performance_profiler = (
            PerformanceProfiler() if enable_performance_profiling else None
        )

        # State (fallback for when analyzer components not available)
        self._baselines: Dict[str, PerformanceBaseline] = {}
        self._alerts: deque = deque(maxlen=1000)  # Keep last 1000 alerts
        self._metrics_history: deque = deque(maxlen=10000)  # Keep last 10000 metrics
        self._lock = threading.RLock()

        # Start memory profiling if enabled
        if self.memory_profiler:
            self.memory_profiler.start_profiling()

        logger.info("PerformanceOptimizationEngine initialized")

    @contextmanager
    def monitor_operation(
        self, operation_name: str, custom_metrics: Optional[Dict[str, Any]] = None
    ):
        """Monitor a specific operation"""
        if not self.enable_performance_profiling:
            yield
            return

        with self.performance_profiler.profile_operation(operation_name, custom_metrics) as profiler:  # type: ignore[union-attr]
            yield profiler

        # Get the latest metrics and check for alerts
        latest_metrics = self.performance_profiler._profiles[operation_name][-1]  # type: ignore[union-attr]
        self._check_alerts(latest_metrics)
        self._update_baseline(latest_metrics)

        with self._lock:
            self._metrics_history.append(latest_metrics)

    def profile_function(self, operation_name: Optional[str] = None):
        """Decorator for profiling functions"""

        def decorator(func: Callable) -> Callable:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.monitor_operation(op_name):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def take_memory_snapshot(self, description: str = "") -> None:
        """Take a memory snapshot"""
        if self.memory_profiler:
            self.memory_profiler.take_snapshot(description)

    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        if not self.memory_profiler:
            return {"error": "Memory profiling not enabled"}

        return self.memory_profiler.optimize_memory()

    def detect_regressions(
        self, operation_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Detect performance regressions"""
        with self._lock:
            if (
                self.regression_detector is not None
                and self.baseline_manager is not None
            ):
                # Use SRP components
                baselines = cast(Any, self.baseline_manager).get_all_baselines()
                recent_metrics = list(self._metrics_history)
                srp_result = cast(Any, self.regression_detector).detect_regressions(
                    baselines, recent_metrics, operation_name
                )
                # Fallback if SRP has no data or finds nothing
                if srp_result:
                    return srp_result
                # Otherwise fall back to internal baselines if available
                return self._detect_regressions_fallback(operation_name)
            else:
                # Fallback to integrated logic
                return self._detect_regressions_fallback(operation_name)

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "memory_info": self._get_memory_info(),
            "operation_stats": {},
            "bottlenecks": [],
            "regressions": [],
            "alerts": [],
            "recommendations": [],
        }

        # Get operation statistics
        if self.performance_profiler is not None:
            report["operation_stats"] = self.performance_profiler.get_all_stats()
            report["bottlenecks"] = self.performance_profiler.identify_bottlenecks()

        # Get regressions
        report["regressions"] = self.detect_regressions()

        # Get recent alerts
        with self._lock:
            report["alerts"] = [alert.to_dict() for alert in list(self._alerts)[-10:]]

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)

        return report

    def get_metrics_history(
        self, operation_name: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get metrics history"""
        with self._lock:
            metrics = list(self._metrics_history)

            if operation_name:
                metrics = [m for m in metrics if m.operation_name == operation_name]

            return [m.to_dict() for m in metrics[-limit:]]

    def clear_history(self) -> None:
        """Clear all performance history"""
        with self._lock:
            self._metrics_history.clear()
            self._alerts.clear()
            self._baselines.clear()

            if self.performance_profiler:
                self.performance_profiler._profiles.clear()

        logger.info("Performance history cleared")

    def _check_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance alerts"""
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

        # Add alerts to history
        with self._lock:
            for alert in alerts:
                self._alerts.append(alert)
                logger.warning(f"Performance alert: {alert.message}")

    def _update_baseline(self, metrics: PerformanceMetrics) -> None:
        """Update performance baseline"""
        with self._lock:
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

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "memory_available_gb": psutil.virtual_memory().available
            / 1024
            / 1024
            / 1024,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "python_version": sys.version,
            "platform": sys.platform,
        }

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        if not self.memory_profiler:
            return {}

        current_mb, peak_mb = self.memory_profiler.get_memory_usage()

        return {
            "current_usage_mb": current_mb,
            "peak_usage_mb": peak_mb,
            "top_consumers": self.memory_profiler.get_top_memory_consumers(5),
        }

    def _detect_regressions_fallback(
        self, operation_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fallback regression detection when SRP components not available"""
        regressions = []

        operations_to_check = (
            [operation_name] if operation_name else self._baselines.keys()
        )

        for op_name in operations_to_check:
            baseline = self._baselines.get(op_name)
            if not baseline:
                continue

            # Get recent metrics for this operation
            recent_metrics = [
                m
                for m in list(self._metrics_history)[-100:]
                if m.operation_name == op_name
            ]

            if not recent_metrics:
                continue

            # Calculate recent averages
            recent_avg_duration = sum(m.duration_ms for m in recent_metrics) / len(
                recent_metrics
            )
            recent_avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(
                recent_metrics
            )

            # Also consider worst-case recent value to catch immediate 3x regressions
            recent_max_duration = max(m.duration_ms for m in recent_metrics)
            recent_max_memory = max(m.memory_usage_mb for m in recent_metrics)

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

            # Include max factors to be sensitive to spikes
            max_duration_factor = (
                recent_max_duration / baseline.avg_duration_ms
                if baseline.avg_duration_ms > 0
                else 1
            )
            max_memory_factor = (
                recent_max_memory / baseline.avg_memory_mb
                if baseline.avg_memory_mb > 0
                else 1
            )

            regression_threshold = self.alert_thresholds["regression_factor"]
            triggered = (
                duration_factor > regression_threshold
                or memory_factor > regression_threshold
                or max_duration_factor > regression_threshold
                or max_memory_factor > regression_threshold
            )

            if triggered:
                regressions.append(
                    {
                        "operation_name": op_name,
                        "duration_regression_factor": max(
                            duration_factor, max_duration_factor
                        ),
                        "memory_regression_factor": max(
                            memory_factor, max_memory_factor
                        ),
                        "baseline_duration_ms": baseline.avg_duration_ms,
                        "recent_duration_ms": recent_avg_duration,
                        "baseline_memory_mb": baseline.avg_memory_mb,
                        "recent_memory_mb": recent_avg_memory,
                        "severity": (
                            "critical"
                            if max(
                                duration_factor,
                                memory_factor,
                                max_duration_factor,
                                max_memory_factor,
                            )
                            > regression_threshold * 1.5
                            else "warning"
                        ),
                    }
                )

        return regressions

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        # Memory recommendations
        memory_info = report.get("memory_info", {})
        if memory_info.get("current_usage_mb", 0) > 1000:  # > 1GB
            recommendations.append(
                "Consider optimizing memory usage - current usage is high"
            )

        # Bottleneck recommendations
        bottlenecks = report.get("bottlenecks", [])
        if bottlenecks:
            recommendations.append(
                f"Address performance bottlenecks in: {', '.join([b['operation_name'] for b in bottlenecks[:3]])}"
            )

        # Regression recommendations
        regressions = report.get("regressions", [])
        if regressions:
            recommendations.append(
                f"Investigate performance regressions in: {', '.join([r['operation_name'] for r in regressions[:3]])}"
            )

        # System recommendations
        system_info = report.get("system_info", {})
        if system_info.get("memory_percent", 0) > 80:
            recommendations.append(
                "System memory usage is high - consider adding more RAM or optimizing memory usage"
            )

        if system_info.get("cpu_percent", 0) > 80:
            recommendations.append(
                "System CPU usage is high - consider optimizing CPU-intensive operations"
            )

        return recommendations


# Global performance engine instance
_performance_engine: Optional[PerformanceOptimizationEngine] = None
_engine_lock = threading.Lock()


def get_performance_engine() -> PerformanceOptimizationEngine:
    """Get the global performance optimization engine"""
    global _performance_engine

    if _performance_engine is None:
        with _engine_lock:
            if _performance_engine is None:
                _performance_engine = PerformanceOptimizationEngine()

    return _performance_engine


def configure_performance_engine(**kwargs) -> PerformanceOptimizationEngine:
    """Configure the global performance engine"""
    global _performance_engine

    with _engine_lock:
        _performance_engine = PerformanceOptimizationEngine(**kwargs)

    return _performance_engine


def monitor_performance(
    operation_name: str, custom_metrics: Optional[Dict[str, Any]] = None
):
    """Context manager for monitoring performance"""
    engine = get_performance_engine()
    return engine.monitor_operation(operation_name, custom_metrics)


def profile_performance(operation_name: Optional[str] = None):
    """Decorator for profiling function performance"""
    engine = get_performance_engine()
    return engine.profile_function(operation_name)


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report"""
    engine = get_performance_engine()
    return engine.get_performance_report()


def optimize_memory() -> Dict[str, Any]:
    """Optimize memory usage"""
    engine = get_performance_engine()
    return engine.optimize_memory()
