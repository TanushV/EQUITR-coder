"""
Unit tests for game settings and configuration.
"""

import json
import tempfile
from pathlib import Path

from game.settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    GRAVITY,
    JUMP_STRENGTH,
    PLAYER_SPEED,
    TILE_SIZE,
    ASSETS_DIR,
    LEVELS_DIR,
)


def test_default_constants():
    """Test that default constants are set correctly."""
    assert SCREEN_WIDTH == 1024
    assert SCREEN_HEIGHT == 768
    assert FPS == 60
    assert GRAVITY == 0.8
    assert JUMP_STRENGTH == -15
    assert PLAYER_SPEED == 5
    assert TILE_SIZE == 32


def test_directory_paths():
    """Test that directory paths are correctly defined."""
    assert ASSETS_DIR.exists()
    assert LEVELS_DIR.exists()
    assert (ASSETS_DIR / "images").exists()
    assert (ASSETS_DIR / "sounds").exists()
    assert (ASSETS_DIR / "fonts").exists()


def test_config_override():
    """Test that config.json can override default settings."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_file = temp_path / "config.json"
        
        config_data = {
            "SCREEN_WIDTH": 800,
            "FPS": 30,
            "GRAVITY": 1.0,
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Import settings module with custom config path
        import game.settings as settings_module
        settings_module.CONFIG_FILE = config_file
        
        # Reload the module to apply config
        import importlib
        importlib.reload(settings_module)
        
        assert settings_module.SCREEN_WIDTH == 800
        assert settings_module.FPS == 30
        assert settings_module.GRAVITY == 1.0


def test_invalid_config_handling():
    """Test that invalid config files don't crash the game."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_file = temp_path / "config.json"
        
        # Write invalid JSON
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Import settings module with invalid config
        import game.settings as settings_module
        settings_module.CONFIG_FILE = config_file
        
        # Reload the module - should use defaults
        import importlib
        importlib.reload(settings_module)
        
        # Should still have default values
        assert settings_module.SCREEN_WIDTH == 1024
        assert settings_module.FPS == 60