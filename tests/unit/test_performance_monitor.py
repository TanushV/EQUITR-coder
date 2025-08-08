"""
Unit tests for Performance Monitor

Tests the performance monitoring system including:
- Performance metrics collection
- Memory profiling
- Performance profiling
- Regression detection
- Alert generation
- Optimization recommendations
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from datetime import datetime

from equitrcoder.core.performance_monitor import (
    PerformanceMetrics,
    PerformanceBaseline,
    PerformanceAlert,
    MemoryProfiler,
    PerformanceProfiler,
    PerformanceOptimizationEngine,
    get_performance_engine,
    configure_performance_engine,
    monitor_performance,
    profile_performance,
    get_performance_report,
    optimize_memory
)


class TestPerformanceMetrics:
    """Test suite for PerformanceMetrics"""
    
    def test_metrics_creation(self):
        """Test PerformanceMetrics creation and default values"""
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            duration_ms=100.5,
            memory_usage_mb=50.2
        )
        
        assert metrics.operation_name == "test_operation"
        assert metrics.duration_ms == 100.5
        assert metrics.memory_usage_mb == 50.2
        assert isinstance(metrics.timestamp, datetime)
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary"""
        metrics = PerformanceMetrics(
            operation_name="test_op",
            duration_ms=200.0,
            memory_usage_mb=100.0,
            custom_metrics={"custom_value": 42}
        )
        
        result = metrics.to_dict()
        
        assert result['operation_name'] == "test_op"
        assert result['duration_ms'] == 200.0
        assert result['memory_usage_mb'] == 100.0
        assert result['custom_metrics']['custom_value'] == 42
        assert 'timestamp' in result


class TestPerformanceBaseline:
    """Test suite for PerformanceBaseline"""
    
    def test_baseline_creation(self):
        """Test PerformanceBaseline creation"""
        baseline = PerformanceBaseline(
            operation_name="test_op",
            avg_duration_ms=100.0,
            max_duration_ms=150.0,
            avg_memory_mb=50.0,
            max_memory_mb=75.0,
            sample_count=10
        )
        
        assert baseline.operation_name == "test_op"
        assert baseline.avg_duration_ms == 100.0
        assert baseline.sample_count == 10
    
    def test_baseline_update(self):
        """Test updating baseline with new metrics"""
        baseline = PerformanceBaseline(
            operation_name="test_op",
            avg_duration_ms=100.0,
            max_duration_ms=150.0,
            avg_memory_mb=50.0,
            max_memory_mb=75.0,
            sample_count=1
        )
        
        new_metrics = PerformanceMetrics(
            operation_name="test_op",
            duration_ms=200.0,
            memory_usage_mb=100.0
        )
        
        baseline.update_with_metrics(new_metrics)
        
        # Should be moving average
        assert baseline.avg_duration_ms == 150.0  # (100 + 200) / 2
        assert baseline.avg_memory_mb == 75.0     # (50 + 100) / 2
        assert baseline.max_duration_ms == 200.0  # New maximum
        assert baseline.sample_count == 2


class TestPerformanceAlert:
    """Test suite for PerformanceAlert"""
    
    def test_alert_creation(self):
        """Test PerformanceAlert creation"""
        alert = PerformanceAlert(
            alert_type="duration",
            operation_name="slow_operation",
            threshold_value=1000.0,
            actual_value=2000.0,
            severity="warning",
            message="Operation exceeded threshold"
        )
        
        assert alert.alert_type == "duration"
        assert alert.operation_name == "slow_operation"
        assert alert.threshold_value == 1000.0
        assert alert.actual_value == 2000.0
        assert alert.severity == "warning"
    
    def test_alert_to_dict(self):
        """Test converting alert to dictionary"""
        alert = PerformanceAlert(
            alert_type="memory",
            operation_name="memory_intensive",
            threshold_value=500.0,
            actual_value=750.0,
            severity="critical"
        )
        
        result = alert.to_dict()
        
        assert result['alert_type'] == "memory"
        assert result['operation_name'] == "memory_intensive"
        assert result['threshold_value'] == 500.0
        assert result['actual_value'] == 750.0
        assert result['severity'] == "critical"
        assert 'timestamp' in result


