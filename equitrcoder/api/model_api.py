from typing import Any, Dict, List

from equitrcoder.core.unified_config import get_config_manager


def get_config() -> Dict[str, Any]:
	cm = get_config_manager()
	cfg = cm.get_configuration()
	return cfg


class ModelSelector:
	def __init__(self):
		self.cm = get_config_manager()

	def configure_single_model(self, model: str):
		cfg = self.cm.get_configuration()
		llm = dict(cfg.get("llm", {}))
		llm["model"] = model
		self.cm.set("llm.model", model)

	def configure_multi_model(self, primary: str, secondary: str):
		# Unified config doesn’t manage multiple active models; map to supervisor/worker
		self.cm.set("orchestrator.supervisor_model", primary)
		self.cm.set("orchestrator.worker_model", secondary)

	def get_current_config(self) -> Dict[str, Any]:
		cfg = self.cm.get_configuration()
		return {
			"llm": cfg.get("llm", {}),
			"orchestrator": cfg.get("orchestrator", {}),
		}

	def get_available_models(self) -> List[str]:
		# In absence of discovery service, return a common set
		return [
			"openai/gpt-4",
			"openai/gpt-4-turbo",
			"openai/gpt-3.5-turbo",
			"anthropic/claude-3-sonnet",
			"anthropic/claude-3-haiku",
			"moonshot/kimi-k2-0711-preview",
		]

	def is_multi_mode(self) -> bool:
		return True

	def get_active_models(self) -> List[str]:
		cfg = self.cm.get_configuration()
		llm_model = cfg.get("llm", {}).get("model", "")
		sup = cfg.get("orchestrator", {}).get("supervisor_model", "")
		wrk = cfg.get("orchestrator", {}).get("worker_model", "")
		return [m for m in [llm_model, sup, wrk] if m]

	def reset_to_defaults(self):
		# Reset known keys to default-friendly values
		self.cm.set("llm.model", "")
		self.cm.set("orchestrator.supervisor_model", "o3")
		self.cm.set("orchestrator.worker_model", "moonshot/kimi-k2-0711-preview")


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

	return selector.get_current_config()


# Global instance for easy access
_model_selector = None


def get_model_selector() -> ModelSelector:
	global _model_selector
	if _model_selector is None:
		_model_selector = ModelSelector()
	return _model_selector
