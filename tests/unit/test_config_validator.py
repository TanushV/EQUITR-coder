"""
Unit tests for ConfigurationValidator

Tests the configuration validation system including:
- Startup configuration validation
- Environment variable validation
- Model configuration validation
- Limits validation
- Hot-reloading capability
"""

import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from equitrcoder.core.config_validator import (
    ConfigurationValidator,
    get_config_validator,
    validate_startup_config
)
from equitrcoder.core.unified_config import UnifiedConfigManager


class TestConfigurationValidator:
    """Test suite for ConfigurationValidator"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Reset singleton instances
        UnifiedConfigManager._instance = None
        
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = self.temp_dir
        
        # Create test configuration files
        self.create_test_configs()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Reset singletons
        UnifiedConfigManager._instance = None
    
    def create_test_configs(self):
        """Create test configuration files"""
        # Default config
        default_config = {
            'llm': {
                'provider': 'litellm',
                'model': 'gpt-4',
                'temperature': 0.1,
                'max_tokens': 4000,
                'budget': 1.0
            },
            'sandbox': {
                'type': 'venv',
                'timeout': 30,
                'max_memory': 512,
                'allow_network': False
            },
            'orchestrator': {
                'max_iterations': 20,
                'error_retry_limit': 3,
                'error_retry_delay': 1.0,
                'supervisor_model': 'o3',
                'worker_model': 'moonshot/kimi-k2-0711-preview'
            },
            'limits': {
                'max_cost': 5.0,
                'max_workers': 3,
                'max_depth': 3,
                'devops_timeout': 600
            }
        }
        
        with open(os.path.join(self.temp_dir, 'default.yaml'), 'w') as f:
            yaml.dump(default_config, f)
        
        # Profiles config
        profiles_config = {
            'default_tools': ['create_file', 'read_file', 'edit_file'],
            'settings': {
                'profiles_directory': 'equitrcoder/profiles',
                'allow_empty_additional_tools': True
            }
        }
        
        with open(os.path.join(self.temp_dir, 'profiles.yaml'), 'w') as f:
            yaml.dump(profiles_config, f)
        
        # System prompts config
        prompts_config = {
            'single_agent_prompt': 'You are a single agent...',
            'multi_agent_prompt': 'You are a multi agent...',
            'metadata': {
                'version': '1.0',
                'description': 'Test prompts'
            }
        }
        
        with open(os.path.join(self.temp_dir, 'system_prompt.yaml'), 'w') as f:
            yaml.dump(prompts_config, f)
    
    def test_validator_initialization(self):
        """Test that ConfigurationValidator initializes correctly"""
        # Mock the config manager to use our test config
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = MagicMock()
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            
            assert validator.config_manager == mock_config_manager
    
    def test_startup_configuration_validation_success(self):
        """Test successful startup configuration validation"""
        # Create validator with test config
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            result = validator.validate_startup_configuration()
            
            assert result.is_valid
            assert len(result.errors) == 0
    
    def test_startup_configuration_validation_failure(self):
        """Test startup configuration validation with errors"""
        # Create invalid config that won't trigger fallback
        invalid_config = {
            'llm': {
                'provider': 'litellm',  # Valid provider
                'model': 'gpt-4',
                'temperature': 3.0,  # Above maximum - this should cause validation error
                'max_tokens': 4000,
                'budget': 1.0
            },
            'sandbox': {
                'type': 'venv',
                'timeout': 30,
                'max_memory': 512,
                'allow_network': False
            },
            'orchestrator': {
                'max_iterations': 20,
                'error_retry_limit': 3,
                'error_retry_delay': 1.0,
                'supervisor_model': 'o3',
                'worker_model': 'moonshot/kimi-k2-0711-preview'
            }
        }
        
        with open(os.path.join(self.temp_dir, 'default.yaml'), 'w') as f:
            yaml.dump(invalid_config, f)
        
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            result = validator.validate_startup_configuration()
            
            # The configuration should be invalid due to temperature being above maximum
            assert not result.is_valid
            assert len(result.errors) > 0
            assert any('temperature' in error for error in result.errors)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_environment_variables_validation_missing(self):
        """Test environment variable validation when API keys are missing"""
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            missing_vars = validator.validate_environment_variables()
            
            assert len(missing_vars) > 0
            assert any('API key' in var for var in missing_vars)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_environment_variables_validation_success(self):
        """Test environment variable validation when API keys are present"""
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            missing_vars = validator.validate_environment_variables()
            
            assert len(missing_vars) == 0
    
    def test_model_configuration_validation_success(self):
        """Test model configuration validation with valid models"""
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            issues = validator.validate_model_configuration()
            
            assert len(issues) == 0
    
    def test_model_configuration_validation_missing_model(self):
        """Test model configuration validation with missing model"""
        # Create config without model
        config_without_model = {
            'llm': {
                'provider': 'litellm',
                'temperature': 0.1
            },
            'orchestrator': {
                'supervisor_model': 'o3',
                'worker_model': 'gpt-4'
            }
        }
        
        with open(os.path.join(self.temp_dir, 'default.yaml'), 'w') as f:
            yaml.dump(config_without_model, f)
        
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            issues = validator.validate_model_configuration()
            
            assert len(issues) > 0
            assert any('model is not configured' in issue for issue in issues)
    
    def test_limits_configuration_validation_success(self):
        """Test limits configuration validation with valid limits"""
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            issues = validator.validate_limits_configuration()
            
            assert len(issues) == 0
    
    def test_limits_configuration_validation_invalid_limits(self):
        """Test limits configuration validation with invalid limits"""
        # Create config with invalid limits
        config_with_invalid_limits = {
            'limits': {
                'max_cost': 0,  # Invalid: should be > 0
                'max_iterations': -1,  # Invalid: should be > 0
                'max_workers': 0,  # Invalid: should be > 0
                'devops_timeout': 0  # Invalid: should be > 0
            }
        }
        
        with open(os.path.join(self.temp_dir, 'default.yaml'), 'w') as f:
            yaml.dump(config_with_invalid_limits, f)
        
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            issues = validator.validate_limits_configuration()
            
            assert len(issues) > 0
            assert any('should be greater than 0' in issue for issue in issues)
    
    def test_comprehensive_validation_success(self):
        """Test comprehensive validation with valid configuration"""
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                validator = ConfigurationValidator()
                results = validator.perform_comprehensive_validation()
                
                assert results['overall_valid']
                assert results['schema_validation'].is_valid
                assert len(results['environment_issues']) == 0
                assert len(results['model_issues']) == 0
    
    def test_comprehensive_validation_failure(self):
        """Test comprehensive validation with invalid configuration"""
        # Create completely invalid config
        invalid_config = {}
        
        with open(os.path.join(self.temp_dir, 'default.yaml'), 'w') as f:
            yaml.dump(invalid_config, f)
        
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = UnifiedConfigManager(self.config_path)
            mock_get_config.return_value = mock_config_manager
            
            with patch.dict(os.environ, {}, clear=True):
                validator = ConfigurationValidator()
                results = validator.perform_comprehensive_validation()
                
                assert not results['overall_valid']
                assert len(results['environment_issues']) > 0
                assert len(results['model_issues']) > 0
    
    def test_hot_reloading_capability(self):
        """Test configuration hot-reloading capability"""
        with patch('equitrcoder.core.config_validator.get_config_manager') as mock_get_config:
            mock_config_manager = MagicMock()
            mock_get_config.return_value = mock_config_manager
            
            validator = ConfigurationValidator()
            
            # Test enable hot-reloading
            validator.enable_hot_reloading()
            # Should not raise any exceptions
            
            # Test reload configuration
            mock_config_manager.reload_config.return_value = None
            mock_config_manager.load_config.return_value = MagicMock()
            mock_config_manager.validate_schema.return_value = MagicMock(is_valid=True, errors=[])
            
            result = validator.reload_configuration()
            
            mock_config_manager.reload_config.assert_called_once()
            assert result.is_valid
    
    def test_global_functions(self):
        """Test global convenience functions"""
        with patch('equitrcoder.core.config_validator.ConfigurationValidator') as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator_class.return_value = mock_validator
            
            # Test get_config_validator
            validator = get_config_validator()
            assert validator == mock_validator
            
            # Test validate_startup_config
            mock_validator.perform_comprehensive_validation.return_value = {
                'overall_valid': True,
                'environment_issues': [],
                'model_issues': [],
                'limits_issues': [],
                'recommendations': []
            }
            
            result = validate_startup_config()
            assert result is True
            
            # Test validate_startup_config with failure
            mock_validator.perform_comprehensive_validation.return_value = {
                'overall_valid': False,
                'environment_issues': ['Missing API key'],
                'model_issues': ['Model not configured'],
                'limits_issues': [],
                'recommendations': ['Set up API keys']
            }
            
            result = validate_startup_config()
            assert result is False


if __name__ == '__main__':
    pytest.main([__file__])