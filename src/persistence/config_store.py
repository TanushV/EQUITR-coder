import json
import os
from pathlib import Path
from typing import Any, Dict


class ConfigStore:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.expanduser("~/.equitrcoder")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def save(self, key: str, value: Any):
        file_path = self.base_dir / f"{key}.json"
        with open(file_path, "w") as f:
            json.dump(value, f, indent=2)

    def load(self, key: str, default: Any = None) -> Any:
        file_path = self.base_dir / f"{key}.json"
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return default

    def delete(self, key: str):
        file_path = self.base_dir / f"{key}.json"
        if file_path.exists():
            file_path.unlink()

    def exists(self, key: str) -> bool:
        return (self.base_dir / f"{key}.json").exists()

    def list_keys(self) -> list:
        return [f.stem for f in self.base_dir.glob("*.json")]
