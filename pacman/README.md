# Pac-Man (Python)

A simple, beautiful Pac-Man game built with Pygame in a single file.

## Features
- Classic Pac-Man gameplay with smooth animations
- 4 ghosts with different behaviors (Blinky, Pinky, Inky, Clyde)
- Animated Pac-Man with mouth movement
- Power pellets that make ghosts vulnerable
- Scatter/Chase mode switching
- Pulsing power pellets and frightened ghost blinking
- Clean, modern UI with score, lives, level, and mode display

## Quick Start

1. Install Python 3.8+ and pygame:
```bash
pip install pygame==2.6.1
```

2. Run the game:
```bash
python pacman/main.py
```

## Controls
- **Arrow Keys**: Move Pac-Man
- **P**: Pause/Unpause
- **R**: Restart (when game over)
- **ESC**: Quit

## Game Mechanics
- Collect all pellets to advance to the next level
- Power pellets (larger, pulsing) make ghosts vulnerable for 6 seconds
- Ghosts switch between Chase and Scatter modes
- Eat ghosts when they're blue (frightened) for bonus points
- Game over when all lives are lost

## Technical Details
- Single file implementation (~500 lines)
- 60 FPS smooth gameplay
- Procedural animations (no external assets)
- Clean, readable code structure

Enjoy playing!
