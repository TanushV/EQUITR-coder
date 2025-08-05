"""
Integration tests for game imports and basic functionality.
"""

import pytest
import pygame
import json
import os
from pathlib import Path

from game import settings
from game.main import main


class TestGameImports:
    """Test that all game modules can be imported successfully."""
    
    def test_settings_import(self):
        """Test that settings module can be imported and contains expected constants."""
        assert hasattr(settings, 'SCREEN_WIDTH')
        assert hasattr(settings, 'SCREEN_HEIGHT')
        assert hasattr(settings, 'FPS')
        assert settings.SCREEN_WIDTH == 1024
        assert settings.SCREEN_HEIGHT == 768
        assert settings.FPS == 60
    
    def test_assets_directories_exist(self):
        """Test that all required asset directories exist."""
        assert settings.ASSETS_DIR.exists()
        assert settings.IMAGES_DIR.exists()
        assert settings.SOUNDS_DIR.exists()
        assert settings.FONTS_DIR.exists()
        assert settings.LEVELS_DIR.exists()
    
    def test_level_files_exist(self):
        """Test that sample level files exist."""
        json_level = settings.LEVELS_DIR / "json" / "level1.json"
        csv_level = settings.LEVELS_DIR / "csv" / "level1.csv"
        
        assert json_level.exists(), f"JSON level file not found: {json_level}"
        assert csv_level.exists(), f"CSV level file not found: {csv_level}"
    
    def test_config_json_valid(self):
        """Test that config.json is valid JSON if it exists."""
        config_file = Path("config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                assert isinstance(config, dict)
            except json.JSONDecodeError as e:
                pytest.fail(f"config.json is not valid JSON: {e}")
    
    def test_pygame_import(self):
        """Test that pygame can be imported and initialized."""
        try:
            pygame.init()
            pygame.quit()
            assert True
        except Exception as e:
            pytest.fail(f"Failed to import/initialize pygame: {e}")
    
    def test_main_function_exists(self):
        """Test that main function exists in game.main."""
        assert callable(main)


class TestLevelLoading:
    """Test level loading functionality."""
    
    def test_json_level_structure(self):
        """Test that JSON level files have the expected structure."""
        level_file = settings.LEVELS_DIR / "json" / "level1.json"
        
        with open(level_file, 'r') as f:
            level_data = json.load(f)
        
        required_keys = ['name', 'width', 'height', 'tile_size', 'player_start', 'goal', 'tiles']
        for key in required_keys:
            assert key in level_data, f"Missing required key: {key}"
        
        assert isinstance(level_data['tiles'], list)
        assert isinstance(level_data.get('coins', []), list)
        assert isinstance(level_data.get('enemies', []), list)
    
    def test_csv_level_structure(self):
        """Test that CSV level files can be parsed."""
        level_file = settings.LEVELS_DIR / "csv" / "level1.csv"
        
        with open(level_file, 'r') as f:
            lines = f.readlines()
        
        # Should have at least a header and some data
        assert len(lines) >= 2
        
        # Check that it's a rectangular grid
        rows = [line.strip() for line in lines if line.strip()]
        if rows:
            first_row_length = len(rows[0].split(','))
            for row in rows:
                assert len(row.split(',')) == first_row_length