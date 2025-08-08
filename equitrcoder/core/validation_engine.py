"""
Validation Engine for EQUITR Coder

This module provides comprehensive validation throughout the system,
including schema validation, input parameter validation, API response validation,
and file permission validation.

Features:
- Schema validation for all configuration files
- Input parameter validation at all entry points
- API response validation and error handling
- File permission and existence validation
- Model compatibility and availability validation
- Comprehensive error guidance system
"""

import logging
import os
# import json  # Unused
# import yaml  # Unused
# from pathlib import Path  # Unused
from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
# import jsonschema  # Unused
from jsonschema import validate, ValidationError as JsonSchemaValidationError
import threading
# from abc import ABC, abstractmethod  # Unused

from .interfaces import IValidator, Result
from .standardized_error_handler import ErrorCategory, ErrorSeverity, create_contextual_exception

logger = logging.getLogger(__name__)


class ValidationType(Enum):
    """Types of validation"""
    SCHEMA = "schema"
    INPUT = "input"
    OUTPUT = "output"
    FILE = "file"
    MODEL = "model"
    API = "api"
    PERMISSION = "permission"


@dataclass
class ValidationRule:
    """Represents a validation rule"""
    name: str
    description: str
    validator_function: Callable[[Any], bool]
    error_message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.VALIDATION


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    validation_type: Optional[ValidationType] = None


class BaseValidator(IValidator[Any]):
    """Base validator class implementing common validation patterns"""
    
    def __init__(self, name: str):
        self.name = name
        self.rules: List[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule"""
        self.rules.append(rule)
    
    def validate(self, item: Any) -> Result[bool]:
        """Validate an item and return result with details"""
        errors = []
        warnings = []
        
        for rule in self.rules:
            try:
                if not rule.validator_function(item):
                    if rule.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                        errors.append(f"{rule.name}: {rule.error_message}")
                    else:
                        warnings.append(f"{rule.name}: {rule.error_message}")
            except Exception as e:
                errors.append(f"{rule.name}: Validation failed - {str(e)}")
        
        is_valid = len(errors) == 0
        
        return Result(
            success=is_valid,
            data=is_valid,
            error="; ".join(errors) if errors else None,
            metadata={
                'warnings': warnings,
                'errors': errors,
                'validator': self.name
            }
        )
    
    def get_validation_rules(self) -> List[str]:
        """Get list of validation rules"""
        return [f"{rule.name}: {rule.description}" for rule in self.rules]


class SchemaValidator(BaseValidator):
    """Validator for JSON/YAML schema validation"""
    
    def __init__(self, schema: Dict[str, Any], name: str = "schema_validator"):
        super().__init__(name)
        self.schema = schema
    
    def validate(self, item: Any) -> Result[bool]:
        """Validate item against JSON schema"""
        try:
            validate(instance=item, schema=self.schema)
            return Result(success=True, data=True)
        except JsonSchemaValidationError as e:
            return Result(
                success=False,
                data=False,
                error=f"Schema validation failed: {e.message}",
                metadata={
                    'path': list(e.absolute_path),
                    'schema_path': list(e.schema_path),
                    'validator': self.name
                }
            )
        except Exception as e:
            return Result(
                success=False,
                data=False,
                error=f"Schema validation error: {str(e)}",
                metadata={'validator': self.name}
            )


class FileValidator(BaseValidator):
    """Validator for file system operations"""
    
    def __init__(self, name: str = "file_validator"):
        super().__init__(name)
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default file validation rules"""
        self.add_rule(ValidationRule(
            name="file_exists",
            description="File must exist",
            validator_function=lambda path: os.path.exists(str(path)),
            error_message="File does not exist"
        ))
        
        self.add_rule(ValidationRule(
            name="file_readable",
            description="File must be readable",
            validator_function=lambda path: os.path.exists(str(path)) and os.access(str(path), os.R_OK),
            error_message="File is not readable"
        ))
    
    def validate_file_permissions(self, file_path: str, required_permissions: str = "r") -> ValidationResult:
        """
        Validate file permissions
        
        Args:
            file_path: Path to file
            required_permissions: Required permissions (r, w, x combinations)
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        if not os.path.exists(file_path):
            errors.append(f"File does not exist: {file_path}")
        else:
            # Check read permission
            if 'r' in required_permissions and not os.access(file_path, os.R_OK):
                errors.append(f"File is not readable: {file_path}")
            
            # Check write permission
            if 'w' in required_permissions and not os.access(file_path, os.W_OK):
                errors.append(f"File is not writable: {file_path}")
            
            # Check execute permission
            if 'x' in required_permissions and not os.access(file_path, os.X_OK):
                errors.append(f"File is not executable: {file_path}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validation_type=ValidationType.PERMISSION,
            details={'file_path': file_path, 'required_permissions': required_permissions}
        )


class ModelValidator(BaseValidator):
    """Validator for model configurations and availability"""
    
    def __init__(self, name: str = "model_validator"):
        super().__init__(name)
        self.supported_providers = ['openai', 'anthropic', 'litellm', 'ollama']
        self.supported_models = {
            'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
            'litellm': ['*'],  # LiteLLM supports many models
            'ollama': ['llama2', 'codellama', 'mistral']
        }
    
    def validate_model_config(self, model_config: Dict[str, Any]) -> ValidationResult:
        """
        Validate model configuration
        
        Args:
            model_config: Model configuration dictionary
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['provider', 'model']
        for field_name in required_fields:
            if field_name not in model_config:
                errors.append(f"Missing required field: {field_name}")
        
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                validation_type=ValidationType.MODEL
            )
        
        # Validate provider
        provider = model_config.get('provider', '').lower()
        if provider not in self.supported_providers:
            errors.append(f"Unsupported provider: {provider}. Supported: {', '.join(self.supported_providers)}")
        
        # Validate model for provider
        model = model_config.get('model', '')
        if provider in self.supported_models:
            supported_models = self.supported_models[provider]
            if '*' not in supported_models and model not in supported_models:
                warnings.append(f"Model '{model}' may not be supported by provider '{provider}'")
        
        # Validate optional fields
        if 'temperature' in model_config:
            temp = model_config['temperature']
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append("Temperature must be a number between 0 and 2")
        
        if 'max_tokens' in model_config:
            max_tokens = model_config['max_tokens']
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                errors.append("max_tokens must be a positive integer")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validation_type=ValidationType.MODEL,
            details={'provider': provider, 'model': model}
        )


