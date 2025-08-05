# Mario Game

A classic 2D platformer game built with Python and Pygame, inspired by the original Super Mario Bros.

## Features

- **Classic Platforming**: Jump, run, and stomp on enemies
- **Coin Collection**: Gather coins to increase your score
- **Enemy AI**: Simple patrolling enemies with stomp mechanics
- **Level System**: JSON-based level loading with tilemaps
- **Side-scrolling Camera**: Smooth camera that follows the player
- **Multiple Game States**: Title screen, gameplay, pause, game over, and victory screens
- **Sound Effects**: Jump, coin collection, and enemy defeat sounds
- **Score System**: Track your progress with on-screen HUD

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mario_game
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## How to Play

### Controls

- **Arrow Keys** or **A/D**: Move left/right
- **Space**: Jump
- **P**: Pause/unpause game
- **Enter**: Start game or restart after game over
- **M**: Toggle mute/unmute

### Gameplay

- **Objective**: Reach the flag at the end of each level
- **Coins**: Collect coins to increase your score (+1 point each)
- **Enemies**: Stomp on enemies to defeat them (+5 points each)
- **Lives**: You start with 3 lives
- **Game Over**: Lose all lives to trigger game over screen

## Development

### Running the Game

```bash
python -m game.main
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Run linting
flake8 game/ tests/

# Run tests with coverage
pytest --cov=game tests/

# Format code
black game/ tests/
```

### Project Structure

```
mario_game/
├── game/                    # Main game package
│   ├── __init__.py
│   ├── main.py             # Entry point
│   ├── settings.py         # Game constants and configuration
│   ├── entities/           # Game entities (player, enemies, coins)
│   ├── scenes/             # Game states (title, playing, pause, etc.)
│   └── utils/              # Utility modules
├── assets/                 # Game assets
│   ├── images/            # Sprites and textures
│   ├── sounds/            # Sound effects and music
│   └── fonts/             # Font files
├── levels/                 # Level files
│   ├── json/              # JSON level definitions
│   └── csv/               # CSV level definitions (alternative format)
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── .github/workflows/      # CI/CD configuration
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration
├── LICENSE                # MIT License
└── README.md             # This file
```

## Level Format

Levels are defined in JSON format with the following structure:

```json
{
  "name": "Level 1",
  "width": 50,
  "height": 15,
  "tile_size": 32,
  "player_start": {"x": 2, "y": 12},
  "goal": {"x": 47, "y": 12},
  "tiles": [
    {"x": 0, "y": 14, "type": "ground"},
    {"x": 1, "y": 14, "type": "ground"},
    // ... more tiles
  ],
  "coins": [
    {"x": 5, "y": 10},
    {"x": 7, "y": 8}
  ],
  "enemies": [
    {"x": 15, "y": 13, "patrol_start": 15, "patrol_end": 20},
    {"x": 25, "y": 13, "patrol_start": 25, "patrol_end": 30}
  ]
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Asset Credits

- **Player Sprite**: Placeholder rectangle (replace with custom sprite)
- **Enemy Sprite**: Placeholder rectangle (replace with custom sprite)
- **Coin Sprite**: Placeholder circle (replace with custom sprite)
- **Tile Sprites**: Placeholder colored rectangles (replace with custom tileset)
- **Sound Effects**: Placeholder beeps (replace with custom sound effects)

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Inspired by Nintendo's Super Mario Bros.
- Developed as part of the EQUITR Coder framework demonstration