class TestMemoryProfiler:
    """Test suite for MemoryProfiler"""
    
    def test_profiler_initialization(self):
        """Test MemoryProfiler initialization"""
        profiler = MemoryProfiler()
        
        assert not profiler._tracemalloc_started
        assert len(profiler._snapshots) == 0
    
    @patch('tracemalloc.start')
    @patch('tracemalloc.stop')
    def test_start_stop_profiling(self, mock_stop, mock_start):
        """Test starting and stopping profiling"""
        profiler = MemoryProfiler()
        
        profiler.start_profiling()
        assert profiler._tracemalloc_started
        mock_start.assert_called_once()
        
        profiler.stop_profiling()
        assert not profiler._tracemalloc_started
        mock_stop.assert_called_once()
    
    @patch('psutil.Process')
    def test_get_memory_usage(self, mock_process):
        """Test getting memory usage"""
        # Mock memory info
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100 MB in bytes
        
        # Mock the process and memory_info method
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process.return_value = mock_process_instance
        
        # Mock hasattr to return False so peak_mb defaults to current_mb
        with patch('builtins.hasattr', return_value=False):
            profiler = MemoryProfiler()
            current_mb, peak_mb = profiler.get_memory_usage()
        
        assert current_mb == 100.0
        assert peak_mb == 100.0
    
    @patch('gc.collect')
    def test_optimize_memory(self, mock_gc_collect):
        """Test memory optimization"""
        mock_gc_collect.side_effect = [10, 5, 2]  # Objects collected per generation
        
        profiler = MemoryProfiler()
        
        with patch.object(profiler, 'get_memory_usage', return_value=(50.0, 60.0)):
            result = profiler.optimize_memory()
        
        assert result['gc_collected'] == 17  # 10 + 5 + 2
        assert result['gc_by_generation'] == [10, 5, 2]
        assert result['memory_after_mb'] == 50.0
        assert mock_gc_collect.call_count == 3


class TestPerformanceProfiler:
    """Test suite for PerformanceProfiler"""
    
    def test_profiler_initialization(self):
        """Test PerformanceProfiler initialization"""
        profiler = PerformanceProfiler()
        
        assert len(profiler._profiles) == 0
        assert len(profiler._active_profiles) == 0
    
    @patch('psutil.cpu_percent', return_value=50.0)
    @patch('threading.active_count', return_value=5)
    def test_profile_operation(self, mock_thread_count, mock_cpu):
        """Test profiling an operation"""
        profiler = PerformanceProfiler()
        
        with patch.object(profiler, '_get_memory_usage', return_value=(100.0, 120.0)):
            with profiler.profile_operation("test_operation"):
                time.sleep(0.01)  # Simulate work
        
        # Check that metrics were recorded
        assert "test_operation" in profiler._profiles
        assert len(profiler._profiles["test_operation"]) == 1
        
        metrics = profiler._profiles["test_operation"][0]
        assert metrics.operation_name == "test_operation"
        assert metrics.duration_ms > 0
        assert metrics.memory_usage_mb == 100.0
    
    def test_get_operation_stats(self):
        """Test getting operation statistics"""
        profiler = PerformanceProfiler()
        
        # Add some mock metrics
        metrics1 = PerformanceMetrics(operation_name="test_op", duration_ms=100.0, memory_usage_mb=50.0)
        metrics2 = PerformanceMetrics(operation_name="test_op", duration_ms=200.0, memory_usage_mb=75.0)
        
        profiler._profiles["test_op"] = [metrics1, metrics2]
        
        stats = profiler.get_operation_stats("test_op")
        
        assert stats['operation_name'] == "test_op"
        assert stats['sample_count'] == 2
        assert stats['avg_duration_ms'] == 150.0  # (100 + 200) / 2
        assert stats['min_duration_ms'] == 100.0
        assert stats['max_duration_ms'] == 200.0
        assert stats['avg_memory_mb'] == 62.5    # (50 + 75) / 2
    
    def test_identify_bottlenecks(self):
        """Test identifying performance bottlenecks"""
        profiler = PerformanceProfiler()
        
        # Add metrics for different operations
        fast_metrics = PerformanceMetrics(operation_name="fast_op", duration_ms=50.0)
        slow_metrics = PerformanceMetrics(operation_name="slow_op", duration_ms=2500.0)  # > 2x threshold for critical
        
        profiler._profiles["fast_op"] = [fast_metrics]
        profiler._profiles["slow_op"] = [slow_metrics]
        
        bottlenecks = profiler.identify_bottlenecks(threshold_ms=1000.0)
        
        assert len(bottlenecks) == 1
        assert bottlenecks[0]['operation_name'] == "slow_op"
        assert bottlenecks[0]['avg_duration_ms'] == 2500.0
        assert bottlenecks[0]['severity'] == 'critical'


