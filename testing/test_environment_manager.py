"""
Test Environment Manager

This module manages isolated testing environments to ensure tests don't interfere
with each other and provide clean, reproducible test conditions.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import yaml


@dataclass
class TestEnvironmentConfig:
    """Configuration for a test environment."""
    environment_name: str
    model: str = "moonshot/kimi-k2-0711-preview"
    max_cost: float = 5.0
    max_iterations: int = 20
    timeout_seconds: int = 300
    test_task: str = "Create a simple calculator application"
    working_directory: Optional[str] = None
    environment_variables: Optional[Dict[str, str]] = None
    required_files: Optional[List[str]] = None
    cleanup_on_completion: bool = True


class TestEnvironmentManager:
    """Manages isolated testing environments for comprehensive testing."""
    
    def __init__(self, base_test_dir: str = "testing/comprehensive_tests"):
        self.base_test_dir = Path(base_test_dir)
        self.base_test_dir.mkdir(parents=True, exist_ok=True)
        self.active_environments: Dict[str, Path] = {}
        self.environment_configs: Dict[str, TestEnvironmentConfig] = {}
        
        print("🏗️ Test Environment Manager initialized")
        print(f"📁 Base test directory: {self.base_test_dir}")
    
    def create_isolated_environment(self, test_name: str, config: Optional[TestEnvironmentConfig] = None) -> Path:
        """
        Create an isolated testing environment.
        
        Args:
            test_name: Unique name for the test environment
            config: Optional configuration for the environment
            
        Returns:
            Path to the created environment directory
        """
        if config is None:
            config = TestEnvironmentConfig(environment_name=test_name)
        
        # Create unique environment directory
        env_dir = self.base_test_dir / f"env_{test_name}"
        
        # Clean up existing environment if it exists
        if env_dir.exists():
            print(f"🧹 Cleaning up existing environment: {env_dir}")
            shutil.rmtree(env_dir)
        
        # Create new environment directory
        env_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (env_dir / "docs").mkdir(exist_ok=True)
        (env_dir / "src").mkdir(exist_ok=True)
        (env_dir / "tests").mkdir(exist_ok=True)
        (env_dir / "logs").mkdir(exist_ok=True)
        (env_dir / "config").mkdir(exist_ok=True)
        (env_dir / "results").mkdir(exist_ok=True)
        
        # Set up configuration
        self.setup_test_configuration(env_dir, config)
        
        # Copy required files if specified
        if config.required_files:
            self._copy_required_files(env_dir, config.required_files)
        
        # Set up environment variables
        if config.environment_variables:
            self._setup_environment_variables(env_dir, config.environment_variables)
        
        # Register environment
        self.active_environments[test_name] = env_dir
        self.environment_configs[test_name] = config
        
        print(f"✅ Created isolated environment: {env_dir}")
        return env_dir
    
    def setup_test_configuration(self, env_path: Path, config: TestEnvironmentConfig) -> None:
        """
        Set up configuration files for the test environment.
        
        Args:
            env_path: Path to the environment directory
            config: Configuration to apply
        """
        config_dir = env_path / "config"
        
        # Create EquitrCoder configuration
        equitrcoder_config = {
            "llm": {
                "model": config.model,
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "orchestrator": {
                "max_iterations": config.max_iterations,
                "max_cost": config.max_cost,
                "timeout_seconds": config.timeout_seconds,
                "use_multi_agent": False,  # Will be overridden per test
                "debug": True
            },
            "tools": {
                "enabled": [
                    "read_file",
                    "write_file", 
                    "list_files",
                    "grep_search",
                    "shell",
                    "git_status",
                    "git_diff",
                    "git_commit",
                    "create_todo",
                    "update_todo",
                    "list_todos"
                ],
                "disabled": []
            },
            "session": {
                "session_dir": str(env_path / "sessions"),
                "max_context": 8000
            }
        }
        
        # Save EquitrCoder config as YAML
        config_file = config_dir / "equitrcoder_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(equitrcoder_config, f, default_flow_style=False)
        
        # Create test-specific configuration
        test_config = {
            "test_name": config.environment_name,
            "model": config.model,
            "test_task": config.test_task,
            "max_cost": config.max_cost,
            "max_iterations": config.max_iterations,
            "timeout_seconds": config.timeout_seconds,
            "created_at": str(Path.cwd()),
            "environment_path": str(env_path)
        }
        
        test_config_file = config_dir / "test_config.json"
        with open(test_config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Create .env file for environment variables
        env_file = env_path / ".env"
        env_content = f"""# Test Environment Variables for {config.environment_name}
