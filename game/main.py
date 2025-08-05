#!/usr/bin/env python3
"""
Mario Game - Main Entry Point

This is the main entry point for the Mario game.
Run this file to start the game.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Main game entry point."""
    print("🍄 Mario Game - Starting...")
    print("Game initialization complete!")
    print("Run 'python -m game.main' to start the game when implementation is ready.")

if __name__ == "__main__":
    main()