class TestPerformanceOptimizationEngine:
    """Test suite for PerformanceOptimizationEngine"""
    
    def test_engine_initialization(self):
        """Test PerformanceOptimizationEngine initialization"""
        engine = PerformanceOptimizationEngine(
            enable_memory_profiling=True,
            enable_performance_profiling=True
        )
        
        assert engine.enable_memory_profiling
        assert engine.enable_performance_profiling
        assert engine.memory_profiler is not None
        assert engine.performance_profiler is not None
        assert 'duration_ms' in engine.alert_thresholds
    
    def test_engine_disabled_profiling(self):
        """Test engine with profiling disabled"""
        engine = PerformanceOptimizationEngine(
            enable_memory_profiling=False,
            enable_performance_profiling=False
        )
        
        assert not engine.enable_memory_profiling
        assert not engine.enable_performance_profiling
        assert engine.memory_profiler is None
        assert engine.performance_profiler is None
    
    @patch('psutil.cpu_percent', return_value=50.0)
    @patch('threading.active_count', return_value=5)
    def test_monitor_operation(self, mock_thread_count, mock_cpu):
        """Test monitoring an operation"""
        engine = PerformanceOptimizationEngine()
        
        with patch.object(engine.performance_profiler, '_get_memory_usage', return_value=(100.0, 120.0)):
            with engine.monitor_operation("test_operation"):
                time.sleep(0.01)  # Simulate work
        
        # Check that metrics were recorded
        assert len(engine._metrics_history) == 1
        metrics = list(engine._metrics_history)[0]
        assert metrics.operation_name == "test_operation"
    
    def test_profile_function_decorator(self):
        """Test function profiling decorator"""
        engine = PerformanceOptimizationEngine()
        
        @engine.profile_function("decorated_function")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        with patch.object(engine.performance_profiler, '_get_memory_usage', return_value=(100.0, 120.0)):
            result = test_function()
        
        assert result == "result"
        assert len(engine._metrics_history) == 1
        assert list(engine._metrics_history)[0].operation_name == "decorated_function"
    
    def test_detect_regressions(self):
        """Test regression detection"""
        engine = PerformanceOptimizationEngine()
        
        # Create baseline
        baseline_metrics = PerformanceMetrics(
            operation_name="test_op",
            duration_ms=100.0,
            memory_usage_mb=50.0
        )
        engine._update_baseline(baseline_metrics)
        
        # Add recent metrics that show regression
        regression_metrics = PerformanceMetrics(
            operation_name="test_op",
            duration_ms=300.0,  # 3x slower
            memory_usage_mb=150.0  # 3x more memory
        )
        engine._metrics_history.append(regression_metrics)
        
        regressions = engine.detect_regressions("test_op")
        
        assert len(regressions) == 1
        assert regressions[0]['operation_name'] == "test_op"
        assert regressions[0]['duration_regression_factor'] == 3.0
        assert regressions[0]['memory_regression_factor'] == 3.0
    
    def test_alert_generation(self):
        """Test alert generation"""
        engine = PerformanceOptimizationEngine(alert_thresholds={'duration_ms': 100.0})
        
        # Create metrics that exceed threshold
        slow_metrics = PerformanceMetrics(
            operation_name="slow_op",
            duration_ms=200.0  # Exceeds 100ms threshold
        )
        
        engine._check_alerts(slow_metrics)
        
        assert len(engine._alerts) == 1
        alert = list(engine._alerts)[0]
        assert alert.alert_type == "duration"
        assert alert.operation_name == "slow_op"
        assert alert.actual_value == 200.0
    
    @patch('psutil.cpu_count', return_value=8)
    @patch('psutil.cpu_percent', return_value=25.0)
    @patch('psutil.virtual_memory')
    def test_get_performance_report(self, mock_memory, mock_cpu, mock_cpu_count):
        """Test generating performance report"""
        # Mock memory info
        mock_memory.return_value.total = 16 * 1024 * 1024 * 1024  # 16GB
        mock_memory.return_value.available = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.return_value.percent = 50.0
        
        engine = PerformanceOptimizationEngine()
        
        # Add some test data
        metrics = PerformanceMetrics(operation_name="test_op", duration_ms=100.0)
        engine._metrics_history.append(metrics)
        
        report = engine.get_performance_report()
        
        assert 'timestamp' in report
        assert 'system_info' in report
        assert 'memory_info' in report
        assert 'operation_stats' in report
        assert 'bottlenecks' in report
        assert 'regressions' in report
        assert 'alerts' in report
        assert 'recommendations' in report
        
        # Check system info
        assert report['system_info']['cpu_count'] == 8
        assert report['system_info']['memory_total_gb'] == 16.0
    
    def test_clear_history(self):
        """Test clearing performance history"""
        engine = PerformanceOptimizationEngine()
        
        # Add some data
        metrics = PerformanceMetrics(operation_name="test_op")
        engine._metrics_history.append(metrics)
        engine._baselines["test_op"] = PerformanceBaseline(
            operation_name="test_op",
            avg_duration_ms=100.0,
            max_duration_ms=150.0,
            avg_memory_mb=50.0,
            max_memory_mb=75.0,
            sample_count=1
        )
        
        assert len(engine._metrics_history) == 1
        assert len(engine._baselines) == 1
        
        engine.clear_history()
        
        assert len(engine._metrics_history) == 0
        assert len(engine._baselines) == 0


