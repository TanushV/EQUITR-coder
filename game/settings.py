"""
Game settings and constants for Mario-style platformer.
"""

import os
import json
from pathlib import Path

# Screen settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
TITLE = "Mario Platformer"

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
SKY_BLUE = (135, 206, 235)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)

# Game physics
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5
MAX_FALL_SPEED = 20

# Tile settings
TILE_SIZE = 32
MAP_WIDTH = 50  # tiles
MAP_HEIGHT = 24  # tiles

# Asset paths
ASSETS_DIR = Path(__file__).parent.parent / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"
FONTS_DIR = ASSETS_DIR / "fonts"
LEVELS_DIR = Path(__file__).parent.parent / "levels"

# Player settings
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 48
PLAYER_LIVES = 3

# Enemy settings
ENEMY_SPEED = 2
ENEMY_WIDTH = 32
ENEMY_HEIGHT = 32

# Coin settings
COIN_SIZE = 24
COIN_VALUE = 1

# Scoring
ENEMY_STOMP_SCORE = 100

# Audio settings
SOUND_ENABLED = True
MUSIC_VOLUME = 0.7
SFX_VOLUME = 0.8

# Debug settings
DEBUG_MODE = False
SHOW_FPS = True
SHOW_COLLISION_BOXES = False

# Load config override if exists
CONFIG_FILE = Path(__file__).parent.parent / "config.json"
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            for key, value in config.items():
                if key in globals():
                    globals()[key] = value
    except (json.JSONDecodeError, IOError):
        pass  # Use defaults if config is invalid

# Ensure directories exist
for directory in [ASSETS_DIR, IMAGES_DIR, SOUNDS_DIR, FONTS_DIR, LEVELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)