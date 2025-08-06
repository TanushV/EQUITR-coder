# Sound Assets

This directory contains sound effects and music for the Mario game.

## Current Placeholders

The following sound files are needed:

- `jump.ogg` - Player jump sound
- `coin.ogg` - Coin collection sound
- `stomp.ogg` - Enemy stomp sound
- `game_over.ogg` - Game over sound
- `level_complete.ogg` - Level completion sound
- `background_music.ogg` - Background music (optional)

## Placeholder Creation

For development, you can use simple generated sounds or find free assets:

1. **Generated Sounds**: Use tools like sfxr or bfxr
2. **Free Assets**: Check OpenGameArt.org or similar sites
3. **Creative Commons**: Ensure proper attribution

## Usage

Sounds are loaded through the game's audio system in `game/audio.py`.

## File Format

- **Sound Effects**: .ogg or .wav format
- **Music**: .ogg format (looping)
- **Quality**: 44.1kHz, 16-bit stereo recommended