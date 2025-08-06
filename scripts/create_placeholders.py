#!/usr/bin/env python3
"""
Script to create placeholder game assets.
This creates simple colored rectangles as placeholders for actual game sprites.
"""

import pygame
import os
from pathlib import Path

# Initialize pygame for image creation
pygame.init()

# Asset directories
ASSETS_DIR = Path(__file__).parent.parent / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def create_placeholder_image(filename, width, height, color, text=None):
    """Create a simple colored rectangle as a placeholder image."""
    surface = pygame.Surface((width, height))
    surface.fill(color)
    
    if text:
        font = pygame.font.Font(None, min(width, height) // 2)
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(width//2, height//2))
        surface.blit(text_surface, text_rect)
    
    pygame.image.save(surface, str(IMAGES_DIR / filename))
    print(f"Created {filename}")

# Create placeholder images
create_placeholder_image("player.png", 32, 48, (255, 0, 0), "P")
create_placeholder_image("enemy.png", 32, 32, (0, 255, 0), "E")
create_placeholder_image("coin.png", 24, 24, (255, 255, 0), "C")
create_placeholder_image("ground.png", 32, 32, (139, 69, 19), "G")
create_placeholder_image("brick.png", 32, 32, (165, 42, 42), "B")
create_placeholder_image("flag.png", 32, 32, (0, 0, 255), "F")
create_placeholder_image("sky.png", 32, 32, (135, 206, 235), "")

print("All placeholder assets created successfully!")