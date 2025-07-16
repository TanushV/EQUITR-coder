import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict


@dataclass
class ModelConfig:
    mode: str = "single"  # "single" or "multi"
    primary_model: str = "strong"
    secondary_model: Optional[str] = None
    models: List[str] = None

    def __post_init__(self):
        if self.models is None:
            self.models = [self.primary_model]
        if (
            self.mode == "multi"
            and self.secondary_model
            and self.secondary_model not in self.models
        ):
            self.models.append(self.secondary_model)


class ModelConfigManager:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.equitrcoder")
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "model_config.json"
        self._config = self._load_config()

    def _load_config(self) -> ModelConfig:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                return ModelConfig(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return ModelConfig()

    def save_config(self, config: ModelConfig):
        self._config = config
        with open(self.config_file, "w") as f:
            json.dump(asdict(config), f, indent=2)

    def get_config(self) -> ModelConfig:
        return self._config

    def set_mode(self, mode: str):
        if mode not in ["single", "multi"]:
            raise ValueError("Mode must be 'single' or 'multi'")
        config = self.get_config()
        config.mode = mode
        self.save_config(config)

    def set_models(self, primary: str, secondary: Optional[str] = None):
        config = self.get_config()
        config.primary_model = primary
        config.secondary_model = secondary
        if config.mode == "multi" and secondary:
            config.models = [primary, secondary]
        else:
            config.models = [primary]
        self.save_config(config)

    def get_available_models(self) -> List[str]:
        return [
            "strong",
            "weak",
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-haiku",
        ]

    def is_multi_mode(self) -> bool:
        return self._config.mode == "multi"

    def get_active_models(self) -> List[str]:
        return self._config.models


# Global instance
_config_manager = None


def get_config_manager() -> ModelConfigManager:
    global _config_manager
    if _config_manager is None:
        _config_manager = ModelConfigManager()
    return _config_manager
