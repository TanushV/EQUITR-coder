from typing import Any, Dict, List, Optional

from equitrcoder.config.model_config import ModelConfig, get_config_manager


class ModelSelector:
    def __init__(self):
        self.config_manager = get_config_manager()

    def configure_single_model(self, model: str):
        """Configure to use a single model."""
        available = self.config_manager.get_available_models()
        if model not in available:
            raise ValueError(f"Model '{model}' not available. Available: {available}")

        self.config_manager.set_mode("single")
        self.config_manager.set_models(model)

    def configure_multi_model(self, primary: str, secondary: str):
        """Configure to use multi-model mode with primary and secondary models."""
        available = self.config_manager.get_available_models()

        if primary not in available:
            raise ValueError(
                f"Primary model '{primary}' not available. Available: {available}"
            )
        if secondary not in available:
            raise ValueError(
                f"Secondary model '{secondary}' not available. Available: {available}"
            )

        self.config_manager.set_mode("multi")
        self.config_manager.set_models(primary, secondary)

    def get_current_config(self) -> Dict[str, Any]:
        """Get current model configuration."""
        config = self.config_manager.get_config()
        return {
            "mode": config.mode,
            "primary_model": config.primary_model,
            "secondary_model": config.secondary_model,
            "active_models": config.models,
        }

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return self.config_manager.get_available_models()

    def is_multi_mode(self) -> bool:
        """Check if currently in multi-model mode."""
        return self.config_manager.is_multi_mode()

    def get_active_models(self) -> List[str]:
        """Get list of currently active models."""
        return self.config_manager.get_active_models()

    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        from equitrcoder.config.model_config import ModelConfig

        self.config_manager.save_config(ModelConfig())


class ModelContext:
    def __init__(self):
        self.selector = ModelSelector()

    def __enter__(self):
        return self.selector

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def configure_models(**kwargs):
    """Convenience function for quick model configuration."""
    selector = ModelSelector()

    if "single" in kwargs:
        selector.configure_single_model(kwargs["single"])
    elif "primary" in kwargs and "secondary" in kwargs:
        selector.configure_multi_model(kwargs["primary"], kwargs["secondary"])
    elif "mode" in kwargs:
        selector.config_manager.set_mode(kwargs["mode"])

    return selector.get_current_config()


# Global instance for easy access
_model_selector = None


def get_model_selector() -> ModelSelector:
    global _model_selector
    if _model_selector is None:
        _model_selector = ModelSelector()
    return _model_selector