class APIValidator(BaseValidator):
    """Validator for API requests and responses"""
    
    def __init__(self, name: str = "api_validator"):
        super().__init__(name)
    
    def validate_api_response(self, response: Dict[str, Any], expected_schema: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate API response
        
        Args:
            response: API response dictionary
            expected_schema: Expected response schema
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Basic response validation
        if not isinstance(response, dict):
            errors.append("Response must be a dictionary")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                validation_type=ValidationType.API
            )
        
        # Check for error indicators
        if 'error' in response:
            errors.append(f"API returned error: {response['error']}")
        
        # Schema validation if provided
        if expected_schema:
            try:
                validate(instance=response, schema=expected_schema)
            except JsonSchemaValidationError as e:
                errors.append(f"Response schema validation failed: {e.message}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validation_type=ValidationType.API,
            details={'response_keys': list(response.keys())}
        )


class ValidationEngine:
    """
    Comprehensive validation engine for all system boundaries
    """
    
    def __init__(self):
        self.validators: Dict[ValidationType, List[BaseValidator]] = {
            ValidationType.SCHEMA: [],
            ValidationType.INPUT: [],
            ValidationType.OUTPUT: [],
            ValidationType.FILE: [],
            ValidationType.MODEL: [],
            ValidationType.API: [],
            ValidationType.PERMISSION: []
        }
        
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Initialize default validators
        self._initialize_default_validators()
        
        logger.info("ValidationEngine initialized")
    
    def _initialize_default_validators(self):
        """Initialize default validators"""
        # File validator
        file_validator = FileValidator()
        self.register_validator(ValidationType.FILE, file_validator)
        
        # Model validator
        model_validator = ModelValidator()
        self.register_validator(ValidationType.MODEL, model_validator)
        
        # API validator
        api_validator = APIValidator()
        self.register_validator(ValidationType.API, api_validator)
    
    def register_validator(self, validation_type: ValidationType, validator: BaseValidator) -> None:
        """
        Register a validator for a specific validation type
        
        Args:
            validation_type: Type of validation
            validator: Validator instance
        """
        with self._lock:
            self.validators[validation_type].append(validator)
            logger.debug(f"Registered validator {validator.name} for type {validation_type.value}")
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """
        Register a JSON schema for validation
        
        Args:
            name: Schema name
            schema: JSON schema dictionary
        """
        with self._lock:
            self.schemas[name] = schema
            
            # Create and register schema validator
            schema_validator = SchemaValidator(schema, f"schema_{name}")
            self.register_validator(ValidationType.SCHEMA, schema_validator)
            
            logger.debug(f"Registered schema: {name}")
    
    def validate_configuration(self, config: Dict[str, Any], schema_name: Optional[str] = None) -> ValidationResult:
        """
        Validate configuration against schema
        
        Args:
            config: Configuration dictionary
            schema_name: Name of registered schema to validate against
            
        Returns:
            ValidationResult
        """
        if schema_name and schema_name in self.schemas:
            schema = self.schemas[schema_name]
            validator = SchemaValidator(schema, f"config_{schema_name}")
            result = validator.validate(config)
            
            return ValidationResult(
                is_valid=result.success,
                errors=[result.error] if result.error else [],
                validation_type=ValidationType.SCHEMA,
                details=result.metadata or {}
            )
        else:
            # Generic configuration validation
            errors = []
            warnings = []
            
            # Check for common configuration issues
            if not isinstance(config, dict):
                errors.append("Configuration must be a dictionary")
            
            # Check for empty configuration
            if isinstance(config, dict) and len(config) == 0:
                warnings.append("Configuration is empty")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                validation_type=ValidationType.SCHEMA
            )
    
    def validate_input_parameters(self, parameters: Dict[str, Any], required_params: List[str] = None, 
                                 param_types: Dict[str, Type] = None) -> ValidationResult:
        """
        Validate input parameters at entry points
        
        Args:
            parameters: Input parameters dictionary
            required_params: List of required parameter names
            param_types: Expected types for parameters
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        required_params = required_params or []
        param_types = param_types or {}
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
            elif parameters[param] is None:
                errors.append(f"Required parameter cannot be None: {param}")
        
        # Check parameter types
        for param, expected_type in param_types.items():
            if param in parameters and parameters[param] is not None:
                if not isinstance(parameters[param], expected_type):
                    errors.append(f"Parameter '{param}' must be of type {expected_type.__name__}, got {type(parameters[param]).__name__}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validation_type=ValidationType.INPUT,
            details={'parameter_count': len(parameters)}
        )
    
    def validate_file_access(self, file_path: str, required_permissions: str = "r") -> ValidationResult:
        """
        Validate file permissions and existence
        
        Args:
            file_path: Path to file
            required_permissions: Required permissions (r, w, x combinations)
            
        Returns:
            ValidationResult
        """
        with self._lock:
            file_validators = self.validators[ValidationType.FILE]
            
            if file_validators:
                # Use the first file validator
                validator = file_validators[0]
                if isinstance(validator, FileValidator):
                    return validator.validate_file_permissions(file_path, required_permissions)
        
        # Fallback validation
        errors = []
        if not os.path.exists(file_path):
            errors.append(f"File does not exist: {file_path}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            validation_type=ValidationType.FILE
        )
    
    def validate_model_configuration(self, model_config: Dict[str, Any]) -> ValidationResult:
        """
        Validate model configuration
        
        Args:
            model_config: Model configuration dictionary
            
        Returns:
            ValidationResult
        """
        with self._lock:
            model_validators = self.validators[ValidationType.MODEL]
            
            if model_validators:
                # Use the first model validator
                validator = model_validators[0]
                if isinstance(validator, ModelValidator):
                    return validator.validate_model_config(model_config)
        
        # Fallback validation
        errors = []
        if 'model' not in model_config:
            errors.append("Model configuration must include 'model' field")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            validation_type=ValidationType.MODEL
        )
    
    def validate_api_response(self, response: Dict[str, Any], schema_name: Optional[str] = None) -> ValidationResult:
        """
        Validate API response
        
        Args:
            response: API response dictionary
            schema_name: Name of registered schema for response validation
            
        Returns:
            ValidationResult
        """
        expected_schema = None
        if schema_name and schema_name in self.schemas:
            expected_schema = self.schemas[schema_name]
        
        with self._lock:
            api_validators = self.validators[ValidationType.API]
            
            if api_validators:
                # Use the first API validator
                validator = api_validators[0]
                if isinstance(validator, APIValidator):
                    return validator.validate_api_response(response, expected_schema)
        
        # Fallback validation
        errors = []
        if not isinstance(response, dict):
            errors.append("API response must be a dictionary")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            validation_type=ValidationType.API
        )
    
    def get_validation_guidance(self, validation_result: ValidationResult) -> List[str]:
        """
        Get specific correction instructions for validation failures
        
        Args:
            validation_result: Result of validation
            
        Returns:
            List of guidance instructions
        """
        guidance = []
        
        if not validation_result.is_valid:
            for error in validation_result.errors:
                if "missing required" in error.lower():
                    guidance.append(f"Add the missing required field: {error}")
                elif "file does not exist" in error.lower():
                    guidance.append("Check the file path and ensure the file exists")
                elif "not readable" in error.lower():
                    guidance.append("Check file permissions and ensure read access")
                elif "schema validation failed" in error.lower():
                    guidance.append("Review the data structure and ensure it matches the expected schema")
                elif "unsupported provider" in error.lower():
                    guidance.append("Use a supported provider or add support for the new provider")
                else:
                    guidance.append(f"Fix validation error: {error}")
        
        # Add warnings as guidance
        for warning in validation_result.warnings:
            guidance.append(f"Consider addressing: {warning}")
        
        return guidance
    
    def get_registered_schemas(self) -> List[str]:
        """Get list of registered schema names"""
        with self._lock:
            return list(self.schemas.keys())
    
    def get_validator_info(self) -> Dict[str, Any]:
        """Get information about registered validators"""
        with self._lock:
            info = {}
            for validation_type, validators in self.validators.items():
                info[validation_type.value] = [
                    {
                        'name': validator.name,
                        'rules_count': len(validator.rules)
                    }
                    for validator in validators
                ]
            return info


# Global validation engine instance
_global_validation_engine: Optional[ValidationEngine] = None
_engine_lock = threading.Lock()


def get_validation_engine() -> ValidationEngine:
    """Get the global validation engine instance"""
    global _global_validation_engine
    
    if _global_validation_engine is None:
        with _engine_lock:
            if _global_validation_engine is None:
                _global_validation_engine = ValidationEngine()
    
    return _global_validation_engine


def configure_validation_engine(engine: ValidationEngine) -> None:
    """Configure the global validation engine"""
    global _global_validation_engine
    
    with _engine_lock:
        _global_validation_engine = engine


# Convenience functions for common validations
def validate_config(config: Dict[str, Any], schema_name: Optional[str] = None) -> ValidationResult:
    """Validate configuration using global engine"""
    engine = get_validation_engine()
    return engine.validate_configuration(config, schema_name)


def validate_input(parameters: Dict[str, Any], required_params: List[str] = None, 
                  param_types: Dict[str, Type] = None) -> ValidationResult:
    """Validate input parameters using global engine"""
    engine = get_validation_engine()
    return engine.validate_input_parameters(parameters, required_params, param_types)


def validate_file(file_path: str, required_permissions: str = "r") -> ValidationResult:
    """Validate file access using global engine"""
    engine = get_validation_engine()
    return engine.validate_file_access(file_path, required_permissions)


def validate_model(model_config: Dict[str, Any]) -> ValidationResult:
    """Validate model configuration using global engine"""
    engine = get_validation_engine()
    return engine.validate_model_configuration(model_config)


def validate_api_response(response: Dict[str, Any], schema_name: Optional[str] = None) -> ValidationResult:
    """Validate API response using global engine"""
    engine = get_validation_engine()
    return engine.validate_api_response(response, schema_name)


# Decorator for automatic input validation
def validate_inputs(required_params: List[str] = None, param_types: Dict[str, Type] = None):
    """
    Decorator for automatic input parameter validation
    
    Args:
        required_params: List of required parameter names
        param_types: Expected types for parameters
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Validate kwargs as input parameters
            validation_result = validate_input(kwargs, required_params, param_types)
            
            if not validation_result.is_valid:
                error_msg = f"Input validation failed for {func.__name__}: {'; '.join(validation_result.errors)}"
                raise create_contextual_exception(
                    error_msg,
                    ErrorCategory.VALIDATION,
                    ErrorSeverity.HIGH,
                    context={'function': func.__name__, 'parameters': list(kwargs.keys())},
                    recovery_suggestions=get_validation_engine().get_validation_guidance(validation_result)
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator