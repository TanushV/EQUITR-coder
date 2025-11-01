"""
Unit tests for Validation Engine

Tests the validation system including:
- Schema validation
- Input parameter validation
- File permission validation
- Model configuration validation
- API response validation
- Validation guidance system
"""

import os
import tempfile

import pytest

from equitrcoder.core.standardized_error_handler import (
    ErrorSeverity,
)

# from typing import Dict, Any  # Unused
from equitrcoder.core.validation_engine import (
    APIValidator,
    BaseValidator,
    FileValidator,
    ModelValidator,
    SchemaValidator,
    ValidationEngine,
    ValidationResult,
    ValidationRule,
    ValidationType,
    configure_validation_engine,
    get_validation_engine,
    validate_config,
    validate_input,
    validate_inputs,
    validate_model,
)


class TestValidationResult:
    """Test suite for ValidationResult"""

    def test_validation_result_creation(self):
        """Test validation result creation"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Test warning"],
            validation_type=ValidationType.SCHEMA,
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.validation_type == ValidationType.SCHEMA


class TestValidationRule:
    """Test suite for ValidationRule"""

    def test_validation_rule_creation(self):
        """Test validation rule creation"""
        rule = ValidationRule(
            name="test_rule",
            description="Test validation rule",
            validator_function=lambda x: x > 0,
            error_message="Value must be positive",
        )

        assert rule.name == "test_rule"
        assert rule.description == "Test validation rule"
        assert rule.validator_function(5) is True
        assert rule.validator_function(-1) is False
        assert rule.error_message == "Value must be positive"


class TestBaseValidator:
    """Test suite for BaseValidator"""

    def setup_method(self):
        """Setup for each test method"""
        self.validator = BaseValidator("test_validator")

    def test_validator_initialization(self):
        """Test validator initialization"""
        assert self.validator.name == "test_validator"
        assert len(self.validator.rules) == 0

    def test_add_rule(self):
        """Test adding validation rules"""
        rule = ValidationRule(
            name="positive_number",
            description="Number must be positive",
            validator_function=lambda x: isinstance(x, (int, float)) and x > 0,
            error_message="Value must be a positive number",
        )

        self.validator.add_rule(rule)
        assert len(self.validator.rules) == 1
        assert self.validator.rules[0] == rule

    def test_validate_success(self):
        """Test successful validation"""
        rule = ValidationRule(
            name="positive_number",
            description="Number must be positive",
            validator_function=lambda x: isinstance(x, (int, float)) and x > 0,
            error_message="Value must be a positive number",
        )

        self.validator.add_rule(rule)
        result = self.validator.validate(5)

        assert result.success is True
        assert result.data is True
        assert result.error is None

    def test_validate_failure(self):
        """Test validation failure"""
        rule = ValidationRule(
            name="positive_number",
            description="Number must be positive",
            validator_function=lambda x: isinstance(x, (int, float)) and x > 0,
            error_message="Value must be a positive number",
            severity=ErrorSeverity.HIGH,
        )

        self.validator.add_rule(rule)
        result = self.validator.validate(-1)

        assert result.success is False
        assert result.data is False
        assert "Value must be a positive number" in result.error

    def test_get_validation_rules(self):
        """Test getting validation rules"""
        rule = ValidationRule(
            name="test_rule",
            description="Test rule description",
            validator_function=lambda x: True,
            error_message="Test error",
        )

        self.validator.add_rule(rule)
        rules = self.validator.get_validation_rules()

        assert len(rules) == 1
        assert "test_rule: Test rule description" in rules


class TestSchemaValidator:
    """Test suite for SchemaValidator"""

    def setup_method(self):
        """Setup for each test method"""
        self.schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
            },
            "required": ["name"],
        }
        self.validator = SchemaValidator(self.schema)

    def test_valid_data(self):
        """Test validation with valid data"""
        data = {"name": "John", "age": 30}
        result = self.validator.validate(data)

        assert result.success is True
        assert result.data is True

    def test_invalid_data(self):
        """Test validation with invalid data"""
        data = {"age": 30}  # Missing required 'name'
        result = self.validator.validate(data)

        assert result.success is False
        assert result.data is False
        assert "Schema validation failed" in result.error

    def test_invalid_type(self):
        """Test validation with invalid type"""
        data = {"name": "John", "age": "thirty"}  # Age should be integer
        result = self.validator.validate(data)

        assert result.success is False
        assert result.data is False


class TestFileValidator:
    """Test suite for FileValidator"""

    def setup_method(self):
        """Setup for each test method"""
        self.validator = FileValidator()

    def test_existing_file(self):
        """Test validation with existing file"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")

        try:
            result = self.validator.validate_file_permissions(temp_path, "r")
            assert result.is_valid is True
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        """Test validation with nonexistent file"""
        result = self.validator.validate_file_permissions("/nonexistent/file.txt", "r")

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "does not exist" in result.errors[0]

    def test_permission_validation(self):
        """Test permission validation"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test content")

        try:
            # Make file read-only
            os.chmod(temp_path, 0o444)

            # Test read permission (should pass)
            result = self.validator.validate_file_permissions(temp_path, "r")
            assert result.is_valid is True

            # Test write permission (should fail)
            result = self.validator.validate_file_permissions(temp_path, "w")
            assert result.is_valid is False
            assert any("not writable" in error for error in result.errors)

        finally:
            os.chmod(temp_path, 0o666)  # Restore permissions for deletion
            os.unlink(temp_path)


class TestModelValidator:
    """Test suite for ModelValidator"""

    def setup_method(self):
        """Setup for each test method"""
        self.validator = ModelValidator()

    def test_valid_model_config(self):
        """Test validation with valid model configuration"""
        config = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        result = self.validator.validate_model_config(config)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        config = {"temperature": 0.7}

        result = self.validator.validate_model_config(config)

        assert result.is_valid is False
        assert any(
            "Missing required field: provider" in error for error in result.errors
        )
        assert any("Missing required field: model" in error for error in result.errors)

    def test_unsupported_provider(self):
        """Test validation with unsupported provider"""
        config = {"provider": "unsupported_provider", "model": "some_model"}

        result = self.validator.validate_model_config(config)

        assert result.is_valid is False
        assert any("Unsupported provider" in error for error in result.errors)

    def test_invalid_temperature(self):
        """Test validation with invalid temperature"""
        config = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 3.0,  # Invalid: > 2
        }

        result = self.validator.validate_model_config(config)

        assert result.is_valid is False
        assert any(
            "Temperature must be a number between 0 and 2" in error
            for error in result.errors
        )

    def test_invalid_max_tokens(self):
        """Test validation with invalid max_tokens"""
        config = {
            "provider": "openai",
            "model": "gpt-4",
            "max_tokens": -100,  # Invalid: negative
        }

        result = self.validator.validate_model_config(config)

        assert result.is_valid is False
        assert any(
            "max_tokens must be a positive integer" in error for error in result.errors
        )


class TestAPIValidator:
    """Test suite for APIValidator"""

    def setup_method(self):
        """Setup for each test method"""
        self.validator = APIValidator()

    def test_valid_api_response(self):
        """Test validation with valid API response"""
        response = {"status": "success", "data": {"result": "test"}}

        result = self.validator.validate_api_response(response)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_api_response_with_error(self):
        """Test validation with API response containing error"""
        response = {"error": "Something went wrong", "status": "failed"}

        result = self.validator.validate_api_response(response)

        assert result.is_valid is False
        assert any("API returned error" in error for error in result.errors)

    def test_invalid_response_type(self):
        """Test validation with invalid response type"""
        response = "not a dictionary"

        result = self.validator.validate_api_response(response)

        assert result.is_valid is False
        assert any("Response must be a dictionary" in error for error in result.errors)

    def test_schema_validation(self):
        """Test API response schema validation"""
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string"}, "data": {"type": "object"}},
            "required": ["status"],
        }

        # Valid response
        valid_response = {"status": "success", "data": {}}
        result = self.validator.validate_api_response(valid_response, schema)
        assert result.is_valid is True

        # Invalid response (missing required field)
        invalid_response = {"data": {}}
        result = self.validator.validate_api_response(invalid_response, schema)
        assert result.is_valid is False


class TestValidationEngine:
    """Test suite for ValidationEngine"""

    def setup_method(self):
        """Setup for each test method"""
        self.engine = ValidationEngine()

    def test_engine_initialization(self):
        """Test validation engine initialization"""
        assert isinstance(self.engine, ValidationEngine)
        assert len(self.engine.validators) == len(ValidationType)
        assert len(self.engine.schemas) == 0

    def test_register_validator(self):
        """Test registering a validator"""
        validator = BaseValidator("test_validator")
        self.engine.register_validator(ValidationType.INPUT, validator)

        assert validator in self.engine.validators[ValidationType.INPUT]

    def test_register_schema(self):
        """Test registering a schema"""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }

        self.engine.register_schema("test_schema", schema)

        assert "test_schema" in self.engine.schemas
        assert self.engine.schemas["test_schema"] == schema

    def test_validate_configuration(self):
        """Test configuration validation"""
        # Register a schema
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        self.engine.register_schema("config_schema", schema)

        # Valid configuration
        valid_config = {"name": "test"}
        result = self.engine.validate_configuration(valid_config, "config_schema")
        assert result.is_valid is True

        # Invalid configuration
        invalid_config = {}
        result = self.engine.validate_configuration(invalid_config, "config_schema")
        assert result.is_valid is False

    def test_validate_input_parameters(self):
        """Test input parameter validation"""
        parameters = {"name": "John", "age": 30}
        required_params = ["name"]
        param_types = {"name": str, "age": int}

        result = self.engine.validate_input_parameters(
            parameters, required_params, param_types
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_input_parameters_missing_required(self):
        """Test input parameter validation with missing required parameter"""
        parameters = {"age": 30}
        required_params = ["name", "age"]

        result = self.engine.validate_input_parameters(parameters, required_params)

        assert result.is_valid is False
        assert any(
            "Missing required parameter: name" in error for error in result.errors
        )

    def test_validate_input_parameters_wrong_type(self):
        """Test input parameter validation with wrong type"""
        parameters = {"name": "John", "age": "thirty"}
        param_types = {"name": str, "age": int}

        result = self.engine.validate_input_parameters(
            parameters, param_types=param_types
        )

        assert result.is_valid is False
        assert any("must be of type int" in error for error in result.errors)

    def test_get_validation_guidance(self):
        """Test getting validation guidance"""
        result = ValidationResult(
            is_valid=False,
            errors=["Missing required field: name", "File does not exist: test.txt"],
            warnings=["Consider adding optional field: description"],
        )

        guidance = self.engine.get_validation_guidance(result)

        assert len(guidance) > 0
        assert any("Add the missing required field" in g for g in guidance)
        assert any("Check the file path" in g for g in guidance)
        assert any("Consider addressing" in g for g in guidance)

    def test_get_registered_schemas(self):
        """Test getting registered schemas"""
        schema = {"type": "object"}
        self.engine.register_schema("test_schema", schema)

        schemas = self.engine.get_registered_schemas()

        assert "test_schema" in schemas

    def test_get_validator_info(self):
        """Test getting validator information"""
        info = self.engine.get_validator_info()

        assert isinstance(info, dict)
        assert ValidationType.FILE.value in info
        assert ValidationType.MODEL.value in info
        assert ValidationType.API.value in info


class TestGlobalValidationEngine:
    """Test suite for global validation engine functions"""

    def setup_method(self):
        """Setup for each test method"""
        # Reset global engine
        import equitrcoder.core.validation_engine

        equitrcoder.core.validation_engine._global_validation_engine = None

    def test_get_validation_engine(self):
        """Test getting global validation engine"""
        engine1 = get_validation_engine()
        engine2 = get_validation_engine()

        assert engine1 is engine2
        assert isinstance(engine1, ValidationEngine)

    def test_configure_validation_engine(self):
        """Test configuring global validation engine"""
        custom_engine = ValidationEngine()
        configure_validation_engine(custom_engine)

        global_engine = get_validation_engine()
        assert global_engine is custom_engine

    def test_validate_config_function(self):
        """Test global validate_config function"""
        config = {"test": "value"}
        result = validate_config(config)

        assert isinstance(result, ValidationResult)

    def test_validate_input_function(self):
        """Test global validate_input function"""
        parameters = {"name": "test"}
        result = validate_input(parameters, ["name"], {"name": str})

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    def test_validate_model_function(self):
        """Test global validate_model function"""
        model_config = {"provider": "openai", "model": "gpt-4"}
        result = validate_model(model_config)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True


class TestValidationDecorator:
    """Test suite for validation decorator"""

    def test_validate_inputs_decorator_success(self):
        """Test validate_inputs decorator with valid inputs"""

        @validate_inputs(
            required_params=["name"], param_types={"name": str, "age": int}
        )
        def test_function(name, age=None):
            return f"Hello {name}, age {age}"

        result = test_function(name="John", age=30)
        assert result == "Hello John, age 30"

    def test_validate_inputs_decorator_failure(self):
        """Test validate_inputs decorator with invalid inputs"""

        @validate_inputs(required_params=["name"], param_types={"name": str})
        def test_function(name):
            return f"Hello {name}"

        with pytest.raises(Exception) as exc_info:
            test_function()  # Missing required parameter

        assert "Input validation failed" in str(exc_info.value)

    def test_validate_inputs_decorator_type_error(self):
        """Test validate_inputs decorator with type error"""

        @validate_inputs(param_types={"age": int})
        def test_function(age):
            return f"Age is {age}"

        with pytest.raises(Exception) as exc_info:
            test_function(age="thirty")  # Wrong type

        assert "Input validation failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