EQUITR_CONFIG_PATH={config_dir / 'equitrcoder_config.yaml'}
EQUITR_SESSION_DIR={env_path / 'sessions'}
EQUITR_LOG_DIR={env_path / 'logs'}
EQUITR_TEST_MODE=true
EQUITR_TEST_NAME={config.environment_name}
"""
        
        # Add custom environment variables
        if config.environment_variables:
            for key, value in config.environment_variables.items():
                env_content += f"{key}={value}\n"
        
        env_file.write_text(env_content)
        
        print(f"⚙️ Configuration set up for environment: {config.environment_name}")
    
    def _copy_required_files(self, env_path: Path, required_files: List[str]) -> None:
        """Copy required files to the test environment."""
        for file_path in required_files:
            source = Path(file_path)
            if source.exists():
                if source.is_file():
                    dest = env_path / source.name
                    shutil.copy2(source, dest)
                    print(f"📄 Copied file: {source} -> {dest}")
                elif source.is_dir():
                    dest = env_path / source.name
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                    print(f"📁 Copied directory: {source} -> {dest}")
            else:
                print(f"⚠️ Required file not found: {file_path}")
    
    def _setup_environment_variables(self, env_path: Path, env_vars: Dict[str, str]) -> None:
        """Set up environment variables for the test environment."""
        env_file = env_path / ".env"
        
        # Read existing content if file exists
        existing_content = ""
        if env_file.exists():
            existing_content = env_file.read_text()
        
        # Add new environment variables
        new_content = existing_content
        for key, value in env_vars.items():
            new_content += f"\n{key}={value}"
        
        env_file.write_text(new_content)
        print(f"🔧 Environment variables configured for: {env_path.name}")
    
    def get_environment_path(self, test_name: str) -> Optional[Path]:
        """Get the path to a test environment."""
        return self.active_environments.get(test_name)
    
    def get_environment_config(self, test_name: str) -> Optional[TestEnvironmentConfig]:
        """Get the configuration for a test environment."""
        return self.environment_configs.get(test_name)
    
    def list_active_environments(self) -> List[str]:
        """List all active test environments."""
        return list(self.active_environments.keys())
    
    def validate_environment_isolation(self, test_name: str) -> Dict[str, bool]:
        """
        Validate that a test environment is properly isolated.
        
        Returns:
            Dictionary with validation results
        """
        env_path = self.get_environment_path(test_name)
        if not env_path:
            return {"error": "Environment not found"}
        
        validation_results = {
            "directory_exists": env_path.exists(),
            "config_exists": (env_path / "config" / "test_config.json").exists(),
            "env_file_exists": (env_path / ".env").exists(),
            "subdirectories_created": all([
                (env_path / subdir).exists() 
                for subdir in ["docs", "src", "tests", "logs", "config", "results"]
            ]),
            "isolated_from_parent": self._check_isolation(env_path),
            "writable": os.access(env_path, os.W_OK),
            "readable": os.access(env_path, os.R_OK)
        }
        
        return validation_results
    
    def _check_isolation(self, env_path: Path) -> bool:
        """Check if environment is properly isolated from parent directories."""
        try:
            # Check that we can't access parent project files directly
            parent_files = [".git", "requirements.txt", "setup.py"]
            for file_name in parent_files:
                if (env_path / file_name).exists():
                    return False  # Environment is not isolated
            
            # Check that environment has its own configuration
            config_file = env_path / "config" / "test_config.json"
            if not config_file.exists():
                return False
            
            return True
        except Exception:
            return False
    
    def cleanup_environment(self, test_name: str) -> bool:
        """
        Clean up a test environment.
        
        Args:
            test_name: Name of the test environment to clean up
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        env_path = self.get_environment_path(test_name)
        config = self.get_environment_config(test_name)
        
        if not env_path or not config:
            print(f"⚠️ Environment {test_name} not found for cleanup")
            return False
        
        # Check if cleanup is enabled
        if not config.cleanup_on_completion:
            print(f"🔒 Cleanup disabled for environment: {test_name}")
            return True
        
        try:
            # Remove environment directory
            if env_path.exists():
                shutil.rmtree(env_path)
                print(f"🧹 Cleaned up environment: {test_name}")
            
            # Remove from active environments
            if test_name in self.active_environments:
                del self.active_environments[test_name]
            
            if test_name in self.environment_configs:
                del self.environment_configs[test_name]
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to cleanup environment {test_name}: {str(e)}")
            return False
    
    def cleanup_all_environments(self) -> Dict[str, bool]:
        """
        Clean up all active test environments.
        
        Returns:
            Dictionary mapping environment names to cleanup success status
        """
        cleanup_results = {}
        
        # Get list of environments to avoid modifying dict during iteration
        env_names = list(self.active_environments.keys())
        
        for env_name in env_names:
            cleanup_results[env_name] = self.cleanup_environment(env_name)
        
        return cleanup_results
    
    def create_environment_snapshot(self, test_name: str, snapshot_name: str) -> Optional[Path]:
        """
        Create a snapshot of a test environment for debugging or analysis.
        
        Args:
            test_name: Name of the test environment
            snapshot_name: Name for the snapshot
            
        Returns:
            Path to the snapshot directory if successful, None otherwise
        """
        env_path = self.get_environment_path(test_name)
        if not env_path or not env_path.exists():
            print(f"⚠️ Environment {test_name} not found for snapshot")
            return None
        
        try:
            snapshot_dir = self.base_test_dir / "snapshots"
            snapshot_dir.mkdir(exist_ok=True)
            
            snapshot_path = snapshot_dir / f"{test_name}_{snapshot_name}"
            
            # Remove existing snapshot if it exists
            if snapshot_path.exists():
                shutil.rmtree(snapshot_path)
            
            # Create snapshot
            shutil.copytree(env_path, snapshot_path)
            
            # Add snapshot metadata
            metadata = {
                "original_environment": test_name,
                "snapshot_name": snapshot_name,
                "created_at": str(Path.cwd()),
                "source_path": str(env_path)
            }
            
            metadata_file = snapshot_path / "snapshot_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📸 Created snapshot: {snapshot_path}")
            return snapshot_path
            
        except Exception as e:
            print(f"❌ Failed to create snapshot for {test_name}: {str(e)}")
            return None
    
    def get_environment_status(self) -> Dict[str, Any]:
        """Get status of all managed environments."""
        status = {
            "total_environments": len(self.active_environments),
            "base_directory": str(self.base_test_dir),
            "environments": {}
        }
        
        for env_name, env_path in self.active_environments.items():
            config = self.environment_configs.get(env_name)
            validation = self.validate_environment_isolation(env_name)
            
            status["environments"][env_name] = {
                "path": str(env_path),
                "exists": env_path.exists(),
                "config": config.__dict__ if config else None,
                "validation": validation,
                "size_mb": self._get_directory_size(env_path) if env_path.exists() else 0
            }
        
        return status
    
    def _get_directory_size(self, path: Path) -> float:
        """Get the size of a directory in MB."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0