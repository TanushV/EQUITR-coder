"""
Configuration classes for comprehensive mode testing.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class ComprehensiveTestConfig:
    """Configuration for comprehensive mode testing."""
    
    # Model configuration
    model: str = "moonshot/kimi-k2-0711-preview"
    
    # Cost and iteration limits
    max_cost_per_test: float = 5.0
    max_iterations_per_test: int = 20
    timeout_seconds: int = 300
    
    # Test task configuration
    test_task: str = "Create a simple calculator application with basic arithmetic operations (add, subtract, multiply, divide), a command-line interface, input validation, error handling for division by zero, and comprehensive unit tests"
    
    # Multi-agent configuration
    parallel_agents_count: int = 4
    max_workers: int = 3
    
    # Testing behavior
    enable_auto_fix: bool = True
    preserve_artifacts: bool = True
    cleanup_on_success: bool = False
    retry_failed_tests: bool = True
    max_retries: int = 2
    
    # Expected outputs for validation
    expected_files: List[str] = field(default_factory=lambda: [
        "requirements.md",
        "design.md", 
        "todos.md",
        "calculator.py",
        "test_calculator.py"
    ])
    expected_todos_min: int = 5
    expected_todos_max: int = 20
    
    # Output configuration
    base_test_dir: str = "testing/comprehensive_mode_tests"
    results_format: str = "both"  # "json", "markdown", "both"
    verbose_output: bool = True
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.max_cost_per_test <= 0:
            raise ValueError("max_cost_per_test must be positive")
        if self.max_iterations_per_test <= 0:
            raise ValueError("max_iterations_per_test must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.parallel_agents_count <= 0:
            raise ValueError("parallel_agents_count must be positive")
        if not self.test_task.strip():
            raise ValueError("test_task cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'model': self.model,
            'max_cost_per_test': self.max_cost_per_test,
            'max_iterations_per_test': self.max_iterations_per_test,
            'timeout_seconds': self.timeout_seconds,
            'test_task': self.test_task,
            'parallel_agents_count': self.parallel_agents_count,
            'max_workers': self.max_workers,
            'enable_auto_fix': self.enable_auto_fix,
            'preserve_artifacts': self.preserve_artifacts,
            'cleanup_on_success': self.cleanup_on_success,
            'retry_failed_tests': self.retry_failed_tests,
            'max_retries': self.max_retries,
            'expected_files': self.expected_files,
            'expected_todos_min': self.expected_todos_min,
            'expected_todos_max': self.expected_todos_max,
            'base_test_dir': self.base_test_dir,
            'results_format': self.results_format,
            'verbose_output': self.verbose_output
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComprehensiveTestConfig':
        """Create configuration from dictionary."""
        return cls(**data)
    
    def get_test_run_dir(self, run_id: str) -> Path:
        """Get the test run directory path."""
        return Path(self.base_test_dir) / f"run_{run_id}"
    
    def get_mode_test_dir(self, run_id: str, mode: str) -> Path:
        """Get the mode-specific test directory path."""
        return self.get_test_run_dir(run_id) / f"{mode}_envs"
    
    def validate_environment(self) -> List[str]:
        """Validate the testing environment and return any issues."""
        issues = []
        
        # Check if base test directory can be created
        try:
            base_dir = Path(self.base_test_dir)
            base_dir.mkdir(parents=True, exist_ok=True)
            if not base_dir.exists():
                issues.append(f"Cannot create base test directory: {self.base_test_dir}")
        except Exception as e:
            issues.append(f"Error creating base test directory: {str(e)}")
        
        # Check model format
        if not self.model or '/' not in self.model:
            issues.append(f"Invalid model format: {self.model}")
        
        # Check resource limits are reasonable
        if self.max_cost_per_test > 50.0:
            issues.append(f"max_cost_per_test seems very high: ${self.max_cost_per_test}")
        
        if self.timeout_seconds > 3600:  # 1 hour
            issues.append(f"timeout_seconds seems very high: {self.timeout_seconds}s")
        
        return issues


@dataclass
class TestEnvironmentConfig:
    """Configuration for individual test environments."""
    
    env_id: str
    mode: str  # "single", "multi_sequential", "multi_parallel"
    base_dir: Path
    model: str
    max_cost: float
    max_iterations: int
    timeout_seconds: int
    
    def get_env_dir(self) -> Path:
        """Get the environment directory path."""
        return self.base_dir / self.env_id
    
    def get_docs_dir(self) -> Path:
        """Get the docs directory path."""
        return self.get_env_dir() / "docs"
    
    def get_artifacts_dir(self) -> Path:
        """Get the artifacts directory path."""
        return self.get_env_dir() / "artifacts"
    
    def get_logs_dir(self) -> Path:
        """Get the logs directory path."""
        return self.get_env_dir() / "logs"