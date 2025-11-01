"""
Configuration Validation System

This module provides configuration validation at application startup
and implements configuration hot-reloading capability.
"""

import logging
import os
from typing import Dict, Any, List
from .unified_config import get_config_manager, ValidationResult

logger = logging.getLogger(__name__)


from .interfaces import IValidator, Result  # noqa: E402


class ConfigurationValidator(IValidator[Dict[str, Any]]):
    """Validates configuration at application startup and provides hot-reloading"""

    def __init__(self):
        self.config_manager = get_config_manager()

    # Implement IValidator interface for tests expecting concrete class
    def validate(self, item: Dict[str, Any]) -> Result[bool]:
        try:
            validation_result = self.config_manager.validate_schema(item)
            if validation_result.is_valid:
                return Result(success=True, data=True)
            else:
                return Result(
                    success=False,
                    data=False,
                    error=f"Validation failed: {', '.join(validation_result.errors)}",
                )
        except Exception as e:
            return Result(success=False, data=False, error=str(e))

    def get_validation_rules(self) -> List[str]:
        return [
            "Configuration must have valid LLM settings",
            "Configuration must have valid sandbox settings",
            "Configuration must have valid orchestrator settings",
            "Configuration must have valid limits settings",
            "All required environment variables must be set",
            "Model configurations must be valid",
            "Limits must be within reasonable ranges",
        ]

    def validate_startup_configuration(self) -> ValidationResult:
        """
        Validate configuration at application startup

        Returns:
            ValidationResult: Result of the validation with any errors or warnings
        """
        logger.info("Starting configuration validation...")

        try:
            # Load the configuration
            config_data = self.config_manager.load_config()

            # Validate the configuration schema
            validation_result = self.config_manager.validate_schema(
                config_data.__dict__
            )

            if validation_result.is_valid:
                logger.info("Configuration validation passed successfully")
                self._log_configuration_summary(config_data)
            else:
                logger.error(
                    f"Configuration validation failed with {len(validation_result.errors)} errors"
                )
                for error in validation_result.errors:
                    logger.error(f"Config error: {error}")

                if validation_result.warnings:
                    for warning in validation_result.warnings:
                        logger.warning(f"Config warning: {warning}")

            return validation_result

        except Exception as e:
            logger.error(f"Configuration validation failed with exception: {e}")
            return ValidationResult(
                is_valid=False, errors=[f"Configuration validation exception: {str(e)}"]
            )

    def _log_configuration_summary(self, config_data) -> None:
        """Log a summary of the loaded configuration"""
        logger.info("Configuration Summary:")
        logger.info(f"  LLM Provider: {config_data.llm.get('provider', 'Not set')}")
        logger.info(f"  LLM Model: {config_data.llm.get('model', 'Not set')}")
        logger.info(f"  Max Cost: {config_data.limits.get('max_cost', 'Not set')}")
        logger.info(
            f"  Max Iterations: {config_data.limits.get('max_iterations', 'Not set')}"
        )
        logger.info(
            f"  Max Workers: {config_data.limits.get('max_workers', 'Not set')}"
        )
        logger.info(f"  Sandbox Type: {config_data.sandbox.get('type', 'Not set')}")
        logger.info(
            f"  Sandbox Timeout: {config_data.sandbox.get('timeout', 'Not set')}"
        )

    def validate_environment_variables(self) -> List[str]:
        """
        Validate that required environment variables are set

        Returns:
            List[str]: List of missing environment variables
        """
        missing_vars = []

        # Check for API keys based on provider
        provider = self.config_manager.get("llm.provider", "litellm")

        if provider == "litellm":
            # LiteLLM can use various providers, check for common API keys
            api_keys = [
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "MOONSHOT_API_KEY",
                "DEEPSEEK_API_KEY",
                "GROQ_API_KEY",
            ]

            # Check if at least one API key is set
            if not any(os.getenv(key) for key in api_keys):
                missing_vars.append(
                    "At least one API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, MOONSHOT_API_KEY, DEEPSEEK_API_KEY, or GROQ_API_KEY)"
                )

        elif provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                missing_vars.append("OPENAI_API_KEY")

        elif provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                missing_vars.append("ANTHROPIC_API_KEY")

        return missing_vars

    def validate_model_configuration(self) -> List[str]:
        """
        Validate model configuration

        Returns:
            List[str]: List of model configuration issues
        """
        issues = []

        model = self.config_manager.get("llm.model")
        if not model:
            issues.append(
                "LLM model is not configured. Please set llm.model in configuration or EQUITR_LLM_MODEL environment variable."
            )

        supervisor_model = self.config_manager.get("orchestrator.supervisor_model")
        if not supervisor_model:
            issues.append(
                "Supervisor model is not configured. Please set orchestrator.supervisor_model in configuration."
            )

        worker_model = self.config_manager.get("orchestrator.worker_model")
        if not worker_model:
            issues.append(
                "Worker model is not configured. Please set orchestrator.worker_model in configuration."
            )

        return issues

    def validate_limits_configuration(self) -> List[str]:
        """
        Validate limits configuration for reasonable values

        Returns:
            List[str]: List of limit configuration issues
        """
        issues = []

        max_cost = self.config_manager.get("limits.max_cost", 0)
        if max_cost <= 0:
            issues.append("Max cost limit should be greater than 0")
        elif max_cost > 100:
            issues.append(
                "Max cost limit is very high (>$100). Consider if this is intentional."
            )

        max_iterations = self.config_manager.get("limits.max_iterations", 0)
        if max_iterations <= 0:
            issues.append("Max iterations should be greater than 0")
        elif max_iterations > 100:
            issues.append(
                "Max iterations is very high (>100). Consider if this is intentional."
            )

        max_workers = self.config_manager.get("limits.max_workers", 0)
        if max_workers <= 0:
            issues.append("Max workers should be greater than 0")
        elif max_workers > 10:
            issues.append(
                "Max workers is very high (>10). Consider if this is intentional."
            )

        devops_timeout = self.config_manager.get("limits.devops_timeout", 0)
        if devops_timeout <= 0:
            issues.append("DevOps timeout should be greater than 0")
        elif devops_timeout > 3600:  # 1 hour
            issues.append(
                "DevOps timeout is very high (>1 hour). Consider if this is intentional."
            )

        return issues

    def perform_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Perform comprehensive configuration validation

        Returns:
            Dict[str, Any]: Comprehensive validation results
        """
        results: Dict[str, Any] = {
            "overall_valid": True,
            "schema_validation": None,
            "environment_issues": [],
            "model_issues": [],
            "limits_issues": [],
            "recommendations": [],
        }

        # Schema validation
        schema_result = self.validate_startup_configuration()
        results["schema_validation"] = schema_result
        if not schema_result.is_valid:
            results["overall_valid"] = False

        # Environment validation
        env_issues = self.validate_environment_variables()
        results["environment_issues"] = env_issues
        if env_issues:
            results["overall_valid"] = False

        # Model validation
        model_issues = self.validate_model_configuration()
        results["model_issues"] = model_issues
        if model_issues:
            results["overall_valid"] = False

        # Limits validation
        limits_issues = self.validate_limits_configuration()
        results["limits_issues"] = limits_issues
        # Limits issues are warnings, not errors

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _generate_recommendations(
        self, validation_results: Dict[str, Any]
    ) -> List[str]:
        """Generate configuration recommendations based on validation results"""
        recommendations = []

        if validation_results["environment_issues"]:
            recommendations.append(
                "Set up required API keys in your environment variables"
            )

        if validation_results["model_issues"]:
            recommendations.append(
                "Configure LLM models in your configuration file or environment variables"
            )

        if validation_results["limits_issues"]:
            recommendations.append(
                "Review and adjust configuration limits for optimal performance"
            )

        # Performance recommendations
        max_cost = self.config_manager.get("limits.max_cost", 0)
        if max_cost < 1.0:
            recommendations.append(
                "Consider increasing max_cost limit for better task completion rates"
            )

        max_iterations = self.config_manager.get("limits.max_iterations", 0)
        if max_iterations < 10:
            recommendations.append(
                "Consider increasing max_iterations for complex tasks"
            )

        return recommendations

    def enable_hot_reloading(self) -> None:
        """Enable configuration hot-reloading capability"""
        logger.info("Configuration hot-reloading is enabled")
        # The UnifiedConfigManager already supports hot-reloading via reload_config()
        # This method can be extended to add file watchers if needed

    def reload_configuration(self) -> ValidationResult:
        """
        Reload configuration and validate

        Returns:
            ValidationResult: Result of the validation after reload
        """
        logger.info("Reloading configuration...")

        try:
            self.config_manager.reload_config()
            return self.validate_startup_configuration()
        except Exception as e:
            logger.error(f"Configuration reload failed: {e}")
            return ValidationResult(
                is_valid=False, errors=[f"Configuration reload failed: {str(e)}"]
            )


# Global validator instance
_validator = None


def get_config_validator() -> ConfigurationValidator:
    """Get the global configuration validator instance"""
    global _validator
    if _validator is None:
        _validator = ConfigurationValidator()
    return _validator


def validate_startup_config() -> bool:
    """
    Convenience function to validate configuration at startup

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    validator = get_config_validator()
    results = validator.perform_comprehensive_validation()

    if not results["overall_valid"]:
        logger.error("Configuration validation failed!")

        # Log all issues
        if results["environment_issues"]:
            logger.error("Environment issues:")
            for issue in results["environment_issues"]:
                logger.error(f"  - {issue}")

        if results["model_issues"]:
            logger.error("Model configuration issues:")
            for issue in results["model_issues"]:
                logger.error(f"  - {issue}")

        if results["limits_issues"]:
            logger.warning("Limits configuration issues:")
            for issue in results["limits_issues"]:
                logger.warning(f"  - {issue}")

        # Log recommendations
        if results["recommendations"]:
            logger.info("Recommendations:")
            for rec in results["recommendations"]:
                logger.info(f"  - {rec}")

        return False

    logger.info("Configuration validation passed!")
    return True