class TestGlobalFunctions:
    """Test suite for global convenience functions"""
    
    def test_get_performance_engine(self):
        """Test getting global performance engine"""
        engine1 = get_performance_engine()
        engine2 = get_performance_engine()
        
        # Should return the same instance (singleton)
        assert engine1 is engine2
    
    def test_configure_performance_engine(self):
        """Test configuring global performance engine"""
        engine = configure_performance_engine(
            enable_memory_profiling=False,
            alert_thresholds={'duration_ms': 2000.0}
        )
        
        assert not engine.enable_memory_profiling
        assert engine.alert_thresholds['duration_ms'] == 2000.0
    
    @patch('psutil.cpu_percent', return_value=50.0)
    @patch('threading.active_count', return_value=5)
    def test_monitor_performance(self, mock_thread_count, mock_cpu):
        """Test global monitor_performance function"""
        # Clear any existing engine
        import equitrcoder.core.performance_monitor
        equitrcoder.core.performance_monitor._performance_engine = None
        
        with monitor_performance("global_test_operation"):
            time.sleep(0.01)
        
        engine = get_performance_engine()
        assert len(engine._metrics_history) >= 1
    
    def test_profile_performance_decorator(self):
        """Test global profile_performance decorator"""
        @profile_performance("global_decorated_function")
        def test_function():
            return "decorated_result"
        
        result = test_function()
        assert result == "decorated_result"
    
    def test_get_performance_report_global(self):
        """Test global get_performance_report function"""
        report = get_performance_report()
        
        assert isinstance(report, dict)
        assert 'timestamp' in report
        assert 'system_info' in report


if __name__ == '__main__':
    pytest.main([__file__])