"""
Isolated test environment management for comprehensive mode testing.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import subprocess

from .config import TestEnvironmentConfig, ComprehensiveTestConfig
from .results import ErrorCategory, FailureAnalysis


class TestEnvironment:
    """Represents an isolated test environment."""
    
    def __init__(self, config: TestEnvironmentConfig):
        """Initialize test environment."""
        self.config = config
        self.env_dir = config.get_env_dir()
        self.docs_dir = config.get_docs_dir()
        self.artifacts_dir = config.get_artifacts_dir()
        self.logs_dir = config.get_logs_dir()
        
        # Environment state
        self.is_initialized = False
        self.is_active = False
        self.artifacts: List[str] = []
        self.logs: List[str] = []
        
    def initialize(self) -> bool:
        """Initialize the test environment."""
        try:
            # Create directory structure
            self.env_dir.mkdir(parents=True, exist_ok=True)
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create environment metadata
            metadata = {
                'env_id': self.config.env_id,
                'mode': self.config.mode,
                'model': self.config.model,
                'max_cost': self.config.max_cost,
                'max_iterations': self.config.max_iterations,
                'timeout_seconds': self.config.timeout_seconds,
                'created_at': str(self.env_dir.stat().st_ctime),
                'initialized': True
            }
            
            metadata_path = self.env_dir / "environment.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create basic project structure
            self._create_project_structure()
            
            self.is_initialized = True
            self.is_active = True
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize environment {self.config.env_id}: {str(e)}")
            return False
    
    def _create_project_structure(self):
        """Create basic project structure for testing."""
        # Create basic Python project structure
        (self.env_dir / "src").mkdir(exist_ok=True)
        (self.env_dir / "tests").mkdir(exist_ok=True)
        (self.env_dir / "docs").mkdir(exist_ok=True)
        
        # Create basic files
        (self.env_dir / "README.md").write_text("# Test Project\n\nThis is a test project for EquitrCoder testing.\n")
        (self.env_dir / "requirements.txt").write_text("# Test project requirements\n")
        
        # Create .gitignore
        gitignore_content = """
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
"""
        (self.env_dir / ".gitignore").write_text(gitignore_content.strip())
    
    def cleanup(self, preserve_artifacts: bool = True) -> bool:
        """Clean up the test environment."""
        try:
            if preserve_artifacts and self.artifacts:
                # Move artifacts to a preserved location
                preserved_dir = self.config.base_dir / "preserved_artifacts" / self.config.env_id
                preserved_dir.mkdir(parents=True, exist_ok=True)
                
                for artifact in self.artifacts:
                    artifact_path = Path(artifact)
                    if artifact_path.exists():
                        dest_path = preserved_dir / artifact_path.name
                        shutil.copy2(artifact_path, dest_path)
            
            # Remove environment directory
            if self.env_dir.exists():
                shutil.rmtree(self.env_dir)
            
            self.is_active = False
            return True
            
        except Exception as e:
            print(f"❌ Failed to cleanup environment {self.config.env_id}: {str(e)}")
            return False
    
    def add_artifact(self, file_path: str):
        """Add a file as an artifact to be preserved."""
        if file_path not in self.artifacts:
            self.artifacts.append(file_path)
    
    def add_log(self, log_path: str):
        """Add a log file."""
        if log_path not in self.logs:
            self.logs.append(log_path)
    
    def get_working_directory(self) -> str:
        """Get the working directory for this environment."""
        return str(self.env_dir)
    
    def validate(self) -> List[str]:
        """Validate the environment setup."""
        issues = []
        
        if not self.env_dir.exists():
            issues.append(f"Environment directory does not exist: {self.env_dir}")
        
        if not self.docs_dir.exists():
            issues.append(f"Docs directory does not exist: {self.docs_dir}")
        
        if not self.artifacts_dir.exists():
            issues.append(f"Artifacts directory does not exist: {self.artifacts_dir}")
        
        if not self.logs_dir.exists():
            issues.append(f"Logs directory does not exist: {self.logs_dir}")
        
        # Check write permissions
        if not os.access(self.env_dir, os.W_OK):
            issues.append(f"No write permission for environment directory: {self.env_dir}")
        
        return issues


class IsolatedTestEnvironmentManager:
    """Manages isolated test environments for each mode."""
    
    def __init__(self, base_test_dir: str):
        """Initialize the environment manager."""
        self.base_test_dir = Path(base_test_dir)
        self.base_test_dir.mkdir(parents=True, exist_ok=True)
        
        # Track active environments
        self.active_environments: Dict[str, TestEnvironment] = {}
        self.environment_counter = 0
        
    def create_environment(
        self, 
        mode: str, 
        model: str = "moonshot/kimi-k2-0711-preview",
        max_cost: float = 5.0,
        max_iterations: int = 20,
        timeout_seconds: int = 300
    ) -> TestEnvironment:
        """Create isolated test environment."""
        self.environment_counter += 1
        env_id = f"env_{self.environment_counter:03d}"
        
        # Create mode-specific directory
        mode_dir = self.base_test_dir / f"{mode}_envs"
        mode_dir.mkdir(exist_ok=True)
        
        # Create environment configuration
        env_config = TestEnvironmentConfig(
            env_id=env_id,
            mode=mode,
            base_dir=mode_dir,
            model=model,
            max_cost=max_cost,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds
        )
        
        # Create environment
        environment = TestEnvironment(env_config)
        
        # Initialize environment
        if environment.initialize():
            self.active_environments[env_id] = environment
            print(f"✅ Created test environment: {env_id} (mode: {mode})")
            return environment
        else:
            raise RuntimeError(f"Failed to initialize test environment: {env_id}")
    
    def get_environment(self, env_id: str) -> Optional[TestEnvironment]:
        """Get an environment by ID."""
        return self.active_environments.get(env_id)
    
    def cleanup_environment(self, env_id: str, preserve_artifacts: bool = True) -> bool:
        """Clean up test environment."""
        environment = self.active_environments.get(env_id)
        if not environment:
            print(f"⚠️ Environment not found: {env_id}")
            return False
        
        success = environment.cleanup(preserve_artifacts)
        if success:
            del self.active_environments[env_id]
            print(f"🧹 Cleaned up environment: {env_id}")
        
        return success
    
    def cleanup_all_environments(self, preserve_artifacts: bool = True) -> int:
        """Clean up all active environments."""
        cleaned_count = 0
        env_ids = list(self.active_environments.keys())
        
        for env_id in env_ids:
            if self.cleanup_environment(env_id, preserve_artifacts):
                cleaned_count += 1
        
        return cleaned_count
    
    def preserve_artifacts(self, env_id: str, artifacts_dir: str) -> bool:
        """Preserve test artifacts for analysis."""
        environment = self.active_environments.get(env_id)
        if not environment:
            return False
        
        try:
            artifacts_path = Path(artifacts_dir)
            artifacts_path.mkdir(parents=True, exist_ok=True)
            
            # Copy all artifacts
            for artifact in environment.artifacts:
                artifact_path = Path(artifact)
                if artifact_path.exists():
                    dest_path = artifacts_path / artifact_path.name
                    shutil.copy2(artifact_path, dest_path)
            
            # Copy logs
            logs_dir = artifacts_path / "logs"
            logs_dir.mkdir(exist_ok=True)
            for log in environment.logs:
                log_path = Path(log)
                if log_path.exists():
                    dest_path = logs_dir / log_path.name
                    shutil.copy2(log_path, dest_path)
            
            # Copy environment metadata
            env_metadata_path = environment.env_dir / "environment.json"
            if env_metadata_path.exists():
                dest_path = artifacts_path / "environment.json"
                shutil.copy2(env_metadata_path, dest_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to preserve artifacts for {env_id}: {str(e)}")
            return False
    
    def validate_environment(self, env_id: str) -> List[str]:
        """Validate environment setup and return any issues."""
        environment = self.active_environments.get(env_id)
        if not environment:
            return [f"Environment not found: {env_id}"]
        
        return environment.validate()
    
    def get_active_environments(self) -> Dict[str, TestEnvironment]:
        """Get all active environments."""
        return self.active_environments.copy()
    
    def get_environment_stats(self) -> Dict[str, Any]:
        """Get statistics about managed environments."""
        return {
            'total_environments': len(self.active_environments),
            'environments_by_mode': self._get_environments_by_mode(),
            'base_directory': str(self.base_test_dir),
            'disk_usage_mb': self._calculate_disk_usage()
        }
    
    def _get_environments_by_mode(self) -> Dict[str, int]:
        """Get count of environments by mode."""
        mode_counts = {}
        for env in self.active_environments.values():
            mode = env.config.mode
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        return mode_counts
    
    def _calculate_disk_usage(self) -> float:
        """Calculate total disk usage in MB."""
        try:
            total_size = 0
            for env in self.active_environments.values():
                if env.env_dir.exists():
                    total_size += sum(
                        f.stat().st_size for f in env.env_dir.rglob('*') if f.is_file()
                    )
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0
    
    def create_environment_for_config(self, config: ComprehensiveTestConfig, mode: str) -> TestEnvironment:
        """Create environment using comprehensive test config."""
        return self.create_environment(
            mode=mode,
            model=config.model,
            max_cost=config.max_cost_per_test,
            max_iterations=config.max_iterations_per_test,
            timeout_seconds=config.timeout_seconds
        )
    
    def analyze_environment_failure(self, env_id: str, error: Exception) -> FailureAnalysis:
        """Analyze environment-related failures."""
        environment = self.active_environments.get(env_id)
        
        context = {
            'env_id': env_id,
            'environment_exists': environment is not None,
            'base_dir': str(self.base_test_dir),
            'error_type': type(error).__name__
        }
        
        if environment:
            context.update({
                'env_dir': str(environment.env_dir),
                'is_initialized': environment.is_initialized,
                'is_active': environment.is_active,
                'mode': environment.config.mode
            })
        
        # Categorize error
        error_message = str(error)
        if "permission" in error_message.lower():
            error_category = ErrorCategory.ENVIRONMENT_ERROR
            root_cause = "Insufficient file system permissions"
            suggested_fixes = [
                "Check file system permissions for test directory",
                "Run tests with appropriate user permissions",
                "Verify disk space availability"
            ]
        elif "disk" in error_message.lower() or "space" in error_message.lower():
            error_category = ErrorCategory.ENVIRONMENT_ERROR
            root_cause = "Insufficient disk space"
            suggested_fixes = [
                "Free up disk space",
                "Use a different test directory location",
                "Clean up old test environments"
            ]
        elif "directory" in error_message.lower() or "path" in error_message.lower():
            error_category = ErrorCategory.CONFIGURATION_ERROR
            root_cause = "Invalid directory or path configuration"
            suggested_fixes = [
                "Verify test directory path is valid",
                "Check parent directory exists and is writable",
                "Use absolute paths instead of relative paths"
            ]
        else:
            error_category = ErrorCategory.ENVIRONMENT_ERROR
            root_cause = f"Environment setup failure: {error_message}"
            suggested_fixes = [
                "Check system resources and permissions",
                "Verify test environment configuration",
                "Review error logs for more details"
            ]
        
        return FailureAnalysis(
            error_category=error_category,
            root_cause=root_cause,
            error_message=error_message,
            stack_trace=str(error),
            suggested_fixes=suggested_fixes,
            context=context,
            auto_fixable=error_category == ErrorCategory.CONFIGURATION_ERROR
        )